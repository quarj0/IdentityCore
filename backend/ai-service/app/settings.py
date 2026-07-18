from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = Field(default="ai-service", alias="AI_SERVICE_NAME")
    service_version: str = Field(default="1.0.0", alias="AI_SERVICE_VERSION")
    service_mode: str = Field(default="real", alias="AI_SERVICE_MODE")
    shared_token: str = Field(default="", alias="AI_SERVICE_SHARED_TOKEN")

    cache_dir: str = Field(default="/tmp/identitycore-ai", alias="AI_SERVICE_CACHE_DIR")
    ai_model_root: Path = Field(default=Path("/opt/identitycore/models"), alias="AI_MODEL_ROOT")
    object_storage_bucket: str = Field(
        default="",
        validation_alias=AliasChoices("OBJECT_STORAGE_BUCKET"),
    )
    object_storage_media_bucket: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OBJECT_STORAGE_MEDIA_BUCKET",
            "R2_MEDIA_BUCKET",
        ),
    )
    object_storage_temp_bucket: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OBJECT_STORAGE_TEMP_BUCKET",
            "R2_TEMP_BUCKET",
        ),
    )
    object_storage_evidence_bucket: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OBJECT_STORAGE_EVIDENCE_BUCKET",
            "R2_EVIDENCE_BUCKET",
        ),
    )
    object_storage_public_bucket: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OBJECT_STORAGE_PUBLIC_BUCKET",
            "R2_PUBLIC_BUCKET",
        ),
    )
    object_storage_endpoint_url: str = Field(
        default="",
        validation_alias=AliasChoices("OBJECT_STORAGE_ENDPOINT_URL", "R2_ENDPOINT_URL"),
    )
    object_storage_access_key_id: str = Field(
        default="",
        validation_alias=AliasChoices("OBJECT_STORAGE_ACCESS_KEY_ID", "R2_ACCESS_KEY_ID"),
    )
    object_storage_secret_access_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OBJECT_STORAGE_SECRET_ACCESS_KEY",
            "R2_SECRET_ACCESS_KEY",
        ),
    )
    object_storage_region: str = Field(
        default="",
        validation_alias=AliasChoices("OBJECT_STORAGE_REGION", "R2_REGION"),
    )
    object_storage_signature_version: str = Field(
        default="s3v4", alias="OBJECT_STORAGE_SIGNATURE_VERSION"
    )
    object_storage_use_path_style: bool = Field(
        default=False, alias="OBJECT_STORAGE_USE_PATH_STYLE"
    )

    mediapipe_min_detection_confidence: float = Field(
        default=0.6, alias="MEDIAPIPE_MIN_DETECTION_CONFIDENCE"
    )
    document_quality_blur_threshold: float = Field(
        default=90.0, alias="DOCUMENT_QUALITY_BLUR_THRESHOLD"
    )
    document_quality_glare_threshold: float = Field(
        default=0.08, alias="DOCUMENT_QUALITY_GLARE_THRESHOLD"
    )
    document_quality_dark_threshold: float = Field(
        default=55.0, alias="DOCUMENT_QUALITY_DARK_THRESHOLD"
    )
    document_quality_bright_threshold: float = Field(
        default=225.0, alias="DOCUMENT_QUALITY_BRIGHT_THRESHOLD"
    )
    liveness_min_score: float = Field(default=0.65, alias="LIVENESS_MIN_SCORE")
    active_liveness_motion_threshold: float = Field(
        default=0.02, alias="ACTIVE_LIVENESS_MOTION_THRESHOLD"
    )
    video_frame_sample_limit: int = Field(default=12, alias="VIDEO_FRAME_SAMPLE_LIMIT")

    document_classification_minimum_candidate_evidence: float = Field(
        default=0.55,
        alias="DOCUMENT_CLASSIFICATION_MINIMUM_CANDIDATE_EVIDENCE",
    )
    document_classification_minimum_required_group_coverage: float = Field(
        default=0.5,
        alias="DOCUMENT_CLASSIFICATION_MINIMUM_REQUIRED_GROUP_COVERAGE",
    )
    document_classification_minimum_classification_margin: float = Field(
        default=0.08,
        alias="DOCUMENT_CLASSIFICATION_MINIMUM_CLASSIFICATION_MARGIN",
    )
    document_classification_minimum_average_ocr_confidence: float = Field(
        default=0.35,
        alias="DOCUMENT_CLASSIFICATION_MINIMUM_AVERAGE_OCR_CONFIDENCE",
    )
    document_classification_required_evidence_weight: float = Field(
        default=0.55,
        alias="DOCUMENT_CLASSIFICATION_REQUIRED_EVIDENCE_WEIGHT",
    )
    document_classification_optional_evidence_weight: float = Field(
        default=0.10,
        alias="DOCUMENT_CLASSIFICATION_OPTIONAL_EVIDENCE_WEIGHT",
    )
    document_classification_structural_evidence_weight: float = Field(
        default=0.20,
        alias="DOCUMENT_CLASSIFICATION_STRUCTURAL_EVIDENCE_WEIGHT",
    )
    document_classification_ocr_quality_weight: float = Field(
        default=0.10,
        alias="DOCUMENT_CLASSIFICATION_OCR_QUALITY_WEIGHT",
    )
    document_classification_negative_evidence_weight: float = Field(
        default=0.20,
        alias="DOCUMENT_CLASSIFICATION_NEGATIVE_EVIDENCE_WEIGHT",
    )
    document_classification_enabled_country_codes_raw: str = Field(
        default="",
        alias="DOCUMENT_CLASSIFICATION_ENABLED_COUNTRY_CODES",
    )

    insightface_model_name: str = Field(
        default="buffalo_l", alias="INSIGHTFACE_MODEL_NAME"
    )
    insightface_allow_download: bool = Field(
        default=False, alias="INSIGHTFACE_ALLOW_DOWNLOAD"
    )
    insightface_detection_size: int = Field(
        default=640, alias="INSIGHTFACE_DETECTION_SIZE"
    )

    paddle_pdx_cache_home: str = Field(default="/tmp/identitycore-ai/paddlex")
    paddle_home: str = Field(default="/tmp/identitycore-ai/paddle")
    matplotlib_config_dir: str = Field(
        default="/tmp/identitycore-ai/matplotlib"
    )
    xdg_cache_home: str = Field(default="/tmp/identitycore-ai/.cache")
    paddle_disable_model_source_check: bool = Field(
        default=True, alias="PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"
    )
    paddle_allow_download: bool = Field(
        default=False, alias="PADDLE_OCR_ALLOW_DOWNLOAD"
    )

    @field_validator("service_mode", mode="before")
    @classmethod
    def normalize_service_mode(cls, value: str) -> str:
        normalized = str(value or "real").strip().lower()
        if normalized == "local":
            return "mock"
        if normalized not in {"mock", "hybrid", "real"}:
            raise ValueError("AI_SERVICE_MODE must be one of: mock, hybrid, real.")
        return normalized

    @property
    def cache_path(self) -> Path:
        return Path(self.cache_dir)

    @property
    def insightface_root_dir(self) -> Path:
        return self.ai_model_root / "insightface"

    @property
    def paddle_root_dir(self) -> Path:
        return self.ai_model_root / "paddleocr"

    @property
    def mediapipe_root_dir(self) -> Path:
        return self.ai_model_root / "mediapipe"

    @property
    def onnx_root_dir(self) -> Path:
        return self.ai_model_root / "onnx"

    @property
    def paddle_text_detection_model_dir(self) -> Path:
        return self.paddle_root_dir / "det"

    @property
    def paddle_text_recognition_model_dir(self) -> Path:
        return self.paddle_root_dir / "rec"

    @property
    def paddle_textline_orientation_model_dir(self) -> Path:
        return self.paddle_root_dir / "cls"

    @staticmethod
    def paddle_model_is_complete(path: Path) -> bool:
        return (path / "inference.yml").is_file() and any(
            (path / filename).is_file()
            for filename in ("inference.json", "inference.pdmodel", "model.pdmodel")
        )

    @property
    def insightface_model_dir(self) -> Path:
        return self.insightface_root_dir / "models" / self.insightface_model_name

    @property
    def document_classification_policy(self):
        from app.document_classification.models import DocumentClassificationPolicy

        return DocumentClassificationPolicy(
            minimum_candidate_evidence=self.document_classification_minimum_candidate_evidence,
            minimum_required_group_coverage=self.document_classification_minimum_required_group_coverage,
            minimum_classification_margin=self.document_classification_minimum_classification_margin,
            minimum_average_ocr_confidence=self.document_classification_minimum_average_ocr_confidence,
        )

    @property
    def document_classification_scoring_config(self):
        from app.document_classification.models import ClassificationScoringConfig

        return ClassificationScoringConfig(
            required_evidence_weight=self.document_classification_required_evidence_weight,
            optional_evidence_weight=self.document_classification_optional_evidence_weight,
            structural_evidence_weight=self.document_classification_structural_evidence_weight,
            ocr_quality_weight=self.document_classification_ocr_quality_weight,
            negative_evidence_weight=self.document_classification_negative_evidence_weight,
        )

    @property
    def document_classification_enabled_country_codes(self) -> tuple[str, ...]:
        raw = self.document_classification_enabled_country_codes_raw.strip()
        if not raw:
            return ()
        return tuple(
            country_code.strip().upper()
            for country_code in raw.split(",")
            if country_code.strip()
        )

    def real_inference_missing_requirements(self) -> list[str]:
        missing: list[str] = []

        if not (self.object_storage_media_bucket or self.object_storage_bucket):
            missing.append("object_storage.media_bucket")
        if not self.object_storage_endpoint_url:
            missing.append("object_storage.endpoint_url")
        if not self.object_storage_access_key_id:
            missing.append("object_storage.access_key_id")
        if not self.object_storage_secret_access_key:
            missing.append("object_storage.secret_access_key")

        if not self.insightface_allow_download and not self.insightface_model_dir.exists():
            missing.append(f"models.insightface:{self.insightface_model_dir}")

        if not self.paddle_allow_download:
            for label, path in (
                ("models.paddleocr.det", self.paddle_text_detection_model_dir),
                ("models.paddleocr.rec", self.paddle_text_recognition_model_dir),
            ):
                if not self.paddle_model_is_complete(path):
                    missing.append(f"{label}:{path}")

        return missing

    @property
    def real_mode_enabled(self) -> bool:
        return self.service_mode in {"real", "hybrid"}

    @property
    def mock_fallback_enabled(self) -> bool:
        return self.service_mode in {"mock", "hybrid"}

    @property
    def real_inference_ready(self) -> bool:
        return not self.real_inference_missing_requirements()


@lru_cache
def get_settings() -> Settings:
    return Settings()
