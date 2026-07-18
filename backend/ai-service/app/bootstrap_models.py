import hashlib
import json
import shutil
from pathlib import Path
import yaml

from app.pipeline import get_insightface_analyzer, get_paddle_ocr_engine
from app.settings import get_settings


PADDLE_MODEL_CANDIDATES = {
    "det": ("PP-OCRv5_server_det", "PP-OCRv5_mobile_det"),
    "rec": ("en_PP-OCRv5_mobile_rec", "PP-OCRv5_server_rec", "PP-OCRv5_mobile_rec"),
}


def _persist_downloaded_paddle_models(settings) -> None:
    official_roots = (
        Path(settings.paddle_pdx_cache_home) / "official_models",
        Path.home() / ".paddlex" / "official_models",
    )
    targets = {
        "det": settings.paddle_text_detection_model_dir,
        "rec": settings.paddle_text_recognition_model_dir,
    }
    for kind, target in targets.items():
        if settings.paddle_model_is_complete(target):
            continue
        source = next(
            (root / name for root in official_roots for name in PADDLE_MODEL_CANDIDATES[kind]
             if settings.paddle_model_is_complete(root / name)),
            None,
        )
        if source is None:
            raise RuntimeError(f"Downloaded PaddleOCR {kind} model was not found under: {', '.join(map(str, official_roots))}.")
        shutil.copytree(source, target, dirs_exist_ok=True)


def _model_name(path: Path) -> str:
    payload = yaml.safe_load((path / "inference.yml").read_text(encoding="utf-8")) or {}
    return str((payload.get("Global") or {}).get("model_name") or path.name)


def main() -> None:
    settings = get_settings()
    settings.ai_model_root.mkdir(parents=True, exist_ok=True)
    paddle_directories = (
        settings.paddle_text_detection_model_dir,
        settings.paddle_text_recognition_model_dir,
    )
    for directory in paddle_directories:
        directory.mkdir(parents=True, exist_ok=True)

    get_insightface_analyzer()
    get_paddle_ocr_engine()

    _persist_downloaded_paddle_models(settings)

    incomplete_directories = [str(path) for path in paddle_directories if not settings.paddle_model_is_complete(path)]
    if incomplete_directories:
        raise RuntimeError(
            "PaddleOCR bootstrap did not populate complete models: " + ", ".join(incomplete_directories)
        )
    files = []
    for path in sorted(settings.ai_model_root.rglob("*")):
        if path.is_file():
            files.append({
                "path": str(path.relative_to(settings.ai_model_root)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            })
    manifest_path = settings.ai_model_root / "manifest.json"
    manifest_path.write_text(json.dumps({
        "insightface_model": settings.insightface_model_name,
        "paddle_models": {
            "detection": _model_name(settings.paddle_text_detection_model_dir),
            "recognition": _model_name(settings.paddle_text_recognition_model_dir),
        },
        "files": files,
    }, indent=2), encoding="utf-8")
    print(f"Model bootstrap complete: {len(files)} artifacts recorded in {manifest_path}")


if __name__ == "__main__":
    main()
