#!/usr/bin/env python3
"""Require fresh HTTPS readiness before routing candidate deployment traffic."""

import argparse
import json
import ssl
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def check(base, *, timeout=30, ca_file=None):
    parsed = urlsplit(base)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or not 1 <= timeout <= 120
    ):
        return False
    context = ssl.create_default_context(cafile=ca_file)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = build_opener(HTTPSHandler(context=context), NoRedirect())
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        try:
            with opener.open(
                Request(
                    base.rstrip("/") + "/api/v1/ready",
                    headers={"Accept": "application/json"},
                ),
                timeout=max(0.01, min(5, remaining)),
            ) as response:
                payload = response.read(4097)
                if (
                    response.status == 200
                    and len(payload) <= 4096
                    and "no-store" in response.headers.get("Cache-Control", "").lower()
                    and json.loads(payload).get("data", {}).get("status") == "ready"
                ):
                    return True
        except Exception:
            pass
        time.sleep(min(0.25, max(0, deadline - time.monotonic())))
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--ca-file")
    args = parser.parse_args()
    try:
        passed = check(args.api, timeout=args.timeout, ca_file=args.ca_file)
    except Exception:
        passed = False
    Path(args.output).write_text(
        json.dumps({"check": "candidate_readiness", "passed": passed}) + "\n"
    )
    print(
        "Candidate readiness passed."
        if passed
        else "Candidate readiness failed; promotion is blocked."
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
