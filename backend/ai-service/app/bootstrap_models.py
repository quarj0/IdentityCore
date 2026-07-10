import hashlib
import json

from app.pipeline import get_insightface_analyzer, get_paddle_ocr_engine
from app.settings import get_settings


def main() -> None:
    settings = get_settings()
    settings.ai_model_root.mkdir(parents=True, exist_ok=True)
    paddle_directories = (
        settings.paddle_text_detection_model_dir,
        settings.paddle_text_recognition_model_dir,
        settings.paddle_textline_orientation_model_dir,
    )
    for directory in paddle_directories:
        directory.mkdir(parents=True, exist_ok=True)

    get_insightface_analyzer()
    get_paddle_ocr_engine()

    empty_directories = [str(path) for path in paddle_directories if not any(path.iterdir())]
    if empty_directories:
        raise RuntimeError(
            "PaddleOCR bootstrap did not populate: " + ", ".join(empty_directories)
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
        "paddle_ocr_version": settings.paddle_ocr_version,
        "files": files,
    }, indent=2), encoding="utf-8")
    print(f"Model bootstrap complete: {len(files)} artifacts recorded in {manifest_path}")


if __name__ == "__main__":
    main()
