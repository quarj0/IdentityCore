from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = Field(default="ai-service", alias="AI_SERVICE_NAME")
    service_version: str = Field(default="1.0.0", alias="AI_SERVICE_VERSION")
    service_mode: str = Field(default="mock", alias="AI_SERVICE_MODE")
    shared_token: str = Field(default="", alias="AI_SERVICE_SHARED_TOKEN")

    cache_dir: str = Field(default="/tmp/identitycore-ai", alias="AI_SERVICE_CACHE_DIR")
    object_storage_bucket: str = Field(default="", alias="OBJECT_STORAGE_BUCKET")
    object_storage_endpoint_url: str = Field(
        default="", alias="OBJECT_STORAGE_ENDPOINT_URL"
    )
    object_storage_access_key_id: str = Field(
        default="", alias="OBJECT_STORAGE_ACCESS_KEY_ID"
    )
    object_storage_secret_access_key: str = Field(
        default="", alias="OBJECT_STORAGE_SECRET_ACCESS_KEY"
    )
    object_storage_region: str = Field(default="", alias="OBJECT_STORAGE_REGION")
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

    insightface_model_name: str = Field(
        default="buffalo_l", alias="INSIGHTFACE_MODEL_NAME"
    )
    insightface_root_dir: str = Field(
        default="/tmp/identitycore-ai/insightface", alias="INSIGHTFACE_ROOT_DIR"
    )
    insightface_allow_download: bool = Field(
        default=False, alias="INSIGHTFACE_ALLOW_DOWNLOAD"
    )
    insightface_detection_size: int = Field(
        default=640, alias="INSIGHTFACE_DETECTION_SIZE"
    )

    paddle_pdx_cache_home: str = Field(
        default="/tmp/identitycore-ai/paddlex", alias="PADDLE_PDX_CACHE_HOME"
    )
    paddle_home: str = Field(
        default="/tmp/identitycore-ai/paddle", alias="PADDLE_HOME"
    )
    matplotlib_config_dir: str = Field(
        default="/tmp/identitycore-ai/matplotlib", alias="MPLCONFIGDIR"
    )
    xdg_cache_home: str = Field(default="/tmp/identitycore-ai/.cache", alias="XDG_CACHE_HOME")
    paddle_disable_model_source_check: bool = Field(
        default=True, alias="PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"
    )
    paddle_lang: str = Field(default="en", alias="PADDLE_OCR_LANG")
    paddle_ocr_version: str = Field(default="PP-OCRv5", alias="PADDLE_OCR_VERSION")
    paddle_allow_download: bool = Field(default=False, alias="PADDLE_OCR_ALLOW_DOWNLOAD")
    paddle_text_detection_model_dir: str = Field(
        default="", alias="PADDLE_OCR_TEXT_DETECTION_MODEL_DIR"
    )
    paddle_text_recognition_model_dir: str = Field(
        default="", alias="PADDLE_OCR_TEXT_RECOGNITION_MODEL_DIR"
    )
    paddle_textline_orientation_model_dir: str = Field(
        default="", alias="PADDLE_OCR_TEXTLINE_ORIENTATION_MODEL_DIR"
    )

    @property
    def cache_path(self) -> Path:
        return Path(self.cache_dir)

    @property
    def real_mode_enabled(self) -> bool:
        return self.service_mode in {"real", "hybrid"}

    @property
    def mock_fallback_enabled(self) -> bool:
        return self.service_mode in {"mock", "hybrid"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
