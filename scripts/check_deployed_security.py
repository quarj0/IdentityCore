#!/usr/bin/env python3
"""Fail-closed HTTPS promotion checks. Reports never include response data or secrets."""

import argparse
import json
import os
import re
import ssl
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit
from urllib.error import HTTPError
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener


class CheckFailed(Exception):
    pass


def origin(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise CheckFailed("invalid_https_origin")
    return value.rstrip("/")


class Probe:
    def __init__(self, base, context):
        self.base = origin(base)
        self.url = urlsplit(self.base)
        self.context = context

    def request(self, method, path, *, headers=None, body=None):
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None

        payload = json.dumps(body).encode() if body is not None else None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        # The default ProxyHandler honors the runner's configured HTTPS proxy.
        opener = build_opener(HTTPSHandler(context=self.context), NoRedirect())
        request = Request(self.base + path, payload, request_headers, method=method)
        try:
            response = opener.open(request, timeout=15)
        except HTTPError as exc:
            response = exc
        with response:
            data = response.read(65537)
            if len(data) > 65536 or 300 <= response.status < 400:
                raise CheckFailed("oversized_or_redirected_response")
            return response.status, response.headers, data


def require(condition, code):
    if not condition:
        raise CheckFailed(code)


def security_headers(headers, *, html=False):
    hsts = headers.get("Strict-Transport-Security", "")
    match = re.search(r"(?:^|;)\s*max-age=(\d+)(?:;|$)", hsts, re.I)
    require(match and int(match.group(1)) >= 31536000, "hsts")
    require(headers.get("X-Content-Type-Options", "").lower() == "nosniff", "nosniff")
    require(
        headers.get("Referrer-Policy", "").lower()
        in {
            "no-referrer",
            "same-origin",
            "strict-origin",
            "strict-origin-when-cross-origin",
        },
        "referrer_policy",
    )
    require(
        headers.get("X-Frame-Options", "").upper() in {"DENY", "SAMEORIGIN"}, "framing"
    )
    if html:
        directives = {}
        for part in headers.get("Content-Security-Policy", "").split(";"):
            tokens = part.split()
            if tokens:
                # Browsers use the first occurrence of a duplicate directive.
                directives.setdefault(tokens[0].lower(), tokens[1:])
        require(
            "default-src" in directives
            and directives.get("object-src") == ["'none'"]
            and "frame-ancestors" in directives
            and "base-uri" in directives
            and "script-src" in directives,
            "csp_missing_directive",
        )
        require(
            directives["frame-ancestors"] in (["'none'"], ["'self'"])
            and directives["base-uri"] in (["'none'"], ["'self'"]),
            "csp_unsafe_boundary",
        )
        script_policies = [directives["script-src"]]
        for name in ("script-src-elem", "script-src-attr"):
            if name in directives:
                script_policies.append(directives[name])
        require(
            all(
                "*" not in scripts
                and "'unsafe-inline'" not in scripts
                and "'unsafe-eval'" not in scripts
                for scripts in script_policies
            ),
            "csp_unsafe_script",
        )


def checked_cookies(headers, names, path):
    parsed = SimpleCookie()
    for value in headers.get_all("Set-Cookie", []):
        parsed.load(value)
    values = []
    for name in names:
        require(name in parsed, "missing_cookie")
        cookie = parsed[name]
        require(
            cookie["secure"]
            and cookie["httponly"]
            and cookie["samesite"].lower() in {"lax", "strict"}
            and not cookie["domain"]
            and cookie["path"] == path
            and bool(cookie.value),
            "unsafe_cookie",
        )
        values.append(f"{name}={cookie.value}")
    return "; ".join(values)


def run(config, credentials, *, ca_file=None):
    require(config.get("environment") in {"sandbox", "production"}, "environment")
    context = ssl.create_default_context(cafile=ca_file)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    api, dashboard, portal = [
        Probe(config[name], context) for name in ("api", "dashboard", "portal")
    ]
    approved = [origin(value) for value in config.get("approved_origins", [])]
    require(
        bool(approved) and dashboard.base in approved and portal.base in approved,
        "environment_origins",
    )
    require(
        all(
            credentials.get(name)
            for name in ("email", "password", "session_id", "session_token")
        ),
        "smoke_credentials_required",
    )
    results = []

    def check(name, operation):
        try:
            operation()
            results.append({"check": name, "passed": True})
        except Exception:
            # Includes TLS, DNS, HTTP and policy failures; no exception text is safe to report.
            results.append({"check": name, "passed": False})

    def public_headers(probe, path, html=False):
        status, headers, _ = probe.request("GET", path)
        require(status == 200, "public_status")
        security_headers(headers, html=html)

    check("api_tls_headers", lambda: public_headers(api, "/api/v1/health"))
    check("dashboard_tls_headers", lambda: public_headers(dashboard, "/login", True))
    check("portal_tls_headers", lambda: public_headers(portal, "/", True))

    def cors():
        for allowed in approved:
            status, headers, _ = api.request(
                "OPTIONS",
                "/api/v1/auth/login",
                headers={
                    "Origin": allowed,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,x-identitycore-session-scope",
                },
            )
            require(
                status in {200, 204}
                and headers.get("Access-Control-Allow-Origin") == allowed
                and headers.get("Access-Control-Allow-Credentials") == "true"
                and "origin" in headers.get("Vary", "").lower(),
                "approved_cors",
            )
            require(
                "POST" in headers.get("Access-Control-Allow-Methods", "").split(", "),
                "cors_method",
            )
            allowed_headers = {
                v.strip().lower()
                for v in headers.get("Access-Control-Allow-Headers", "").split(",")
            }
            require(
                {"content-type", "x-identitycore-session-scope"} <= allowed_headers,
                "cors_headers",
            )
        for denied in (
            "https://unapproved.invalid",
            "https://localhost",
            "null",
            approved[0] + ".unapproved.invalid",
        ):
            _, headers, _ = api.request(
                "OPTIONS",
                "/api/v1/auth/login",
                headers={"Origin": denied, "Access-Control-Request-Method": "POST"},
            )
            require(not headers.get("Access-Control-Allow-Origin"), "unapproved_cors")

    check("environment_cors", cors)

    def endpoints():
        status, _, _ = api.request("GET", "/api/v1/auth/me")
        require(status in {401, 403}, "anonymous_private_access")
        status, _, _ = api.request("GET", "/api/v1/auth/login")
        require(status == 405, "public_method")
        status, headers, _ = portal.request(
            "POST",
            "/api/verification/session",
            headers={"Origin": "https://unapproved.invalid"},
            body={},
        )
        require(status == 403 and not headers.get_all("Set-Cookie"), "portal_origin")

    check("endpoint_boundaries", endpoints)

    def backend_cookie():
        cookie = None
        request_headers = {
            "Origin": dashboard.base,
            "X-IdentityCore-Session-Scope": "dashboard",
        }
        try:
            status, headers, _ = api.request(
                "POST",
                "/api/v1/auth/login",
                headers=request_headers,
                body={
                    "email": credentials["email"],
                    "password": credentials["password"],
                },
            )
            # Keep even an unsafe issued cookie in memory so cleanup can revoke its session.
            raw = SimpleCookie()
            for value in headers.get_all("Set-Cookie", []):
                raw.load(value)
            cookie = (
                "; ".join(f"{key}={value.value}" for key, value in raw.items()) or None
            )
            name = config.get("refresh_cookie_name", "identitycore_refresh_dashboard")
            require(bool(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", name)), "cookie_name")
            require(status == 200, "login_or_mfa_required")
            checked_cookies(headers, [name], "/api/v1/auth/")
        finally:
            if cookie:
                status, _, _ = api.request(
                    "POST",
                    "/api/v1/auth/logout",
                    headers={**request_headers, "Cookie": cookie},
                    body={},
                )
                require(status == 200, "session_cleanup")

    check("dashboard_refresh_cookie", backend_cookie)

    def portal_cookie():
        try:
            status, headers, _ = portal.request(
                "POST",
                "/api/verification/session",
                headers={"Origin": portal.base},
                body={
                    "sessionId": credentials["session_id"],
                    "sessionToken": credentials["session_token"],
                },
            )
            require(status == 200, "portal_exchange")
            checked_cookies(
                headers,
                ["__Host-identitycore_verify", "__Host-identitycore_verify_id"],
                "/",
            )
        finally:
            status, _, _ = portal.request(
                "DELETE", "/api/verification/session", headers={"Origin": portal.base}
            )
            require(status == 200, "portal_cleanup")

    check("portal_session_cookies", portal_cookie)
    return {
        "environment": config["environment"],
        "passed": all(r["passed"] for r in results),
        "checks": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ca-file")
    args = parser.parse_args()
    try:
        config = json.loads(Path(args.config).read_text())
        credentials = {
            name: os.environ.get("DEPLOYMENT_SMOKE_" + name.upper(), "")
            for name in ("email", "password", "session_id", "session_token")
        }
        report = run(config, credentials, ca_file=args.ca_file)
    except Exception:
        report = {
            "passed": False,
            "checks": [{"check": "configuration", "passed": False}],
        }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(
        "Deployment security checks passed."
        if report["passed"]
        else "Deployment security checks failed. See sanitized report."
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
