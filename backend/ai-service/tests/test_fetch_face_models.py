import hashlib
import importlib.util
import io
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fetch_face_models.py"
spec = importlib.util.spec_from_file_location("fetch_face_models", SCRIPT)
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


@pytest.mark.parametrize("body", [b"tampered", b"candidate plus extra"])
def test_invalid_download_preserves_prior_asset_and_removes_temporary_file(
    monkeypatch, tmp_path, body
):
    target = tmp_path / "model.onnx"
    target.write_bytes(b"prior reviewed model")
    monkeypatch.setattr(fetch, "urlopen", lambda *a, **k: io.BytesIO(body))
    asset = {
        "name": target.name,
        "url": "https://invalid.example/model.onnx",
        "bytes": len(b"candidate"),
        "sha256": hashlib.sha256(b"candidate").hexdigest(),
    }
    with pytest.raises(ValueError):
        fetch.download_verified(asset, tmp_path)
    assert target.read_bytes() == b"prior reviewed model"
    assert list(tmp_path.iterdir()) == [target]
