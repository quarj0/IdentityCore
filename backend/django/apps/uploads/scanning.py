from io import BytesIO

from PIL import Image, UnidentifiedImageError


IMAGE_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}

MP4_BRANDS = {
    b"avc1",
    b"dash",
    b"iso2",
    b"iso3",
    b"iso4",
    b"iso5",
    b"iso6",
    b"iso7",
    b"iso8",
    b"iso9",
    b"isom",
    b"M4V ",
    b"mp41",
    b"mp42",
}
QUICKTIME_BRAND = b"qt  "
WEBM_VIDEO_CODECS = {b"V_AV1", b"V_VP8", b"V_VP9"}
ISO_VIDEO_SAMPLE_CONFIGS = {
    b"av01": b"av1C",
    b"avc1": b"avcC",
    b"avc3": b"avcC",
    b"hev1": b"hvcC",
    b"hvc1": b"hvcC",
    b"vp08": b"vpcC",
    b"vp09": b"vpcC",
}


def _iso_boxes(
    content: bytes, *, start: int = 0, end: int | None = None
) -> list[tuple[bytes, int, int]] | None:
    """Return structurally bounded ISO-BMFF boxes, or None for malformed bytes."""
    boundary = len(content) if end is None else end
    offset = start
    boxes = []
    while offset < boundary:
        if boundary - offset < 8:
            return None
        box_size = int.from_bytes(content[offset : offset + 4], "big")
        box_type = content[offset + 4 : offset + 8]
        header_size = 8
        if box_size == 1:
            if boundary - offset < 16:
                return None
            box_size = int.from_bytes(content[offset + 8 : offset + 16], "big")
            header_size = 16
        elif box_size == 0:
            box_size = boundary - offset
        if box_size < header_size or offset + box_size > boundary:
            return None
        payload_start = offset + header_size
        payload_end = offset + box_size
        boxes.append((box_type, payload_start, payload_end))
        offset = payload_end
    return boxes if offset == boundary else None


def _valid_full_box(
    content: bytes,
    start: int,
    end: int,
    *,
    version_zero_size: int,
    version_one_size: int | None = None,
) -> bool:
    if start >= end:
        return False
    expected_size = version_zero_size
    if content[start] == 1 and version_one_size is not None:
        expected_size = version_one_size
    elif content[start] != 0:
        return False
    return end - start >= expected_size


def _iso_stbl_has_video_sample_entry(content: bytes, start: int, end: int) -> bool:
    boxes = _iso_boxes(content, start=start, end=end)
    if not boxes:
        return False
    required_tables = {b"stsd", b"stsc", b"stsz", b"stts"}
    box_types = {box_type for box_type, _, _ in boxes}
    if not required_tables.issubset(box_types) or not box_types.intersection(
        {b"co64", b"stco"}
    ):
        return False
    for required_type in (b"stts", b"stsc"):
        _, table_start, table_end = next(
            box for box in boxes if box[0] == required_type
        )
        if (
            table_end - table_start < 8
            or content[table_start] != 0
            or int.from_bytes(content[table_start + 4 : table_start + 8], "big") == 0
        ):
            return False
    _, size_start, size_end = next(box for box in boxes if box[0] == b"stsz")
    if (
        size_end - size_start < 12
        or content[size_start] != 0
        or int.from_bytes(content[size_start + 8 : size_start + 12], "big") == 0
    ):
        return False
    chunk_box = next(box for box in boxes if box[0] in {b"co64", b"stco"})
    _, chunk_start, chunk_end = chunk_box
    if (
        chunk_end - chunk_start < 8
        or content[chunk_start] != 0
        or int.from_bytes(content[chunk_start + 4 : chunk_start + 8], "big") == 0
        or int.from_bytes(
            content[chunk_start + 8 : chunk_start + (16 if chunk_box[0] == b"co64" else 12)],
            "big",
        )
        == 0
    ):
        return False
    stsd = next(box for box in boxes if box[0] == b"stsd")
    _, stsd_start, stsd_end = stsd
    if stsd_end - stsd_start < 8 or content[stsd_start] != 0:
        return False
    entry_count = int.from_bytes(content[stsd_start + 4 : stsd_start + 8], "big")
    entries = _iso_boxes(content, start=stsd_start + 8, end=stsd_end)
    if not entries or entry_count != len(entries):
        return False
    for sample_type, sample_start, sample_end in entries:
        config_type = ISO_VIDEO_SAMPLE_CONFIGS.get(sample_type)
        if config_type is None or sample_end - sample_start < 78:
            continue
        width = int.from_bytes(content[sample_start + 24 : sample_start + 26], "big")
        height = int.from_bytes(content[sample_start + 26 : sample_start + 28], "big")
        codec_boxes = _iso_boxes(content, start=sample_start + 78, end=sample_end)
        if (
            width > 0
            and height > 0
            and codec_boxes
            and any(
                box_type == config_type and payload_end > payload_start
                for box_type, payload_start, payload_end in codec_boxes
            )
        ):
            return True
    return False


def _iso_has_video_track(content: bytes, moov_start: int, moov_end: int) -> bool:
    moov_boxes = _iso_boxes(content, start=moov_start, end=moov_end)
    if not moov_boxes or not any(
        box_type == b"mvhd"
        and _valid_full_box(
            content,
            payload_start,
            payload_end,
            version_zero_size=100,
            version_one_size=112,
        )
        for box_type, payload_start, payload_end in moov_boxes
    ):
        return False
    for box_type, trak_start, trak_end in moov_boxes:
        if box_type != b"trak":
            continue
        trak_boxes = _iso_boxes(content, start=trak_start, end=trak_end)
        if not trak_boxes or not any(
            child_type == b"tkhd"
            and _valid_full_box(
                content,
                child_start,
                child_end,
                version_zero_size=84,
                version_one_size=96,
            )
            for child_type, child_start, child_end in trak_boxes
        ):
            continue
        for child_type, mdia_start, mdia_end in trak_boxes:
            if child_type != b"mdia":
                continue
            mdia_boxes = _iso_boxes(content, start=mdia_start, end=mdia_end)
            if not mdia_boxes or not any(
                media_type == b"mdhd"
                and _valid_full_box(
                    content,
                    child_start,
                    child_end,
                    version_zero_size=24,
                    version_one_size=36,
                )
                for media_type, child_start, child_end in mdia_boxes
            ):
                continue
            has_video_handler = any(
                media_type == b"hdlr"
                and payload_end - payload_start >= 24
                and content[payload_start] == 0
                and content[payload_start + 8 : payload_start + 12] == b"vide"
                for media_type, payload_start, payload_end in mdia_boxes
            )
            if not has_video_handler:
                continue
            for media_type, minf_start, minf_end in mdia_boxes:
                if media_type != b"minf":
                    continue
                minf_boxes = _iso_boxes(content, start=minf_start, end=minf_end)
                if not minf_boxes or not any(
                    child_type == b"vmhd"
                    and _valid_full_box(
                        content,
                        child_start,
                        child_end,
                        version_zero_size=12,
                    )
                    for child_type, child_start, child_end in minf_boxes
                ):
                    continue
                if any(
                    child_type == b"stbl"
                    and _iso_stbl_has_video_sample_entry(
                        content, child_start, child_end
                    )
                    for child_type, child_start, child_end in minf_boxes
                ):
                    return True
    return False


def _is_supported_iso_video(content: bytes, declared_mime_type: str) -> bool:
    boxes = _iso_boxes(content)
    if not boxes or boxes[0][0] != b"ftyp":
        return False
    _, ftyp_start, ftyp_end = boxes[0]
    ftyp = content[ftyp_start:ftyp_end]
    if len(ftyp) < 8 or (len(ftyp) - 8) % 4:
        return False
    major_brand = ftyp[:4]
    compatible_brands = {
        ftyp[index : index + 4] for index in range(8, len(ftyp), 4)
    }
    brands = compatible_brands | {major_brand}
    if declared_mime_type == "video/quicktime":
        if QUICKTIME_BRAND not in brands:
            return False
    elif not brands.intersection(MP4_BRANDS) or QUICKTIME_BRAND == major_brand:
        return False

    moov_boxes = [box for box in boxes if box[0] == b"moov"]
    has_media_data = any(
        box_type == b"mdat" and payload_end > payload_start
        for box_type, payload_start, payload_end in boxes
    )
    return has_media_data and any(
        _iso_has_video_track(content, payload_start, payload_end)
        for _, payload_start, payload_end in moov_boxes
    )


def _read_ebml_vint(
    content: bytes, offset: int, *, keep_marker: bool, max_width: int
) -> tuple[int, int, bool] | None:
    if offset >= len(content) or content[offset] == 0:
        return None
    first = content[offset]
    width = 1
    marker = 0x80
    while width <= max_width and not first & marker:
        marker >>= 1
        width += 1
    if width > max_width or offset + width > len(content):
        return None
    if keep_marker:
        return int.from_bytes(content[offset : offset + width], "big"), width, False
    value = first & (marker - 1)
    for byte in content[offset + 1 : offset + width]:
        value = (value << 8) | byte
    return value, width, value == (1 << (7 * width)) - 1


def _ebml_elements(
    content: bytes, *, start: int, end: int
) -> list[tuple[int, int, int, bool]] | None:
    offset = start
    elements = []
    while offset < end:
        element_id = _read_ebml_vint(
            content, offset, keep_marker=True, max_width=4
        )
        if element_id is None:
            return None
        element_value, id_width, _ = element_id
        size = _read_ebml_vint(
            content, offset + id_width, keep_marker=False, max_width=8
        )
        if size is None:
            return None
        payload_size, size_width, unknown_size = size
        payload_start = offset + id_width + size_width
        payload_end = end if unknown_size else payload_start + payload_size
        if payload_end > end:
            return None
        elements.append((element_value, payload_start, payload_end, unknown_size))
        offset = payload_end
        if unknown_size:
            break
    return elements if offset == end else None


def _ebml_uint(content: bytes, start: int, end: int) -> int | None:
    if not 0 < end - start <= 8:
        return None
    return int.from_bytes(content[start:end], "big")


def _valid_webm_info(content: bytes, start: int, end: int) -> bool:
    elements = _ebml_elements(content, start=start, end=end)
    if not elements:
        return False
    element_ids = {element_id for element_id, _, _, _ in elements}
    timestamp_scale = next(
        (
            _ebml_uint(content, payload_start, payload_end)
            for element_id, payload_start, payload_end, unknown_size in elements
            if element_id == 0x2AD7B1 and not unknown_size
        ),
        None,
    )
    return (
        timestamp_scale is not None
        and timestamp_scale > 0
        and {0x4D80, 0x5741}.issubset(element_ids)
    )


def _webm_tracks_include_video(content: bytes, start: int, end: int) -> bool:
    tracks = _ebml_elements(content, start=start, end=end)
    if not tracks:
        return False
    for element_id, entry_start, entry_end, unknown_size in tracks:
        if element_id != 0xAE or unknown_size:
            continue
        entry = _ebml_elements(content, start=entry_start, end=entry_end)
        if not entry:
            continue
        track_type = None
        track_number = None
        track_uid = None
        codec_id = None
        video_dimensions = None
        for child_id, payload_start, payload_end, child_unknown in entry:
            if child_unknown:
                return False
            payload = content[payload_start:payload_end]
            if child_id == 0xD7:
                track_number = _ebml_uint(content, payload_start, payload_end)
            elif child_id == 0x73C5:
                track_uid = _ebml_uint(content, payload_start, payload_end)
            elif child_id == 0x83:
                track_type = _ebml_uint(content, payload_start, payload_end)
            elif child_id == 0x86:
                codec_id = payload
            elif child_id == 0xE0:
                video = _ebml_elements(
                    content, start=payload_start, end=payload_end
                )
                if not video:
                    continue
                width = next(
                    (
                        _ebml_uint(content, child_start, child_end)
                        for video_id, child_start, child_end, video_unknown in video
                        if video_id == 0xB0 and not video_unknown
                    ),
                    None,
                )
                height = next(
                    (
                        _ebml_uint(content, child_start, child_end)
                        for video_id, child_start, child_end, video_unknown in video
                        if video_id == 0xBA and not video_unknown
                    ),
                    None,
                )
                video_dimensions = (width, height)
        if (
            track_number is not None
            and track_number > 0
            and track_uid is not None
            and track_uid > 0
            and track_type == 1
            and codec_id in WEBM_VIDEO_CODECS
            and video_dimensions is not None
            and all(dimension is not None and dimension > 0 for dimension in video_dimensions)
        ):
            return True
    return False


def _webm_cluster_has_frame(content: bytes, start: int, end: int) -> bool:
    elements = _ebml_elements(content, start=start, end=end)
    if not elements:
        return False
    has_timestamp = any(
        element_id == 0xE7
        and not unknown_size
        and _ebml_uint(content, payload_start, payload_end) is not None
        for element_id, payload_start, payload_end, unknown_size in elements
    )
    has_block = False
    for element_id, payload_start, payload_end, unknown_size in elements:
        if element_id != 0xA3 or unknown_size or payload_end - payload_start <= 4:
            continue
        track_number = _read_ebml_vint(
            content, payload_start, keep_marker=False, max_width=8
        )
        if (
            track_number is not None
            and track_number[0] > 0
            and payload_end - payload_start > track_number[1] + 3
        ):
            has_block = True
            break
    return has_timestamp and has_block


def _is_supported_webm_video(content: bytes) -> bool:
    root = _ebml_elements(content, start=0, end=len(content))
    if not root or root[0][0] != 0x1A45DFA3 or root[0][3]:
        return False
    _, header_start, header_end, _ = root[0]
    header = _ebml_elements(content, start=header_start, end=header_end)
    if not header:
        return False
    header_uints = {
        element_id: _ebml_uint(content, payload_start, payload_end)
        for element_id, payload_start, payload_end, unknown_size in header
        if not unknown_size and element_id in {0x4285, 0x4286, 0x42F2, 0x42F3, 0x42F7}
    }
    doc_type = next(
        (
            content[payload_start:payload_end].lower()
            for element_id, payload_start, payload_end, unknown_size in header
            if element_id == 0x4282 and not unknown_size
        ),
        None,
    )
    if (
        doc_type != b"webm"
        or header_uints.get(0x4286) != 1
        or header_uints.get(0x42F7) != 1
        or header_uints.get(0x42F2) != 4
        or header_uints.get(0x42F3) != 8
        or header_uints.get(0x4285) not in {1, 2}
    ):
        return False
    segment = next((element for element in root[1:] if element[0] == 0x18538067), None)
    if segment is None:
        return False
    _, segment_start, segment_end, _ = segment
    children = _ebml_elements(content, start=segment_start, end=segment_end)
    if not children:
        return False
    has_info = any(
        element_id == 0x1549A966
        and not unknown_size
        and _valid_webm_info(content, payload_start, payload_end)
        for element_id, payload_start, payload_end, unknown_size in children
    )
    has_cluster = any(
        element_id == 0x1F43B675
        and _webm_cluster_has_frame(content, payload_start, payload_end)
        for element_id, payload_start, payload_end, _ in children
    )
    has_video_track = any(
        element_id == 0x1654AE6B
        and not unknown_size
        and _webm_tracks_include_video(content, payload_start, payload_end)
        for element_id, payload_start, payload_end, unknown_size in children
    )
    return has_info and has_cluster and has_video_track


def inspect_upload_content(*, content: bytes, declared_mime_type: str) -> tuple[bool, str]:
    """Fail closed when uploaded bytes do not match the declared media type."""
    if b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*" in content:
        return False, "malware_signature_detected"

    if declared_mime_type.startswith("image/"):
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()
                detected_mime_type = IMAGE_FORMATS.get(image.format)
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            return False, "image_decompression_bomb"
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
            return False, "image_content_unrecognized"
        if detected_mime_type != declared_mime_type:
            return False, "declared_type_does_not_match_content"
        return True, ""

    if declared_mime_type in {"video/mp4", "video/quicktime"}:
        if not _is_supported_iso_video(content, declared_mime_type):
            return False, "video_container_unrecognized"
        return True, ""

    if declared_mime_type == "video/webm":
        if not _is_supported_webm_video(content):
            return False, "video_container_unrecognized"
        return True, ""

    return False, "unsupported_content_type"
