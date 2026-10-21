"""Local YuNet/SFace inference using explicitly licensed OpenCV Zoo weights."""

from dataclasses import dataclass
from functools import lru_cache
from threading import RLock

import cv2
import numpy as np

from app.settings import get_settings


@dataclass
class FaceEmbedding:
    bbox: np.ndarray
    embedding: np.ndarray


class OpenCVFaceAnalyzer:
    def __init__(self, settings):
        self._lock = RLock()
        self.detector = cv2.FaceDetectorYN.create(
            str(settings.opencv_face_detection_path),
            "",
            (320, 320),
            score_threshold=0.9,
            nms_threshold=0.3,
            top_k=5000,
        )
        self.recognizer = cv2.FaceRecognizerSF.create(
            str(settings.opencv_face_recognition_path), ""
        )

    def get(self, image):
        if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                "Face inference requires a decoded three-channel uint8 image."
            )
        # Bound detector memory/latency for high-resolution identity captures.
        # Alignment still uses the original pixels and rescaled landmarks.
        scale = min(1.0, 640.0 / max(image.shape[:2]))
        detector_image = image
        if scale < 1.0:
            detector_image = cv2.resize(
                image,
                (
                    max(1, round(image.shape[1] * scale)),
                    max(1, round(image.shape[0] * scale)),
                ),
                interpolation=cv2.INTER_AREA,
            )
        with self._lock:
            self.detector.setInputSize(
                (detector_image.shape[1], detector_image.shape[0])
            )
            _, detections = self.detector.detect(detector_image)
            if detections is None:
                return []
            if len(detections) > 16:
                raise ValueError("Too many faces in capture.")
            faces = []
            for detection in detections:
                detection = detection.copy()
                detection[:14] /= scale
                aligned = self.recognizer.alignCrop(image, detection)
                embedding = self.recognizer.feature(aligned).reshape(-1).copy()
                if not np.isfinite(embedding).all() or np.linalg.norm(embedding) <= 0:
                    raise ValueError("Face model produced an invalid embedding.")
                x, y, width, height = map(float, detection[:4])
                faces.append(
                    FaceEmbedding(np.array([x, y, x + width, y + height]), embedding)
                )
            return faces


@lru_cache
def get_opencv_face_analyzer():
    return OpenCVFaceAnalyzer(get_settings())
