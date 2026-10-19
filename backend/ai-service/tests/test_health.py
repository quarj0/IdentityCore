import asyncio
import hashlib
import json
import sys
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

pytest.importorskip("fastapi")

from fastapi import HTTPException

from app.main import (
    DocumentClassificationRequest,
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    LivenessCheckRequest,
    _enforce_internal_token,
    document_classify,
    document_ocr,
    document_quality,
    face_compare,
    healthcheck,
    liveness_check,
    readiness,
)
from app.pipeline import (
    MediaAsset,
    ProcessingConfigurationError,
    get_paddle_ocr_engine,
    run_document_classification_pipeline,
    run_document_ocr_pipeline,
    run_document_quality_pipeline,
    run_liveness_pipeline,
)
from app.settings import Settings, get_settings


def test_healthcheck():
    response = asyncio.run(healthcheck())

    assert response["status"] == "ok"
    assert response["service"] == "ai-service"
    assert response["mode"] == "mock"


def test_readiness_is_ok_in_mock_mode():
    response = asyncio.run(readiness())

    assert response.status_code == 200


def test_face_compare_returns_completed_match_result():
    response = asyncio.run(
        face_compare(
            FaceCompareRequest(
                verification_id="ver_01TEST",
                selfie_storage_key="uploads/selfies/sel_good",
                document_storage_key="uploads/documents/doc_good",
                threshold=0.85,
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["matched"] is True


def test_liveness_check_returns_failed_for_spoof_key():
    response = asyncio.run(
        liveness_check(
            LivenessCheckRequest(
                verification_id="ver_01TEST",
                selfie_storage_key="uploads/selfies/spoof_case",
                liveness_type="passive",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["passed"] is False


def test_active_liveness_returns_challenge_metadata():
    response = asyncio.run(
        liveness_check(
            LivenessCheckRequest(
                verification_id="ver_01TEST",
                selfie_storage_key="uploads/selfies/sel_good",
                liveness_type="active",
                challenge_actions=[
                    "turn_left",
                    "look_up",
                    "turn_right",
                    "look_down",
                    "turn_left",
                    "look_up",
                    "turn_right",
                    "look_down",
                ],
                challenge_id="lch_test",
                challenge_protocol="ordered_motion_v1",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["challenge_passed"] is True
    assert response["result"]["challenge_id"] == "lch_test"
    assert response["result"]["challenge_protocol"] == "ordered_motion_v1"


@pytest.mark.parametrize(
    "observed,expected",
    [
        (
            [
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
            ],
            True,
        ),
        (["look_up", "turn_left", "turn_right", "look_down", "turn_left"], False),
        (["turn_left", "look_up", "turn_right", "look_down"], False),
        (
            ["turn_left", "look_up", "turn_right", "look_down", "turn_left", "look_up"],
            False,
        ),
    ],
)
def test_real_active_pipeline_requires_exact_observed_order(
    monkeypatch, observed, expected
):
    np = pytest.importorskip("numpy")
    actions = [
        "turn_left",
        "look_up",
        "turn_right",
        "look_down",
        "turn_left",
        "look_up",
        "turn_right",
        "look_down",
    ]
    positions = {
        "turn_left": (0.65, 0.5),
        "turn_right": (0.35, 0.5),
        "look_up": (0.5, 0.35),
        "look_down": (0.5, 0.65),
    }
    centers = [(0.5, 0.5)]
    for action in observed:
        centers.extend([positions[action], (0.5, 0.5)])
    frames = [np.full((8, 8, 3), index, dtype="uint8") for index in range(len(centers))]
    asset = MediaAsset("capture.webm", b"video", "video", frames[0], frames)
    requested = {}

    def load(*args, **kwargs):
        requested.update(kwargs)
        return asset

    def detect(frame):
        x, y = centers[int(frame[0, 0, 0])]
        return [
            {
                "score": 0.99,
                "bbox": {"xmin": x - 0.1, "ymin": y - 0.1, "width": 0.2, "height": 0.2},
            }
        ]

    monkeypatch.setattr("app.pipeline.load_media_asset", load)
    monkeypatch.setattr("app.pipeline._detect_faces", detect)
    monkeypatch.setattr(
        "app.pipeline._compute_image_quality_metrics",
        lambda frame: {"quality_score": 1.0, "blur_variance": 1000.0},
    )
    monkeypatch.setattr(
        "app.pad.run_pad_model",
        lambda *args: {
            "pad_score": 0.99,
            "model_name": "synthetic-pad",
            "model_version": "test",
        },
    )
    result = run_liveness_pipeline(
        "capture.webm",
        "active",
        challenge_actions=actions,
        challenge_id="lch_ordered",
        challenge_protocol="ordered_motion_v1",
    )
    assert result["passed"] is expected
    assert result["challenge_passed"] is expected
    assert result["metrics"]["detected_actions"] == observed
    assert result["challenge_id"] == "lch_ordered"
    assert requested["frame_sample_limit"] == 48


@pytest.mark.parametrize(
    "updates",
    [
        {"challenge_id": ""},
        {"challenge_protocol": "legacy"},
        {"challenge_actions": ["turn_left", "look_up"]},
    ],
)
def test_active_request_rejects_legacy_or_missing_challenge(updates):
    from pydantic import ValidationError

    fields = dict(
        verification_id="ver_test",
        selfie_storage_key="capture.webm",
        liveness_type="active",
        challenge_actions=[
            "turn_left",
            "look_up",
            "turn_right",
            "look_down",
            "turn_left",
            "look_up",
            "turn_right",
            "look_down",
        ],
        challenge_id="lch_test",
        challenge_protocol="ordered_motion_v1",
    )
    with pytest.raises(ValidationError):
        LivenessCheckRequest(**{**fields, **updates})


def test_document_ocr_returns_extracted_fields():
    response = asyncio.run(
        document_ocr(
            DocumentOCRRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/doc_good",
                document_type="national_id",
                country_code="GH",
            )
        )
    )

    assert response["status"] == "completed"
    assert "full_name" in response["result"]["extracted_fields"]


def test_document_ocr_returns_manual_review_when_media_is_missing(monkeypatch):
    missing_object_error = ClientError(
        {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        },
        "GetObject",
    )

    def raise_missing_object(*args, **kwargs):
        raise missing_object_error

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", raise_missing_object)

    result = run_document_ocr_pipeline(
        "uploads/documents/missing.jpg",
        "national_id",
        "GH",
    )

    assert result["confidence_score"] == 0.0
    assert result["requires_manual_review"] is True
    assert result["manual_review"]["required"] is True
    assert "document_media_missing" in result["issues"]


def test_document_quality_flags_blurry_capture():
    response = asyncio.run(
        document_quality(
            DocumentQualityRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/doc_blur_case",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["issues"] == ["blur_detected"]


def test_document_quality_returns_review_signal_when_media_is_missing(monkeypatch):
    missing_object_error = ClientError(
        {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        },
        "GetObject",
    )

    def raise_missing_object(*args, **kwargs):
        raise missing_object_error

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", raise_missing_object)

    result = run_document_quality_pipeline("uploads/documents/missing.jpg")

    assert result["issues"] == ["document_media_missing"]
    assert result["quality_score"] == 0.0


def test_document_quality_falls_back_to_alternate_bucket(monkeypatch):
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    image = np.full((120, 120, 3), 180, dtype=np.uint8)
    cv2.putText(
        image,
        "ID",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    success, encoded = cv2.imencode(".jpg", image)
    assert success is True

    seen_buckets: list[str | None] = []

    def fetch_from_media(storage_key, *, bucket_name=None):
        seen_buckets.append(bucket_name)
        if bucket_name == "identitycore-media":
            return encoded.tobytes()
        raise ClientError(
            {
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "The specified key does not exist.",
                }
            },
            "GetObject",
        )

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", fetch_from_media)
    monkeypatch.setenv("OBJECT_STORAGE_MEDIA_BUCKET", "identitycore-media")
    monkeypatch.setenv("OBJECT_STORAGE_TEMP_BUCKET", "identitycore-temp")
    get_settings.cache_clear()

    try:
        result = run_document_quality_pipeline("uploads/documents/fallback.jpg")
    finally:
        monkeypatch.delenv("OBJECT_STORAGE_MEDIA_BUCKET", raising=False)
        monkeypatch.delenv("OBJECT_STORAGE_TEMP_BUCKET", raising=False)
        get_settings.cache_clear()

    assert "identitycore-media" in seen_buckets
    assert result["model_name"] == "opencv-quality"


def test_document_classification_returns_predicted_type():
    response = asyncio.run(
        document_classify(
            DocumentClassificationRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/national_id_front",
                document_type="national_id",
                country_code="GH",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["predicted_document_type"] == "national_id"
    assert response["result"]["classification_status"] == "recognized"
    assert response["result"]["workflow_action"] == "continue"
    assert response["result"]["manual_review"]["required"] is False


def test_document_classification_returns_manual_review_when_media_is_missing(
    monkeypatch,
):
    missing_object_error = ClientError(
        {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        },
        "GetObject",
    )

    def raise_missing_object(*args, **kwargs):
        raise missing_object_error

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", raise_missing_object)

    result = run_document_classification_pipeline(
        "uploads/documents/missing.jpg",
        "national_id",
        "GH",
    )

    assert result["classification_status"] == "unknown"
    assert result["workflow_action"] == "continue_with_review"
    assert result["requires_manual_review"] is True
    assert result["manual_review"]["required"] is True
    assert "document_media_missing" in result["issues"]


def test_internal_token_is_enforced_when_configured(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_SHARED_TOKEN", "internal-secret")
    get_settings.cache_clear()

    from app import main as main_module

    main_module.settings = get_settings()
    with pytest.raises(HTTPException) as exc:
        _enforce_internal_token("wrong-token")

    _enforce_internal_token("internal-secret")

    assert exc.value.status_code == 401

    monkeypatch.delenv("AI_SERVICE_SHARED_TOKEN", raising=False)
    get_settings.cache_clear()
    main_module.settings = get_settings()


def test_real_document_quality_pipeline_detects_blur(monkeypatch):
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    image = np.full((320, 480, 3), 255, dtype=np.uint8)
    cv2.putText(
        image,
        "IDENTITY",
        (40, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        2.0,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    blurred = cv2.GaussianBlur(image, (31, 31), 0)
    success, encoded = cv2.imencode(".jpg", blurred)
    assert success is True

    monkeypatch.setattr(
        "app.pipeline.fetch_object_bytes",
        lambda storage_key, bucket_name=None: encoded.tobytes(),
    )

    result = run_document_quality_pipeline("uploads/documents/doc_blurred.jpg")

    assert result["model_name"] == "opencv-quality"
    assert "blur_detected" in result["issues"]


def test_local_service_mode_alias_normalizes_to_mock():
    settings = Settings(AI_SERVICE_MODE="local")

    assert settings.service_mode == "mock"


def test_real_mode_requires_storage_and_models(tmp_path):
    settings = Settings(
        AI_SERVICE_MODE="real",
        OBJECT_STORAGE_MEDIA_BUCKET="identitycore-media",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        INSIGHTFACE_ALLOW_DOWNLOAD=False,
        PADDLE_OCR_ALLOW_DOWNLOAD=False,
        AI_MODEL_ROOT=tmp_path,
    )

    missing = settings.real_inference_missing_requirements()

    assert any(item.startswith("models.insightface:") for item in missing)
    assert any(item.startswith("models.paddleocr.det:") for item in missing)
    assert any(item.startswith("models.manifest_missing:") for item in missing)


def _trusted_model_settings(tmp_path, **kwargs):
    paths = [
        "insightface/models/buffalo_l/model.onnx",
        "liveness/pad.onnx",
        "paddleocr/det/inference.yml",
        "paddleocr/det/inference.json",
        "paddleocr/rec/inference.yml",
        "paddleocr/rec/inference.json",
    ]
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"approved-model-fixture")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "insightface_model": "buffalo_l",
                "files": [
                    {
                        "path": name,
                        "sha256": hashlib.sha256(
                            (tmp_path / name).read_bytes()
                        ).hexdigest(),
                    }
                    for name in paths
                ],
            }
        )
    )
    return Settings(
        AI_MODEL_ROOT=tmp_path,
        AI_MODEL_MANIFEST_SHA256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        **kwargs,
    )


def test_model_manifest_detects_missing_and_altered_assets(tmp_path):
    settings = _trusted_model_settings(tmp_path)
    asset = tmp_path / "insightface/models/buffalo_l/model.onnx"
    assert settings.model_asset_integrity_errors() == []
    asset.write_bytes(b"tampered-model")
    assert settings.model_asset_integrity_errors() == [
        "models.asset_checksum_mismatch:insightface/models/buffalo_l/model.onnx"
    ]
    asset.unlink()
    assert settings.model_asset_integrity_errors() == [
        "models.asset_missing:insightface/models/buffalo_l/model.onnx"
    ]


def test_model_manifest_requires_configured_pad_asset(tmp_path):
    settings = _trusted_model_settings(tmp_path)
    assert settings.model_asset_integrity_errors() == []
    settings.pad_model_relative_path = "liveness/other.onnx"
    assert (
        "models.manifest_required_asset_missing:liveness/other.onnx"
        in settings.model_asset_integrity_errors()
    )


def test_real_requirements_validate_pad_model_contract(tmp_path, monkeypatch):
    def reject_contract(model_path, live_class_index):
        raise ProcessingConfigurationError("invalid model contract")

    monkeypatch.setattr("app.pad.validate_pad_model_contract", reject_contract)
    settings = _trusted_model_settings(
        tmp_path,
        AI_SERVICE_MODE="real",
        OBJECT_STORAGE_MEDIA_BUCKET="identitycore-media",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.invalid",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
    )
    assert settings.real_inference_missing_requirements() == [
        f"models.pad_contract_invalid:{tmp_path / 'liveness/pad.onnx'}"
    ]


def test_manifest_requires_external_trust_anchor_and_detects_joint_tampering(tmp_path):
    settings = _trusted_model_settings(tmp_path)
    digest = settings.ai_model_manifest_sha256
    settings.ai_model_manifest_sha256 = ""
    assert settings.model_asset_integrity_errors() == [
        "models.manifest_trust_anchor_required"
    ]
    settings.ai_model_manifest_sha256 = digest
    asset = tmp_path / "insightface/models/buffalo_l/model.onnx"
    asset.write_bytes(b"replacement")
    manifest = tmp_path / "manifest.json"
    payload = json.loads(manifest.read_text())
    for entry in payload["files"]:
        if entry["path"] == str(asset.relative_to(tmp_path)):
            entry["sha256"] = hashlib.sha256(asset.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(payload))
    assert settings.model_asset_integrity_errors() == [
        "models.manifest_checksum_mismatch"
    ]


def test_manifest_rejects_unlisted_assets_selected_model_and_runtime_downloads(
    tmp_path,
):
    settings = _trusted_model_settings(tmp_path)
    extra = tmp_path / "insightface/models/unapproved/model.onnx"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(b"unapproved-model")
    assert settings.model_asset_integrity_errors() == [
        "models.asset_unlisted:insightface/models/unapproved/model.onnx"
    ]
    settings.insightface_model_name = "unapproved"
    errors = settings.model_asset_integrity_errors()
    assert "models.insightface_model_mismatch" in errors
    assert "models.manifest_insightface_assets_missing" in errors
    settings.insightface_allow_download = True
    assert settings.model_asset_integrity_errors() == [
        "models.runtime_downloads_forbidden"
    ]


def test_warm_validation_does_not_reread_model_bytes(tmp_path, monkeypatch):
    from app import model_integrity

    settings = _trusted_model_settings(tmp_path)
    original = model_integrity.file_digest
    reads = []

    def digest(path):
        reads.append(path)
        return original(path)

    monkeypatch.setattr(model_integrity, "file_digest", digest)
    assert settings.model_asset_integrity_errors() == []
    first_reads = list(reads)
    assert len(first_reads) == 7
    for _ in range(3):
        assert settings.model_asset_integrity_errors() == []
    assert reads == first_reads
    asset = tmp_path / "liveness/pad.onnx"
    asset.write_bytes(b"altered")
    assert (
        "models.asset_checksum_mismatch:liveness/pad.onnx"
        in settings.model_asset_integrity_errors()
    )
    assert len(reads) > len(first_reads)


def test_liveness_pad_only_receives_exactly_one_face_frames(monkeypatch):
    frames = [
        pytest.importorskip("numpy").full((8, 8, 3), value, dtype="uint8")
        for value in (10, 20, 30)
    ]
    asset = MediaAsset("capture.mp4", b"video", "video", frames[0], frames)
    bbox = {"xmin": 0.1, "ymin": 0.1, "width": 0.5, "height": 0.5}
    detections = [
        [{"score": 0.9, "bbox": bbox}],
        [],
        [{"score": 0.8, "bbox": bbox}],
    ]
    captured = {}

    monkeypatch.setattr("app.pipeline.load_media_asset", lambda *args, **kwargs: asset)
    monkeypatch.setattr("app.pipeline._detect_faces", lambda frame: detections.pop(0))
    monkeypatch.setattr(
        "app.pipeline._compute_image_quality_metrics",
        lambda frame: {"quality_score": 1.0, "blur_variance": 1000.0},
    )

    def run_pad(frames_to_score, bboxes_to_score):
        captured["frames"] = frames_to_score
        captured["bboxes"] = bboxes_to_score
        return {"pad_score": 0.99, "model_name": "pad", "model_version": "test"}

    monkeypatch.setattr("app.pad.run_pad_model", run_pad)

    run_liveness_pipeline("capture.mp4", "passive")

    assert captured["frames"] == [frames[0], frames[2]]
    assert captured["bboxes"] == [bbox, bbox]


def test_liveness_fails_video_without_two_single_face_frames(monkeypatch):
    np = pytest.importorskip("numpy")
    frames = [np.zeros((8, 8, 3), dtype="uint8") for _ in range(3)]
    asset = MediaAsset("capture.mp4", b"video", "video", frames[0], frames)
    bbox = {"xmin": 0.1, "ymin": 0.1, "width": 0.5, "height": 0.5}
    detections = [[{"score": 0.9, "bbox": bbox}], [], []]

    monkeypatch.setattr("app.pipeline.load_media_asset", lambda *args, **kwargs: asset)
    monkeypatch.setattr("app.pipeline._detect_faces", lambda frame: detections.pop(0))
    monkeypatch.setattr(
        "app.pipeline._compute_image_quality_metrics",
        lambda frame: {"quality_score": 1.0, "blur_variance": 1000.0},
    )

    result = run_liveness_pipeline("capture.mp4", "passive")

    assert result["passed"] is False
    assert result["issues"] == ["insufficient_single_face_frames"]


def test_liveness_requires_two_valid_frames_for_single_frame_video(monkeypatch):
    np = pytest.importorskip("numpy")
    frame = np.zeros((8, 8, 3), dtype="uint8")
    asset = MediaAsset("capture.mp4", b"video", "video", frame, [frame])
    bbox = {"xmin": 0.1, "ymin": 0.1, "width": 0.5, "height": 0.5}

    monkeypatch.setattr("app.pipeline.load_media_asset", lambda *args, **kwargs: asset)
    monkeypatch.setattr(
        "app.pipeline._detect_faces",
        lambda captured_frame: [{"score": 0.9, "bbox": bbox}],
    )
    monkeypatch.setattr(
        "app.pipeline._compute_image_quality_metrics",
        lambda captured_frame: {"quality_score": 1.0, "blur_variance": 1000.0},
    )

    result = run_liveness_pipeline("capture.mp4", "passive")

    assert result["passed"] is False
    assert result["issues"] == ["insufficient_single_face_frames"]


def test_real_mode_accepts_r2_storage_aliases(tmp_path):
    settings = Settings(
        AI_SERVICE_MODE="real",
        R2_MEDIA_BUCKET="identitycore-media",
        R2_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        R2_ACCESS_KEY_ID="key",
        R2_SECRET_ACCESS_KEY="secret",
        INSIGHTFACE_ALLOW_DOWNLOAD=True,
        PADDLE_OCR_ALLOW_DOWNLOAD=True,
        AI_MODEL_ROOT=tmp_path,
    )

    assert settings.real_inference_missing_requirements() == [
        f"models.manifest_missing:{tmp_path / 'manifest.json'}",
        f"models.pad:{tmp_path / 'liveness' / 'pad.onnx'}",
    ]


def test_hybrid_mode_is_degraded_but_ready_when_real_requirements_are_missing(
    monkeypatch,
):
    monkeypatch.setenv("AI_SERVICE_MODE", "hybrid")
    monkeypatch.setenv("OBJECT_STORAGE_MEDIA_BUCKET", "")
    monkeypatch.setenv("OBJECT_STORAGE_BUCKET", "")
    monkeypatch.setenv("OBJECT_STORAGE_ENDPOINT_URL", "")
    monkeypatch.setenv("OBJECT_STORAGE_ACCESS_KEY_ID", "")
    monkeypatch.setenv("OBJECT_STORAGE_SECRET_ACCESS_KEY", "")
    monkeypatch.setenv("INSIGHTFACE_ALLOW_DOWNLOAD", "0")
    monkeypatch.setenv("PADDLE_OCR_ALLOW_DOWNLOAD", "0")
    get_settings.cache_clear()

    response = asyncio.run(readiness())
    payload = response.body.decode("utf-8")

    assert response.status_code == 200
    assert '"status":"degraded"' in payload
    assert '"ready":true' in payload

    monkeypatch.delenv("AI_SERVICE_MODE", raising=False)
    monkeypatch.delenv("INSIGHTFACE_ALLOW_DOWNLOAD", raising=False)
    monkeypatch.delenv("PADDLE_OCR_ALLOW_DOWNLOAD", raising=False)
    get_settings.cache_clear()


def test_real_paddle_ocr_disables_unstable_optional_classifiers(monkeypatch, tmp_path):
    det = tmp_path / "det"
    rec = tmp_path / "rec"
    for directory, model_name in (
        (det, "PP-OCRv5_server_det"),
        (rec, "PP-OCRv5_server_rec"),
    ):
        directory.mkdir()
        (directory / "inference.yml").write_text(
            f"Global:\n  model_name: {model_name}\n",
            encoding="utf-8",
        )
        (directory / "inference.json").write_text("{}", encoding="utf-8")

    captured = {}

    class FakePaddleOCR:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    settings = SimpleNamespace(
        paddle_allow_download=False,
        paddle_text_detection_model_dir=det,
        paddle_text_recognition_model_dir=rec,
        paddle_model_is_complete=lambda path: (
            (path / "inference.yml").is_file() and (path / "inference.json").is_file()
        ),
    )
    monkeypatch.setattr("app.pipeline.get_settings", lambda: settings)
    monkeypatch.setitem(
        sys.modules,
        "paddleocr",
        SimpleNamespace(PaddleOCR=FakePaddleOCR),
    )
    get_paddle_ocr_engine.cache_clear()

    try:
        get_paddle_ocr_engine()
    finally:
        get_paddle_ocr_engine.cache_clear()

    assert captured["use_doc_orientation_classify"] is False
    assert captured["use_doc_unwarping"] is False
    assert captured["use_textline_orientation"] is False
    assert captured["enable_mkldnn"] is False
    assert "textline_orientation_model_dir" not in captured


def test_ocr_pipeline_retains_mrz_checksum_and_field_provenance(monkeypatch):
    import numpy as np
    from types import SimpleNamespace
    from app import pipeline

    lines = [
        "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
        "L898902C36UTO7408122F1204159ZE184226B<<<<<10",
    ]
    monkeypatch.setattr(
        pipeline,
        "load_media_asset",
        lambda *args, **kwargs: SimpleNamespace(
            primary_frame=np.zeros((4, 4, 3), dtype=np.uint8)
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "get_paddle_ocr_engine",
        lambda: SimpleNamespace(
            predict=lambda image: [{"rec_texts": lines, "rec_scores": [0.99, 0.99]}]
        ),
    )
    result = pipeline.run_document_ocr_pipeline("synthetic/key", "passport", "GH")
    assert result["mrz_evidence"]["status"] == "valid"
    assert result["extracted_fields"]["document_number"] == "L898902C3"
    field = result["extracted_fields"]["mrz_fields"]["document_number"]
    assert field["provenance"]["ocr_line"] == 1
    assert result["extracted_fields"]["mrz_evidence"] == result["mrz_evidence"]
    lines[1] = "Z" + lines[1][1:]
    result = pipeline.run_document_ocr_pipeline("synthetic/key", "passport", "GH")
    assert result["mrz_evidence"]["status"] == "invalid"
    assert "mrz_fields" not in result["extracted_fields"]
    assert result["issues"] == ["mrz_checksum_invalid"]


def test_labeled_document_dates_do_not_confuse_issue_date_with_birth():
    from app.pipeline import _normalize_ocr_fields

    result = _normalize_ocr_fields(
        ["ISSUED 2020-01-02", "EXPIRES 2030/02/03", "DOB 2000-10-04"], "passport", "GH"
    )
    assert result["date_of_birth"] == "2000-10-04"
    assert result["issue_date"] == "2020-01-02"
    assert result["expiry_date"] == "2030-02-03"
    assert (
        _normalize_ocr_fields(["ISSUED 2020-01-02"], "passport", "GH")["date_of_birth"]
        == ""
    )


@pytest.mark.parametrize(
    "damage", ["unlisted", "anchor", "joint_replacement", "configured_model"]
)
def test_real_processing_refuses_untrusted_inventory_before_inference(
    tmp_path, monkeypatch, damage
):
    from app.pipeline import run_with_mode, ProcessingError

    settings = _trusted_model_settings(tmp_path, AI_SERVICE_MODE="real")
    if damage == "unlisted":
        (tmp_path / "new-model.onnx").write_bytes(b"unlisted")
    elif damage == "anchor":
        settings.ai_model_manifest_sha256 = ""
    elif damage == "configured_model":
        settings.insightface_model_name = "unapproved"
    else:
        asset = tmp_path / "liveness/pad.onnx"
        asset.write_bytes(b"replaced")
        manifest = tmp_path / "manifest.json"
        payload = json.loads(manifest.read_text())
        for entry in payload["files"]:
            if entry["path"] == "liveness/pad.onnx":
                entry["sha256"] = hashlib.sha256(asset.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(payload))
    monkeypatch.setattr("app.pipeline.get_settings", lambda: settings)

    def forbidden():
        pytest.fail("Untrusted inventory reached inference")

    with pytest.raises(
        ProcessingError, match="Model asset integrity validation failed"
    ):
        run_with_mode(real_callable=forbidden, mock_callable=forbidden, mock_args=())


def test_manifest_rejects_omitted_configured_engine_files(tmp_path):
    settings = _trusted_model_settings(tmp_path)
    manifest = tmp_path / "manifest.json"
    payload = json.loads(manifest.read_text())
    omitted = {
        "paddleocr/rec/inference.json",
        "insightface/models/buffalo_l/model.onnx",
    }
    payload["files"] = [
        entry for entry in payload["files"] if entry["path"] not in omitted
    ]
    manifest.write_text(json.dumps(payload))
    settings.ai_model_manifest_sha256 = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()
    errors = settings.model_asset_integrity_errors()
    assert "models.manifest_insightface_assets_missing" in errors
    assert "models.manifest_paddle_assets_missing:rec" in errors
    for name in omitted:
        assert f"models.asset_unlisted:{name}" in errors
