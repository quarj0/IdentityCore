import os
from pathlib import Path

from app.settings import Settings


def configure_runtime_environment(settings: Settings) -> None:
    os.environ.setdefault("MPLCONFIGDIR", settings.matplotlib_config_dir)
    os.environ.setdefault("XDG_CACHE_HOME", settings.xdg_cache_home)
    os.environ.setdefault("PADDLE_HOME", settings.paddle_home)
    os.environ.setdefault("PADDLE_PDX_CACHE_HOME", settings.paddle_pdx_cache_home)
    os.environ.setdefault("INSIGHTFACE_HOME", str(settings.insightface_root_dir))
    if settings.paddle_disable_model_source_check:
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

    for path in (
        settings.cache_dir,
        settings.matplotlib_config_dir,
        settings.xdg_cache_home,
        settings.paddle_home,
        settings.paddle_pdx_cache_home,
    ):
        Path(path).mkdir(parents=True, exist_ok=True)
