import os


# Unit tests exercise deterministic provider responses explicitly. Force mock
# mode for the test process even when Compose loads the production `.env` with
# AI_SERVICE_MODE=real; the long-running service remains real-mode configured.
os.environ["AI_SERVICE_MODE"] = "mock"
