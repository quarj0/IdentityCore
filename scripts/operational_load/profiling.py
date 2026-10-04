"""Opt-in fixture profiling of fixed routes; never collect arguments or payloads."""

import cProfile
import json
import os
import pstats


class LoadProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = os.getenv("IDENTITYCORE_LOAD_PROFILE_FILE")
        operation = ""
        if (
            request.method == "POST"
            and request.path.rstrip("/") == "/api/v1/verifications"
        ):
            operation = "session"
        elif request.method == "POST" and request.path.endswith("/decision"):
            operation = "review"
        if not path or not operation:
            response = self.get_response(request)
            response["X-IdentityCore-Load-Worker"] = str(os.getpid())
            return response
        profiler = cProfile.Profile()
        response = profiler.runcall(self.get_response, request)
        stats = pstats.Stats(profiler).stats
        rows = [
            {
                "function": str(key),
                "calls": value[1],
                "self_seconds": round(value[2], 6),
                "cumulative_seconds": round(value[3], 6),
            }
            for key, value in sorted(
                stats.items(), key=lambda item: item[1][3], reverse=True
            )[:40]
        ]
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(
                descriptor,
                (
                    json.dumps({"operation": operation, "functions": rows}) + "\n"
                ).encode(),
            )
        finally:
            os.close(descriptor)
        response["X-IdentityCore-Load-Worker"] = str(os.getpid())
        return response
