from types import SimpleNamespace

from app import bootstrap_models


def test_bootstrap_creates_paddle_directories_before_initialization(
    monkeypatch, tmp_path
):
    settings = SimpleNamespace(
        ai_model_root=tmp_path,
        paddle_text_detection_model_dir=tmp_path / "paddleocr" / "det",
        paddle_text_recognition_model_dir=tmp_path / "paddleocr" / "rec",
        insightface_model_name="buffalo_l",
        paddle_pdx_cache_home=str(tmp_path / "paddlex"),
    )
    settings.paddle_model_is_complete = lambda path: (
        (path / "inference.yml").is_file() and (path / "inference.json").is_file()
    )

    def initialize_paddle():
        for directory in (
            settings.paddle_text_detection_model_dir,
            settings.paddle_text_recognition_model_dir,
        ):
            assert directory.is_dir()
            (directory / "inference.yml").write_text("model: test")
            (directory / "inference.json").write_text("{}")

    monkeypatch.setattr(bootstrap_models, "get_settings", lambda: settings)
    monkeypatch.setattr(bootstrap_models, "get_insightface_analyzer", lambda: None)
    monkeypatch.setattr(bootstrap_models, "get_paddle_ocr_engine", initialize_paddle)

    bootstrap_models.main()

    assert (tmp_path / "manifest.json").exists()
