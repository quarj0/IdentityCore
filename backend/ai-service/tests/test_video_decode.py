from pathlib import Path

import numpy as np
import pytest

from app.pipeline import _sample_video_frames


@pytest.mark.parametrize(
    "extension,mime", [("mp4", "video/mp4"), ("webm", "video/webm")]
)
def test_browser_video_formats_decode_without_external_cli(extension, mime):
    path = Path(__file__).parent / "fixtures" / "video" / ("solid-blue." + extension)
    frames = _sample_video_frames(path.read_bytes(), path.name, 2, mime)
    assert len(frames) == 2
    for frame in frames:
        assert frame.shape == (64, 64, 3) and frame.dtype == np.uint8
        channels = frame.mean(axis=(0, 1))
        assert channels[0] > 200 and channels[1] < 25 and channels[2] < 25
