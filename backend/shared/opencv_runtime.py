"""Fail builds if overlapping OpenCV distributions share the cv2 namespace."""

from importlib.metadata import distributions


def verify_opencv_runtime():
    installed = {
        distribution.metadata["Name"].lower().replace("_", "-")
        for distribution in distributions()
        if distribution.metadata["Name"].lower().replace("_", "-").startswith("opencv-")
    }
    if installed != {"opencv-contrib-python-headless"}:
        raise RuntimeError(f"Conflicting OpenCV distributions: {sorted(installed)}")
    import cv2

    if cv2.__version__ != "5.0.0":
        raise RuntimeError(f"Unexpected OpenCV runtime: {cv2.__version__}")


if __name__ == "__main__":
    verify_opencv_runtime()
