from io import BytesIO

from PIL import Image, UnidentifiedImageError


IMAGE_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def inspect_upload_content(*, content: bytes, declared_mime_type: str) -> tuple[bool, str]:
    """Fail closed when uploaded bytes do not match the declared media type."""
    if b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*" in content:
        return False, "malware_signature_detected"

    if declared_mime_type.startswith("image/"):
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()
                detected_mime_type = IMAGE_FORMATS.get(image.format)
        except (UnidentifiedImageError, OSError):
            return False, "image_content_unrecognized"
        if detected_mime_type != declared_mime_type:
            return False, "declared_type_does_not_match_content"
        return True, ""

    if declared_mime_type in {"video/mp4", "video/quicktime"}:
        if len(content) < 12 or content[4:8] != b"ftyp":
            return False, "video_container_unrecognized"
        return True, ""

    if declared_mime_type == "video/webm":
        if not content.startswith(b"\x1a\x45\xdf\xa3"):
            return False, "video_container_unrecognized"
        return True, ""

    return False, "unsupported_content_type"
