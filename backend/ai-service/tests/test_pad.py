from types import SimpleNamespace

import numpy as np
import pytest

from app import pad
from app.pipeline import ProcessingConfigurationError
from app.settings import Settings


class FakeSession:
    def __init__(self, batch="batch"):
        self.batch = batch
        self.inputs = []

    def get_inputs(self):
        return [
            SimpleNamespace(
                name="images", shape=[self.batch, 3, 80, 80], type="tensor(float)"
            )
        ]

    def get_outputs(self):
        return [SimpleNamespace(name="scores", shape=[self.batch, 3])]

    def run(self, _outputs, inputs):
        tensor = inputs["images"]
        self.inputs.append(tensor)
        rows = tensor.shape[0]
        return [np.tile([[2.0, 0.0, -2.0]], (rows, 1)).astype(np.float32)]


def test_pad_live_class_defaults_to_genuine_class():
    assert Settings().pad_live_class_index == 1


def test_pad_contract_rejects_non_float_input():
    session = FakeSession()
    session.get_inputs = lambda: [
        SimpleNamespace(name="images", shape=[1, 3, 80, 80], type="tensor(uint8)")
    ]

    with pytest.raises(ProcessingConfigurationError, match="float32"):
        pad.validate_pad_session_contract(session, live_class_index=1)


def test_pad_contract_rejects_rank_one_output():
    session = FakeSession(batch=1)
    session.get_outputs = lambda: [SimpleNamespace(name="scores", shape=[3])]

    with pytest.raises(ProcessingConfigurationError, match="batch and class"):
        pad.validate_pad_session_contract(session, live_class_index=1)


def test_pad_model_applies_live_class_softmax(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(pad, "get_pad_session", lambda: session)
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


def test_pad_model_converts_bgr_to_rgb(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(pad, "get_pad_session", lambda: session)
    monkeypatch.setattr(
        pad,
        "get_settings",
        lambda: SimpleNamespace(
            pad_output_kind="logits",
            pad_live_class_index=0,
            pad_model_name="MiniFASNetV2",
            pad_model_version="2.7_80x80",
            pad_crop_scale=1.0,
        ),
    )
    blue_bgr_frame = np.zeros((80, 80, 3), dtype=np.uint8)
    blue_bgr_frame[:, :, 0] = 255

    pad.run_pad_model([blue_bgr_frame])

    tensor = session.inputs[0]
    assert np.all(tensor[0, 0] == 0)
    assert np.all(tensor[0, 2] == 1)


def test_pad_model_runs_fixed_batch_one_frame_at_a_time(monkeypatch):
    session = FakeSession(batch=1)
    monkeypatch.setattr(pad, "get_pad_session", lambda: session)
    monkeypatch.setattr(
        pad,
        "get_settings",
        lambda: SimpleNamespace(
            pad_output_kind="logits",
            pad_live_class_index=0,
            pad_model_name="MiniFASNetV2",
            pad_model_version="2.7_80x80",
            pad_crop_scale=1.0,
        ),
    )

    result = pad.run_pad_model(
        [np.zeros((80, 80, 3), dtype=np.uint8) for _ in range(3)]
    )

    assert [batch.shape[0] for batch in session.inputs] == [1, 1, 1]
    assert len(result["pad_frame_scores"]) == 3
