"""Fetch and verify the approved initial MiniFASNetV2 PAD asset.

The binary is intentionally kept outside Git. The destination should normally
be the mounted AI_MODEL_ROOT volume used by the AI service.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


MODEL_URL = (
    "https://huggingface.co/garciafido/minifasnet-v2-anti-spoofing-onnx/"
    "resolve/main/minifasnet_v2.onnx?download=true"
)
LICENSE_URL = (
    "https://huggingface.co/garciafido/minifasnet-v2-anti-spoofing-onnx/"
    "raw/main/LICENSE"
)
EXPECTED_SHA256 = "d7b3cd9ba8a7ceb13baa8c4720902e27ca3112eff52f926c08804af6b6eecc7b"


def download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "IdentityCore-model-bootstrap/1"})
    with urlopen(request, timeout=120) as response:
        destination.write_bytes(response.read())


def download_verified_model(url: str, destination: Path, expected_sha256: str) -> str:
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".download",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        download(url, temporary_path)
        digest = hashlib.sha256(temporary_path.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise SystemExit(
                f"PAD model checksum mismatch: expected {expected_sha256}, got {digest}"
            )
        os.replace(temporary_path, destination)
        temporary_path = None
        return digest
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-root", type=Path, default=Path("/opt/identitycore/models")
    )
    args = parser.parse_args()
    target_dir = args.model_root / "liveness"
    target_dir.mkdir(parents=True, exist_ok=True)
    model_path = target_dir / "pad.onnx"
    license_path = target_dir / "MiniFASNetV2-LICENSE.txt"

    digest = download_verified_model(MODEL_URL, model_path, EXPECTED_SHA256)
    download(LICENSE_URL, license_path)
    print(f"Verified PAD model: {model_path} ({digest})")
    print(f"Saved model attribution: {license_path}")


if __name__ == "__main__":
    main()
