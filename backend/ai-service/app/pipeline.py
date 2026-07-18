from __future__ import annotations

import math
import re
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from botocore.exceptions import ClientError

from app.document_classification import build_ocr_lines, classify_document
from app.settings import get_settings
from app.storage import (
    fetch_object_bytes,
    get_object_storage_media_bucket_name,
    get_object_storage_temp_bucket_name,
)


class ProcessingConfigurationError(RuntimeError):
    pass


class ProcessingError(RuntimeError):
    pass


class MediaAssetNotFoundError(RuntimeError):
    def __init__(self, storage_key: str, bucket_name: str):
        message = f"Media asset '{storage_key}' was not found in bucket '{bucket_name}'."
        super().__init__(message)
        self.storage_key = storage_key
        self.bucket_name = bucket_name


@dataclass
class MediaAsset:
    storage_key: str
    content: bytes
    kind: str
    primary_frame: np.ndarray
    frames: list[np.ndarray]


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _confidence_label(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "medium"
    return "low"


def _safe_mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _decode_image_bytes(content: bytes) -> np.ndarray | None:
    buffer = np.frombuffer(content, dtype=np.uint8)
    if buffer.size == 0:
        return None
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    return image


def _sample_video_frames(content: bytes, storage_key: str, limit: int) -> list[np.ndarray]:
    suffix = Path(storage_key).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    frames: list[np.ndarray] = []
    capture = cv2.VideoCapture(str(temp_path))
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        step = max(1, math.ceil(frame_count / limit)) if frame_count else 1
        index = 0
        while len(frames) < limit:
            success, frame = capture.read()
            if not success:
                break
            if index % step == 0:
                frames.append(frame)
            index += 1
    finally:
        capture.release()
        temp_path.unlink(missing_ok=True)
    return frames


def load_media_asset(storage_key: str, bucket_name: str | None = None) -> MediaAsset:
    settings = get_settings()
    media_bucket_name = get_object_storage_media_bucket_name()
    temp_bucket_name = get_object_storage_temp_bucket_name()
    candidate_buckets: list[str] = []
    if bucket_name:
        candidate_buckets.append(bucket_name)
        candidate_buckets.extend(
            [
                media_bucket_name if bucket_name != media_bucket_name else "",
                temp_bucket_name if bucket_name != temp_bucket_name else "",
            ]
        )
    else:
        candidate_buckets.extend([media_bucket_name, temp_bucket_name])
    candidate_buckets = list(dict.fromkeys(bucket for bucket in candidate_buckets if bucket))
    last_error: ClientError | None = None
    content: bytes | None = None
    resolved_bucket_name = candidate_buckets[0] if candidate_buckets else "<unconfigured>"
    for candidate_bucket in candidate_buckets or [""]:
        try:
            if candidate_bucket:
                content = fetch_object_bytes(storage_key, bucket_name=candidate_bucket)
            else:
                content = fetch_object_bytes(storage_key)
            resolved_bucket_name = candidate_bucket or resolved_bucket_name
            break
        except ClientError as exc:
            error_code = (exc.response.get("Error") or {}).get("Code", "")
            if error_code in {"NoSuchKey", "404", "NotFound", "NoSuchBucket"}:
                last_error = exc
                continue
            raise
    if content is None:
        bucket_label = resolved_bucket_name or "<unconfigured>"
        if candidate_buckets:
            bucket_label = ", ".join(candidate_buckets)
        raise MediaAssetNotFoundError(
            storage_key=storage_key,
            bucket_name=bucket_label,
        ) from last_error
    image = _decode_image_bytes(content)
    if image is not None:
        return MediaAsset(
            storage_key=storage_key,
            content=content,
            kind="image",
            primary_frame=image,
            frames=[image],
        )

    frames = _sample_video_frames(
        content=content,
        storage_key=storage_key,
        limit=settings.video_frame_sample_limit,
    )
    if not frames:
        raise ProcessingError(f"Could not decode media for storage key '{storage_key}'.")
    return MediaAsset(
        storage_key=storage_key,
        content=content,
        kind="video",
        primary_frame=frames[0],
        frames=frames,
    )


@lru_cache
def get_mediapipe_face_detector():
    import mediapipe as mp

    settings = get_settings()
    return mp.solutions.face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=settings.mediapipe_min_detection_confidence,
    )


def _detect_faces(frame: np.ndarray) -> list[dict[str, Any]]:
    detector = get_mediapipe_face_detector()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = detector.process(rgb_frame)
    detections: list[dict[str, Any]] = []
    for detection in result.detections or []:
        bbox = detection.location_data.relative_bounding_box
        detections.append(
            {
                "score": float(detection.score[0]) if detection.score else 0.0,
                "bbox": {
                    "xmin": float(bbox.xmin),
                    "ymin": float(bbox.ymin),
                    "width": float(bbox.width),
                    "height": float(bbox.height),
                },
            }
        )
    return detections


def _bbox_center(bbox: dict[str, float]) -> tuple[float, float]:
    return (
        bbox["xmin"] + (bbox["width"] / 2.0),
        bbox["ymin"] + (bbox["height"] / 2.0),
    )


def _infer_motion_directions(
    centers: list[tuple[float, float]], *, movement_threshold: float = 0.03
) -> list[str]:
    directions: list[str] = []
    for prev, curr in zip(centers, centers[1:]):
        x_delta = curr[0] - prev[0]
        y_delta = curr[1] - prev[1]
        if x_delta >= movement_threshold:
            directions.append("turn_right")
        elif x_delta <= -movement_threshold:
            directions.append("turn_left")
        if y_delta >= movement_threshold:
            directions.append("look_down")
        elif y_delta <= -movement_threshold:
            directions.append("look_up")
    return list(dict.fromkeys(directions))


def _compute_image_quality_metrics(frame: np.ndarray) -> dict[str, float]:
    grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur_variance = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
    brightness = float(np.mean(grayscale))
    contrast = float(np.std(grayscale))
    glare_ratio = float(np.mean(grayscale >= 245))

    blur_score = _clamp(blur_variance / 200.0)
    brightness_score = 1.0 - min(abs(brightness - 140.0) / 140.0, 1.0)
    contrast_score = _clamp(contrast / 64.0)
    glare_score = 1.0 - _clamp(glare_ratio / 0.20)
    overall = _clamp(
        (blur_score * 0.35)
        + (brightness_score * 0.25)
        + (contrast_score * 0.20)
        + (glare_score * 0.20)
    )

    return {
        "blur_variance": blur_variance,
        "brightness": brightness,
        "contrast": contrast,
        "glare_ratio": glare_ratio,
        "quality_score": overall,
    }


def run_document_quality_pipeline(
    storage_key: str, *, bucket_name: str | None = None
) -> dict[str, Any]:
    settings = get_settings()
    try:
        asset = load_media_asset(storage_key, bucket_name=bucket_name)
    except MediaAssetNotFoundError:
        return {
            "quality_score": 0.0,
            "issues": ["document_media_missing"],
            "metrics": {
                "blur_variance": 0.0,
                "brightness": 0.0,
                "contrast": 0.0,
                "glare_ratio": 0.0,
                "quality_score": 0.0,
            },
            "model_name": "opencv-quality",
            "model_version": "v1",
        }
    metrics = _compute_image_quality_metrics(asset.primary_frame)
    issues: list[str] = []

    if metrics["blur_variance"] < settings.document_quality_blur_threshold:
        issues.append("blur_detected")
    if metrics["brightness"] < settings.document_quality_dark_threshold:
        issues.append("underexposed")
    if metrics["brightness"] > settings.document_quality_bright_threshold:
        issues.append("overexposed")
    if metrics["glare_ratio"] > settings.document_quality_glare_threshold:
        issues.append("glare_detected")

    return {
        "quality_score": round(metrics["quality_score"], 4),
        "issues": issues,
        "metrics": metrics,
        "model_name": "opencv-quality",
        "model_version": "v1",
    }


def run_liveness_pipeline(
    storage_key: str,
    liveness_type: str,
    *,
    challenge_actions: list[str] | None = None,
    bucket_name: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    asset = load_media_asset(storage_key, bucket_name=bucket_name)
    frame_detections = [_detect_faces(frame) for frame in asset.frames]
    face_presence_ratio = _safe_mean(
        [1.0 if len(detections) == 1 else 0.0 for detections in frame_detections]
    )
    max_face_count = max((len(detections) for detections in frame_detections), default=0)
    avg_detection_confidence = _safe_mean(
        [
            detections[0]["score"]
            for detections in frame_detections
            if len(detections) == 1
        ]
    )
    quality_metrics = _compute_image_quality_metrics(asset.primary_frame)

    movement_score = 0.0
    centers = [
        _bbox_center(detections[0]["bbox"])
        for detections in frame_detections
        if len(detections) == 1
    ]
    if len(centers) >= 2:
        deltas = [
            abs(curr[0] - prev[0]) + abs(curr[1] - prev[1])
            for prev, curr in zip(centers, centers[1:])
        ]
        movement_score = _clamp(_safe_mean(deltas) * 3.0)
    detected_actions = _infer_motion_directions(centers)
    challenge_actions = challenge_actions or []

    score_components = [
        face_presence_ratio * 0.45,
        avg_detection_confidence * 0.25,
        quality_metrics["quality_score"] * 0.20,
        movement_score * 0.10,
    ]
    score = _clamp(sum(score_components))
    issues: list[str] = []
    passed = score >= settings.liveness_min_score

    if max_face_count == 0:
        issues.append("no_face_detected")
        passed = False
    elif max_face_count > 1:
        issues.append("multiple_faces_detected")
        passed = False
    if quality_metrics["blur_variance"] < settings.document_quality_blur_threshold:
        issues.append("image_too_blurry")
        passed = False
    if liveness_type == "active":
        if asset.kind != "video":
            issues.append("active_liveness_requires_video")
            passed = False
        elif movement_score < settings.active_liveness_motion_threshold:
            issues.append("insufficient_live_motion")
            passed = False
        if challenge_actions:
            missing_actions = [
                action for action in challenge_actions if action not in detected_actions
            ]
            if missing_actions:
                issues.append("challenge_actions_not_completed")
                passed = False

    return {
        "passed": passed,
        "score": round(score, 4),
        "confidence_level": _confidence_label(score),
        "issues": issues,
        "metrics": {
            "asset_kind": asset.kind,
            "frame_count": len(asset.frames),
            "face_presence_ratio": face_presence_ratio,
            "avg_detection_confidence": avg_detection_confidence,
            "movement_score": movement_score,
            "quality_score": quality_metrics["quality_score"],
            "detected_actions": detected_actions,
            "challenge_actions": challenge_actions,
        },
        "challenge_passed": not challenge_actions
        or all(action in detected_actions for action in challenge_actions),
        "model_name": "mediapipe-liveness",
        "model_version": "v1",
    }


@lru_cache
def get_insightface_analyzer():
    settings = get_settings()
    model_root = settings.insightface_root_dir
    model_dir = model_root / "models" / settings.insightface_model_name
    if not model_dir.exists() and not settings.insightface_allow_download:
        raise ProcessingConfigurationError(
            "InsightFace model files are missing under AI_MODEL_ROOT/insightface. Provide local models or enable INSIGHTFACE_ALLOW_DOWNLOAD."
        )

    from insightface.app import FaceAnalysis

    analyzer = FaceAnalysis(name=settings.insightface_model_name, root=str(model_root))
    analyzer.prepare(
        ctx_id=-1,
        det_size=(settings.insightface_detection_size, settings.insightface_detection_size),
    )
    return analyzer


def _pick_largest_face(faces: list[Any]):
    if not faces:
        return None
    return max(
        faces,
        key=lambda face: float((face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1])),
    )


def run_face_compare_pipeline(
    selfie_storage_key: str,
    document_storage_key: str,
    threshold: float,
    *,
    selfie_bucket_name: str | None = None,
    document_bucket_name: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    selfie_asset = load_media_asset(selfie_storage_key, bucket_name=selfie_bucket_name)
    document_asset = load_media_asset(document_storage_key, bucket_name=document_bucket_name)

    selfie_detections = _detect_faces(selfie_asset.primary_frame)
    document_detections = _detect_faces(document_asset.primary_frame)
    issues: list[str] = []
    if len(selfie_detections) != 1:
        issues.append("invalid_selfie_face_count")
    if len(document_detections) < 1:
        issues.append("document_face_not_detected")

    analyzer = get_insightface_analyzer()
    selfie_faces = analyzer.get(selfie_asset.primary_frame)
    document_faces = analyzer.get(document_asset.primary_frame)
    selfie_face = _pick_largest_face(selfie_faces)
    document_face = _pick_largest_face(document_faces)
    if selfie_face is None or document_face is None:
        return {
            "matched": False,
            "match_score": 0.0,
            "threshold_used": threshold,
            "confidence_level": "low",
            "issues": issues or ["embedding_not_generated"],
            "model_name": "insightface",
            "model_version": settings.insightface_model_name,
        }

    similarity = float(
        np.dot(selfie_face.embedding, document_face.embedding)
        / (np.linalg.norm(selfie_face.embedding) * np.linalg.norm(document_face.embedding))
    )
    normalized_score = _clamp((similarity + 1.0) / 2.0)
    matched = normalized_score >= threshold and not issues
    return {
        "matched": matched,
        "match_score": round(normalized_score, 4),
        "threshold_used": threshold,
        "confidence_level": _confidence_label(normalized_score),
        "issues": issues,
        "model_name": "insightface",
        "model_version": settings.insightface_model_name,
    }


@lru_cache
def get_paddle_ocr_engine():
    settings = get_settings()
    model_dirs = (
        settings.paddle_text_detection_model_dir,
        settings.paddle_text_recognition_model_dir,
    )
    if not settings.paddle_allow_download and not all(
        settings.paddle_model_is_complete(path) for path in model_dirs
    ):
        raise ProcessingConfigurationError(
            "PaddleOCR models are not configured under AI_MODEL_ROOT/paddleocr. Provide local models or enable PADDLE_OCR_ALLOW_DOWNLOAD."
        )

    from paddleocr import PaddleOCR
    import yaml

    def local_model_name(path: Path) -> str | None:
        try:
            payload = yaml.safe_load((path / "inference.yml").read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return None
        global_config = payload.get("Global") or {}
        return str(global_config.get("model_name") or "").strip() or None

    kwargs = {
        # IdentityCore performs capture orientation/quality handling separately.
        # Disabling these optional modules keeps real-mode OCR fully local and
        # avoids downloading document-orientation and unwarping models at runtime.
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        # Text-line orientation is optional for the MVP capture flow and its
        # PP-LCNet runtime has been unstable with the current PaddlePaddle CPU
        # executor. Keep OCR deterministic with detection + recognition only.
        "use_textline_orientation": False,
        # PaddlePaddle 3.3.x currently fails on this OCR detection graph in
        # the CPU OneDNN/PIR executor. Use the stable plain CPU executor until
        # the upstream conversion bug is fixed and covered by our inference test.
        "enable_mkldnn": False,
    }
    local_model_arguments = (
        ("text_detection_model_dir", "text_detection_model_name", settings.paddle_text_detection_model_dir),
        ("text_recognition_model_dir", "text_recognition_model_name", settings.paddle_text_recognition_model_dir),
    )
    for directory_argument, name_argument, path in local_model_arguments:
        if settings.paddle_model_is_complete(path):
            kwargs[directory_argument] = str(path)
            model_name = local_model_name(path)
            if model_name:
                kwargs[name_argument] = model_name
    return PaddleOCR(**kwargs)


def _extract_text_lines(ocr_result: Any) -> tuple[list[str], list[float]]:
    if hasattr(ocr_result, "json"):
        payload = ocr_result.json.get("res", ocr_result.json)
    elif isinstance(ocr_result, dict):
        payload = ocr_result
    else:
        payload = dict(ocr_result)

    texts = list(payload.get("rec_texts", []))
    scores = [float(score) for score in payload.get("rec_scores", [])]
    return texts, scores


def _normalize_ocr_fields(texts: list[str], document_type: str, country_code: str) -> dict[str, Any]:
    joined = "\n".join(texts)
    normalized_texts = [text.strip() for text in texts if text.strip()]
    uppercase_candidates = [
        text for text in normalized_texts if re.fullmatch(r"[A-Z][A-Z\s\-]{4,}", text)
    ]
    date_candidates = re.findall(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", joined)
    id_candidates = re.findall(r"\b[A-Z0-9]{6,20}\b", joined)

    return {
        "document_type": document_type,
        "country_code": country_code,
        "full_name": uppercase_candidates[0].title() if uppercase_candidates else "",
        "date_of_birth": date_candidates[0].replace("/", "-") if date_candidates else "",
        "document_number": id_candidates[0] if id_candidates else "",
        "raw_text_lines": normalized_texts,
    }


def run_document_ocr_pipeline(
    storage_key: str,
    document_type: str,
    country_code: str,
    *,
    bucket_name: str | None = None,
) -> dict[str, Any]:
    try:
        asset = load_media_asset(storage_key, bucket_name=bucket_name)
    except MediaAssetNotFoundError:
        return {
            "confidence_score": 0.0,
            "extracted_fields": {},
            "raw_text_lines": [],
            "issues": ["document_media_missing"],
            "requires_manual_review": True,
            "manual_review": {
                "required": True,
                "priority": "high",
                "reason_codes": ["document_media_missing"],
                "review_category": "document_ocr",
            },
            "model_name": "paddleocr",
            "model_version": "PP-OCRv5",
        }
    ocr_engine = get_paddle_ocr_engine()
    rgb_image = cv2.cvtColor(asset.primary_frame, cv2.COLOR_BGR2RGB)
    predictions = ocr_engine.predict(rgb_image)
    prediction = predictions[0] if predictions else {}
    texts, scores = _extract_text_lines(prediction)
    extracted_fields = _normalize_ocr_fields(texts, document_type, country_code)
    confidence_score = _safe_mean(scores)

    return {
        "confidence_score": round(confidence_score, 4),
        "extracted_fields": extracted_fields,
        "raw_text_lines": texts,
        "model_name": "paddleocr",
        "model_version": "PP-OCRv5",
    }


def run_document_classification_pipeline(
    storage_key: str,
    expected_document_type: str,
    country_code: str,
    *,
    bucket_name: str | None = None,
) -> dict[str, Any]:
    try:
        asset = load_media_asset(storage_key, bucket_name=bucket_name)
    except MediaAssetNotFoundError:
        return {
            "classification_status": "unknown",
            "predicted_document_type": "unknown",
            "predicted_country_code": None,
            "expected_document_type": expected_document_type,
            "matched_expected_document_type": None,
            "confidence_score": 0.0,
            "evidence_score": 0.0,
            "classification_margin": 0.0,
            "workflow_action": "continue_with_review",
            "requires_manual_review": True,
            "manual_review": {
                "required": True,
                "priority": "high",
                "reason_codes": ["document_media_missing"],
                "review_category": "document_classification",
            },
            "issues": ["document_media_missing"],
            "ocr": {"average_confidence": 0.0, "line_count": 0, "lines": []},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "score_components": {},
            "classifier": {
                "name": "ocr-evidence-document-classifier",
                "version": "v2",
                "score_type": "uncalibrated_evidence_score",
            },
            "ocr_model": {
                "name": "paddleocr",
                "version": "PP-OCRv5",
            },
            "recommendation": "continue_with_review",
        }
    ocr_engine = get_paddle_ocr_engine()
    rgb_image = cv2.cvtColor(asset.primary_frame, cv2.COLOR_BGR2RGB)
    predictions = ocr_engine.predict(rgb_image)
    prediction = predictions[0] if predictions else {}
    texts, _scores = _extract_text_lines(prediction)
    ocr_lines = build_ocr_lines(texts, _scores)
    result = classify_document(
        ocr_lines,
        expected_document_type=expected_document_type,
        country_code=country_code,
    )
    return {
        **result,
        "country_code": country_code,
        "model_name": result["classifier"]["name"],
        "model_version": result["classifier"]["version"],
    }


def build_mock_face_compare(
    selfie_storage_key: str, document_storage_key: str, threshold: float
) -> dict[str, Any]:
    matched = "mismatch" not in selfie_storage_key and "mismatch" not in document_storage_key
    match_score = 0.96 if matched else 0.42
    return {
        "matched": matched,
        "match_score": match_score,
        "confidence_level": "high" if matched else "medium",
        "threshold_used": threshold,
        "model_name": "mock-face-match",
        "model_version": "v1",
    }


def build_mock_liveness(
    selfie_storage_key: str, liveness_type: str, challenge_actions: list[str] | None = None
) -> dict[str, Any]:
    passed = "spoof" not in selfie_storage_key
    score = 0.94 if passed else 0.23
    challenge_actions = challenge_actions or []
    return {
        "passed": passed,
        "score": score,
        "confidence_level": "high" if passed else "medium",
        "liveness_type": liveness_type,
        "challenge_passed": passed if challenge_actions else True,
        "metrics": {"challenge_actions": challenge_actions, "detected_actions": challenge_actions},
        "model_name": "mock-liveness",
        "model_version": "v1",
    }


def build_mock_document_ocr(
    document_storage_key: str, document_type: str, country_code: str
) -> dict[str, Any]:
    return {
        "confidence_score": 0.91,
        "extracted_fields": {
            "full_name": "Kwame Mensah",
            "date_of_birth": "1998-01-01",
            "document_number": f"hash:{document_type}:{country_code}:{Path(document_storage_key).name}",
            "raw_text_lines": [],
        },
        "model_name": "mock-ocr",
        "model_version": "v1",
    }


def build_mock_document_quality(document_storage_key: str) -> dict[str, Any]:
    issues = ["blur_detected"] if "blur" in document_storage_key else []
    score = 0.42 if issues else 0.88
    return {
        "quality_score": score,
        "issues": issues,
        "model_name": "mock-document-quality",
        "model_version": "v1",
    }


def build_mock_document_classification(
    document_storage_key: str, document_type: str, country_code: str
) -> dict[str, Any]:
    visible_text = document_type.replace("_", " ").upper()
    result = {
        "classification_status": "recognized",
        "predicted_document_type": document_type,
        "predicted_country_code": country_code or None,
        "expected_document_type": document_type,
        "matched_expected_document_type": True,
        "confidence_score": 0.95,
        "evidence_score": 0.95,
        "classification_margin": 1.0,
        "workflow_action": "continue",
        "requires_manual_review": False,
        "manual_review": {
            "required": False,
            "priority": "low",
            "reason_codes": [],
            "review_category": "document_classification",
        },
        "issues": [],
        "ocr": {
            "average_confidence": 0.95,
            "line_count": 1,
            "lines": [
                {
                    "text": visible_text,
                    "normalized_text": visible_text,
                    "confidence": 0.95,
                }
            ],
        },
        "score_components": {
            "required_group_coverage": 1.0,
            "required_evidence_score": 0.95,
            "optional_evidence_score": 0.0,
            "structural_evidence_score": 0.0,
            "average_ocr_confidence": 0.95,
            "negative_evidence_penalty": 0.0,
        },
        "evidence": [
            {
                "type": "ocr",
                "items": [
                    {
                        "expected_phrase": visible_text,
                        "matched_text": visible_text,
                        "similarity_score": 1.0,
                        "ocr_confidence": 0.95,
                        "combined_evidence_score": 0.95,
                        "match_type": "exact",
                        "matched_line_indexes": [0],
                    }
                ],
            }
        ],
        "candidates": [
            {
                "definition_id": f"mock.{document_type}.v1",
                "document_type": document_type,
                "country_code": country_code or None,
                "score": 0.95,
                "required_group_coverage": 1.0,
                "required_evidence_score": 0.95,
                "optional_evidence_score": 0.0,
                "structural_evidence_score": 0.0,
                "average_ocr_confidence": 0.95,
                "negative_evidence_penalty": 0.0,
                "evidence": [],
                "structural_evidence": [],
            }
        ],
        "raw_text_lines": [visible_text],
        "classifier": {
            "name": "mock-document-classifier",
            "version": "v1",
            "score_type": "uncalibrated_evidence_score",
        },
        "ocr_model": {
            "name": "mock-ocr",
            "version": "v1",
        },
        "recommendation": "continue",
    }
    return {
        **result,
        "country_code": country_code,
        "model_name": "mock-document-classifier",
        "model_version": "v1",
    }


def run_with_mode(
    *,
    real_callable,
    mock_callable,
    mock_args: tuple[Any, ...],
    status: str = "completed",
) -> dict[str, Any]:
    settings = get_settings()
    if settings.real_mode_enabled:
        try:
            result = real_callable()
            return {"status": status, "engine": "real", **result}
        except Exception as exc:
            if not settings.mock_fallback_enabled:
                raise ProcessingError(str(exc)) from exc
            result = mock_callable(*mock_args)
            return {
                "status": status,
                "engine": "mock_fallback",
                "fallback_reason": str(exc),
                **result,
            }

    result = mock_callable(*mock_args)
    return {"status": status, "engine": "mock", **result}
