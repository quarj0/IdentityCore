import hashlib
import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).parents[3] / "scripts" / "fetch_pad_model.py"
SPEC = importlib.util.spec_from_file_location("fetch_pad_model", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
fetch_pad_model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch_pad_model)


def test_verified_download_preserves_existing_model_on_checksum_failure(
    tmp_path, monkeypatch
):
    destination = tmp_path / "pad.onnx"
    destination.write_bytes(b"existing-approved-model")

    def download_bad_model(url, target):
        target.write_bytes(b"corrupt-download")

    monkeypatch.setattr(fetch_pad_model, "download", download_bad_model)

    with pytest.raises(SystemExit, match="checksum mismatch"):
        fetch_pad_model.download_verified_model(
            "https://example.invalid/pad.onnx",
            destination,
            hashlib.sha256(b"expected-model").hexdigest(),
        )

    assert destination.read_bytes() == b"existing-approved-model"
    assert list(tmp_path.iterdir()) == [destination]


def test_verified_download_atomically_replaces_model_after_checksum_passes(
    tmp_path, monkeypatch
):
    destination = tmp_path / "pad.onnx"
    destination.write_bytes(b"old-model")
    approved_model = b"new-approved-model"

    def download_approved_model(url, target):
        target.write_bytes(approved_model)

    monkeypatch.setattr(fetch_pad_model, "download", download_approved_model)

    fetch_pad_model.download_verified_model(
        "https://example.invalid/pad.onnx",
        destination,
        hashlib.sha256(approved_model).hexdigest(),
    )

    assert destination.read_bytes() == approved_model
    assert list(tmp_path.iterdir()) == [destination]
