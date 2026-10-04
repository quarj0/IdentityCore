"""Payload-free exception evidence for the isolated synthetic load gate."""

import json
import os
from pathlib import Path


class LoadExceptionDiagnostics:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        destination = os.environ.get("IDENTITYCORE_LOAD_DIAGNOSTICS_FILE")
        if not destination:
            return None
        frames = []
        trace = exception.__traceback__
        while trace is not None:
            frames.append({"file": Path(trace.tb_frame.f_code.co_filename).name, "function": trace.tb_frame.f_code.co_name, "line": trace.tb_lineno})
            trace = trace.tb_next
        cause = exception.__cause__
        evidence = {"exception": type(exception).__name__, "cause": type(cause).__name__ if cause else None,
                    "sqlstate": getattr(cause, "sqlstate", None), "frames": frames}
        # One append write; no exception messages, source text, locals, URLs or
        # request data are serialized. The file exists only in the guarded load
        # settings' synthetic environment and is folded into its evidence report.
        with open(destination, "a", encoding="utf-8") as output:
            output.write(json.dumps(evidence) + "\n")
        return None
