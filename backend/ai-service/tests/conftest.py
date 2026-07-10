import os


# Unit tests exercise deterministic provider responses explicitly. Runtime defaults
# to real processing so a missing deployment setting can never approve evidence.
os.environ.setdefault("AI_SERVICE_MODE", "mock")
