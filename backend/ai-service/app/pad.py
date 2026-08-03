"""Local ONNX presentation-attack detection inference.

The model is intentionally an explicit deployment asset rather than a runtime
download.  The exported model contract is:

* input: float32 NCHW RGB tensor, values in [0, 1]
* output: either one live probability or class logits/probabilities
* the live class is configured by PAD_LIVE_CLASS_INDEX

The service refuses real-mode processing when the model is absent or invalid.
"""

from functools import lru_cache
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort

from app.pipeline import ProcessingConfigurationError
from app.settings import get_settings


@lru_cache
def get_pad_session() -> ort.InferenceSession:
    settings = get_settings()
    model_path = settings.pad_model_path
    if not model_path.is_file():
        raise ProcessingConfigurationError(
            f"PAD model is missing: {model_path}. Provide a verified model asset."
        )
    try:
        return ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
    except Exception as exc:
        raise ProcessingConfigurationError(
            f"PAD model could not be loaded: {model_path}"
        ) from exc


def _softmax(values: np.ndarray) -> np.ndarray:
    shifted = values - np.max(values, axis=-1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / np.sum(exponentials, axis=-1, keepdims=True)


def _crop_face(
    frame: np.ndarray, bbox: dict[str, float] | None, scale: float
) -> np.ndarray:
    if not bbox:
        return frame
    frame_height, frame_width = frame.shape[:2]
    x = bbox["xmin"] * frame_width
    y = bbox["ymin"] * frame_height
    width = bbox["width"] * frame_width
    height = bbox["height"] * frame_height
    center_x = x + width / 2.0
    center_y = y + height / 2.0
    crop_width = width * scale
    crop_height = height * scale
    left = max(0, int(round(center_x - crop_width / 2.0)))
    top = max(0, int(round(center_y - crop_height / 2.0)))
    right = min(frame_width, int(round(center_x + crop_width / 2.0)))
    bottom = min(frame_height, int(round(center_y + crop_height / 2.0)))
    return frame[top:bottom, left:right] if right > left and bottom > top else frame


def run_pad_model(
    frames: list[np.ndarray], face_boxes: list[dict[str, float] | None] | None = None
) -> dict[str, Any]:
    if not frames:
        raise ProcessingConfigurationError("PAD inference requires at least one frame.")

    settings = get_settings()
    session = get_pad_session()
    input_meta = session.get_inputs()[0]
    input_shape = input_meta.shape
    height = int(input_shape[2]) if isinstance(input_shape[2], int) else 80
    width = int(input_shape[3]) if isinstance(input_shape[3], int) else 80
    tensors = []
    for index, frame in enumerate(frames):
        bbox = face_boxes[index] if face_boxes and index < len(face_boxes) else None
        cropped = _crop_face(frame, bbox, settings.pad_crop_scale)
        resized = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_AREA)
        tensors.append(np.transpose(resized.astype(np.float32) / 255.0, (2, 0, 1)))

    raw = session.run(None, {input_meta.name: np.stack(tensors, axis=0)})[0]
    values = np.asarray(raw, dtype=np.float32)
    if values.ndim == 1:
        values = values[:, None]
    values = values.reshape(values.shape[0], -1)
    if values.shape[1] == 1:
        live_scores = values[:, 0]
        if settings.pad_output_kind == "spoof_probability":
            live_scores = 1.0 - live_scores
    else:
        probabilities = (
            _softmax(values)
            if settings.pad_output_kind == "logits"
            else values
        )
        live_scores = probabilities[:, settings.pad_live_class_index]

    score = float(np.clip(np.mean(live_scores), 0.0, 1.0))
    return {
        "pad_score": round(score, 6),
        "pad_frame_scores": [round(float(value), 6) for value in live_scores],
        "model_name": settings.pad_model_name,
        "model_version": settings.pad_model_version,
    }
