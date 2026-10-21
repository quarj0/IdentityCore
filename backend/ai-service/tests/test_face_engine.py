import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import time
from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError

from app import face_engine
from app.settings import Settings


def trusted_settings(root):
    settings = Settings(FACE_EMBEDDING_ENGINE="opencv_sface", AI_MODEL_ROOT=root)
    names = list(settings.opencv_face_required_assets) + ["liveness/pad.onnx"]
    for kind in ("det", "rec"):
        names.extend(
            [f"paddleocr/{kind}/inference.yml", f"paddleocr/{kind}/inference.json"]
        )
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"candidate fixture")
    payload = {
        "face_engine": "opencv_sface",
        "face_models": {"detection": names[0], "recognition": names[1]},
        "files": [
            {
                "path": name,
                "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(),
            }
            for name in names
        ],
    }
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps(payload))
    settings.ai_model_manifest_sha256 = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()
    return settings, payload


def test_face_engine_selection_and_required_inventory_are_bound_to_approved_manifest(
    tmp_path,
):
    settings, payload = trusted_settings(tmp_path)
    assert settings.model_asset_integrity_errors() == []
    assert not settings.insightface_model_dir.exists()
    payload["files"] = [
        e for e in payload["files"] if e["path"] != "face/opencv/SFACE-LICENSE.txt"
    ]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload))
    settings.ai_model_manifest_sha256 = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()
    assert (
        "models.manifest_required_asset_missing:face/opencv/SFACE-LICENSE.txt"
        in settings.model_asset_integrity_errors()
    )
    payload["face_engine"] = "insightface"
    manifest.write_text(json.dumps(payload))
    settings.ai_model_manifest_sha256 = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()
    assert "models.face_engine_mismatch" in settings.model_asset_integrity_errors()
    with pytest.raises(ValidationError):
        Settings(FACE_EMBEDDING_ENGINE="unapproved")


def test_analyzer_serializes_shape_changes_and_preserves_no_face_results(monkeypatch):
    class Detector:
        def setInputSize(self, size):
            self.size = size
            time.sleep(0.01)

        def detect(self, image):
            assert self.size == (image.shape[1], image.shape[0])
            if image[0, 0, 0] == 0:
                return 0, None
            return 1, np.array([[1, 2, 10, 20] + [0] * 10 + [0.99]], dtype=np.float32)

    class Recognizer:
        def alignCrop(self, image, detection):
            return image

        def feature(self, image):
            return np.array([[1.0, 2.0]], dtype=np.float32)

    monkeypatch.setattr(
        face_engine.cv2,
        "FaceDetectorYN",
        SimpleNamespace(create=lambda *a, **k: Detector()),
    )
    monkeypatch.setattr(
        face_engine.cv2,
        "FaceRecognizerSF",
        SimpleNamespace(create=lambda *a, **k: Recognizer()),
    )
    analyzer = face_engine.OpenCVFaceAnalyzer(
        SimpleNamespace(
            opencv_face_detection_path=Path("det.onnx"),
            opencv_face_recognition_path=Path("rec.onnx"),
        )
    )
    assert analyzer.get(np.zeros((10, 20, 3), dtype=np.uint8)) == []
    barrier = Barrier(2)

    def infer(shape):
        barrier.wait(timeout=2)
        return analyzer.get(np.ones(shape, dtype=np.uint8))[0]

    with ThreadPoolExecutor(max_workers=2) as pool:
        faces = list(pool.map(infer, [(20, 30, 3), (50, 60, 3)]))
    assert all(np.array_equal(face.bbox, [1, 2, 11, 22]) for face in faces)
    large = analyzer.get(np.ones((800, 1600, 3), dtype=np.uint8))[0]
    assert np.allclose(large.bbox, [2.5, 5, 27.5, 55])
    analyzer.recognizer.feature = lambda image: np.array([[np.nan, 0]])
    with pytest.raises(ValueError, match="invalid embedding"):
        analyzer.get(np.ones((20, 30, 3), dtype=np.uint8))
