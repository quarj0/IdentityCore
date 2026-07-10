from types import SimpleNamespace

from app import bootstrap_models


def test_bootstrap_creates_paddle_directories_before_initialization(
    monkeypatch, tmp_path
):
    settings = SimpleNamespace(
        ai_model_root=tmp_path,
        paddle_text_detection_model_dir=tmp_path / "paddleocr" / "det",
        paddle_text_recognition_model_dir=tmp_path / "paddleocr" / "rec",
        paddle_textline_orientation_model_dir=tmp_path / "paddleocr" / "cls",
        insightface_model_name="buffalo_l",
        paddle_ocr_version="PP-OCRv5",
    )

    def initialize_paddle():
        for directory in (
            settings.paddle_text_detection_model_dir,
            settings.paddle_text_recognition_model_dir,
            settings.paddle_textline_orientation_model_dir,
        ):
            assert directory.is_dir()
            (directory / "model.pdmodel").write_bytes(b"model")

    monkeypatch.setattr(bootstrap_models, "get_settings", lambda: settings)
    monkeypatch.setattr(bootstrap_models, "get_insightface_analyzer", lambda: None)
    monkeypatch.setattr(bootstrap_models, "get_paddle_ocr_engine", initialize_paddle)

    bootstrap_models.main()

    assert (tmp_path / "manifest.json").exists()
