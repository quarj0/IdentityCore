"""Fetch the pinned MIT YuNet and Apache-2.0 SFace candidate, including notices.

This prepares assets for review. It never sets the approved manifest digest.
"""

from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

SOURCE_COMMIT = "48b10fa505aeb51fbd127fc60a5c660040e823b7"
ASSETS = [
    {
        "name": "yunet-2026may.onnx",
        "url": "https://media.githubusercontent.com/media/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/face_detection_yunet_2026may.onnx",
        "sha256": "ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0",
        "bytes": 229738,
    },
    {
        "name": "YUNET-LICENSE.txt",
        "url": "https://raw.githubusercontent.com/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/LICENSE",
        "sha256": "c83b8120c50ccbd4c4f96edf53141bdd566ebb8f8e9227e415326aa1b1aba958",
        "bytes": 1085,
    },
    {
        "name": "sface-2021dec.onnx",
        "url": "https://media.githubusercontent.com/media/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        "bytes": 38696353,
    },
    {
        "name": "SFACE-LICENSE.txt",
        "url": "https://raw.githubusercontent.com/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/LICENSE",
        "sha256": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        "bytes": 11358,
    },
]


def download_verified(asset, root):
    destination = root / asset["name"]
    temporary = None
    try:
        digest = hashlib.sha256()
        total = 0
        with tempfile.NamedTemporaryFile(
            dir=root, prefix=".model-", delete=False
        ) as output:
            temporary = Path(output.name)
            request = Request(
                asset["url"], headers={"User-Agent": "IdentityCore-model-bootstrap/1"}
            )
            with urlopen(request, timeout=120) as response:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    total += len(chunk)
                    if total > asset["bytes"]:
                        raise ValueError("Model asset exceeds pinned size.")
                    digest.update(chunk)
                    output.write(chunk)
        if total != asset["bytes"] or digest.hexdigest() != asset["sha256"]:
            raise ValueError("Model asset does not match its pinned digest/size.")
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-root", type=Path, default=Path("/opt/identitycore/models")
    )
    args = parser.parse_args()
    root = args.model_root / "face" / "opencv"
    root.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS:
        download_verified(asset, root)
        print("Verified face-model asset: " + asset["name"])
    print(
        "Candidate only: review the manifest, model-use terms and calibration before promotion."
    )


if __name__ == "__main__":
    main()
