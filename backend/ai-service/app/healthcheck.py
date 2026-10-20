"""Container readiness probe with bounded, credential-free diagnostics."""

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check(*, url="http://127.0.0.1:8001/v1/ready", token="", output=None):
    output = sys.stdout if output is None else output
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(url, headers={"X-Internal-Token": token})
    try:
        try:
            response = opener.open(request, timeout=4)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            body = response.read(65537)
        if status in {401, 403}:
            print(
                "AI readiness authentication failed; check AI_SERVICE_SHARED_TOKEN.",
                file=output,
            )
            return 1
        if len(body) > 65536:
            raise ValueError()
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError()
        if status == 200 and payload.get("ready") is True:
            print("AI service is ready.", file=output)
            return 0
        missing = payload.get("missing_requirements", [])
        if (
            not isinstance(missing, list)
            or len(missing) > 64
            or any(not isinstance(item, str) or len(item) > 512 for item in missing)
        ):
            raise ValueError()
        # Only emit the documented requirement codes. Never echo an arbitrary
        # error response, token, credentials, settings object or stack trace.
        codes = sorted({item.split(":", 1)[0] for item in missing})
        if not all(
            code.startswith(
                ("models.", "object_storage.", "auth.", "runtime.", "dependencies.")
            )
            and all(character.isalnum() or character in "._-" for character in code)
            for code in codes
        ):
            raise ValueError()
        print(
            "AI service is not ready" + (": " + ", ".join(codes) if codes else "."),
            file=output,
        )
        print(
            "Check model provisioning and AI_MODEL_MANIFEST_SHA256, object storage and the AI startup log; see backend/README.md.",
            file=output,
        )
        return 1
    except (URLError, TimeoutError, OSError):
        print(
            "AI service is not accepting readiness requests; inspect docker compose logs --tail=40 ai-service.",
            file=output,
        )
        return 1
    except (ValueError, UnicodeError):
        print(
            "AI readiness returned an invalid response; inspect the AI service log.",
            file=output,
        )
        return 1


def main():
    return check(token=os.getenv("AI_SERVICE_SHARED_TOKEN", ""))


if __name__ == "__main__":
    raise SystemExit(main())
