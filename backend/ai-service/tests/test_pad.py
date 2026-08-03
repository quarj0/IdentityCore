from types import SimpleNamespace

import numpy as np

from app import pad


class FakeSession:
    def get_inputs(self):
        return [SimpleNamespace(name="images", shape=["batch", 3, 80, 80])]

    def run(self, _outputs, _inputs):
        return [np.array([[2.0, 0.0, -2.0]], dtype=np.float32)]


def test_pad_model_applies_live_class_softmax(monkeypatch):
    monkeypatch.setattr(pad, "get_pad_session", lambda: FakeSession())
    monkeypatch.setattr(
        pad,
        "get_settings",
        lambda: SimpleNamespace(
            pad_output_kind="logits",
            pad_live_class_index=0,
            pad_model_name="MiniFASNetV2",
            pad_model_version="2.7_80x80",
            pad_crop_scale=2.7,
        ),
    )

    result = pad.run_pad_model(
        [np.zeros((120, 160, 3), dtype=np.uint8)],
        [{"xmin": 0.25, "ymin": 0.2, "width": 0.5, "height": 0.6}],
    )

    assert result["model_name"] == "MiniFASNetV2"
    assert 0.8 < result["pad_score"] < 0.9
