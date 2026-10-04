#!/usr/bin/env python3
"""Create private, disposable operational drill credentials. Never print values."""

import argparse
import base64
from pathlib import Path
import secrets

parser = argparse.ArgumentParser()
parser.add_argument("--directory", required=True)
args = parser.parse_args()
root = Path(args.directory)
root.mkdir(parents=True, mode=0o700, exist_ok=True)
values = {
    "POSTGRES_USER": "identitycore_drill",
    "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
    "DRILL_STORAGE_ACCESS_KEY": secrets.token_urlsafe(24),
    "DRILL_STORAGE_SECRET_KEY": secrets.token_urlsafe(32),
    "DRILL_APPLICATION_SECRET": secrets.token_urlsafe(48),
}
path = root / "drill.env"
path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
path.chmod(0o600)
key = root / "backup.key"
key.write_bytes(base64.b64encode(secrets.token_bytes(32)))
key.chmod(0o600)
