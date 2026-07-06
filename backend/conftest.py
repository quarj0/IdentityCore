from pathlib import Path
import sys


AI_SERVICE_ROOT = Path(__file__).resolve().parent / "ai-service"

if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))
