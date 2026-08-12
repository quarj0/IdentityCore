"""Local ONNX presentation-attack detection inference.

The model is intentionally an explicit deployment asset rather than a runtime
download.  The exported model contract is:

* input: float32 NCHW RGB tensor, values in [0, 1]
* output: either one live probability or class logits/probabilities
* the live class is configured by PAD_LIVE_CLASS_INDEX

The service refuses real-mode processing when the model is absent or invalid.
"""

from functools import lru_cache
from pathlib import Path
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
        session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
    except Exception as exc:
        raise ProcessingConfigurationError(
            f"PAD model could not be loaded: {model_path}"
        ) from exc
    validate_pad_session_contract(session, get_settings().pad_live_class_index)
    return session


def validate_pad_session_contract(
    session: ort.InferenceSession, live_class_index: int
) -> None:
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if len(inputs) != 1 or not outputs:
        raise ProcessingConfigurationError(
            "PAD model must expose exactly one input and at least one output."
        )
    input_shape = inputs[0].shape
    if len(input_shape) != 4 or (
        isinstance(input_shape[1], int) and input_shape[1] != 3
    ):
        raise ProcessingConfigurationError(
            "PAD model input must be a four-dimensional NCHW RGB tensor."
        )
    for dimension in input_shape[2:]:
        if isinstance(dimension, int) and dimension <= 0:
            raise ProcessingConfigurationError(
                "PAD model spatial dimensions must be positive."
            )
    output_shape = outputs[0].shape
    if output_shape and isinstance(output_shape[-1], int):
        class_count = output_shape[-1]
        if class_count > 1 and not 0 <= live_class_index < class_count:
            raise ProcessingConfigurationError(
                "PAD live-class index is outside the model output contract."
            )


def validate_pad_model_contract(model_path: Path, live_class_index: int) -> None:
    try:
        session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        validate_pad_session_contract(session, live_class_index)
    except ProcessingConfigurationError:
        raise
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
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensors.append(np.transpose(rgb.astype(np.float32) / 255.0, (2, 0, 1)))

    declared_batch = input_shape[0]
    batch_size = declared_batch if isinstance(declared_batch, int) else len(tensors)
    if batch_size <= 0:
        raise ProcessingConfigurationError("PAD model batch dimension is invalid.")
    output_batches = []
    for start in range(0, len(tensors), batch_size):
        chunk = tensors[start : start + batch_size]
        actual_size = len(chunk)
        if actual_size < batch_size:
            chunk.extend([chunk[-1]] * (batch_size - actual_size))
        raw = session.run(None, {input_meta.name: np.stack(chunk, axis=0)})[0]
        output_batches.append(np.asarray(raw, dtype=np.float32)[:actual_size])
    values = np.concatenate(output_batches, axis=0)
    if values.ndim == 1:
        values = values[:, None]
    values = values.reshape(values.shape[0], -1)
    if values.shape[1] == 1:
        live_scores = values[:, 0]
        if settings.pad_output_kind == "spoof_probability":
            live_scores = 1.0 - live_scores
    else:
        probabilities = (
            _softmax(values) if settings.pad_output_kind == "logits" else values
        )
        live_scores = probabilities[:, settings.pad_live_class_index]

    score = float(np.clip(np.mean(live_scores), 0.0, 1.0))
    return {
        "pad_score": round(score, 6),
        "pad_frame_scores": [round(float(value), 6) for value in live_scores],
        "model_name": settings.pad_model_name,
        "model_version": settings.pad_model_version,
    }
