from bisect import bisect_right
from io import BytesIO
import warnings

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
        if len(boxes) >= 100_000:
            return None
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


def _range_in_media(offset, length, media_ranges):
    # Top-level mdat payloads are ordered and disjoint. Locate the single
    # possible containing range in logarithmic time, even with many chunks.
    index = bisect_right(media_ranges, (offset, float("inf"))) - 1
    return length > 0 and index >= 0 and offset + length <= media_ranges[index][1]


def _iso_classic_samples_in_media(content, boxes, media_ranges, sample_budget):
    tables = {kind: (start, end) for kind, start, end in boxes}
    if not {b"stsz", b"stsc", b"stts"}.issubset(tables):
        return None

    def rows(kind, width):
        start, end = tables[kind]
        if end - start < 8 or content[start] != 0:
            return None
        count = int.from_bytes(content[start + 4 : start + 8], "big")
        if not 0 < count <= 100_000 or end - start != 8 + count * width * 4:
            return None
        return [
            tuple(
                int.from_bytes(content[pos + index * 4 : pos + index * 4 + 4], "big")
                for index in range(width)
            )
            for pos in range(start + 8, end, width * 4)
        ]

    start, end = tables[b"stsz"]
    if end - start < 12 or content[start] != 0:
        return None
    fixed_size = int.from_bytes(content[start + 4 : start + 8], "big")
    count = int.from_bytes(content[start + 8 : start + 12], "big")
    if not 0 < count <= 100_000 or end - start != 12 + (0 if fixed_size else count * 4):
        return None
    sample_budget[0] -= count
    if sample_budget[0] < 0:
        return None
    sizes = (
        [fixed_size] * count
        if fixed_size
        else [
            int.from_bytes(content[pos : pos + 4], "big")
            for pos in range(start + 12, end, 4)
        ]
    )
    if any(size == 0 for size in sizes):
        return None
    timing = rows(b"stts", 2)
    chunks = rows(b"stsc", 3)
    if not timing or not chunks or sum(row[0] for row in timing) != count:
        return None
    if (
        chunks[0][0] != 1
        or any(row[1] == 0 or row[2] < 1 for row in chunks)
        or any(left[0] >= right[0] for left, right in zip(chunks, chunks[1:]))
    ):
        return None
    kind = b"co64" if b"co64" in tables else b"stco"
    if kind not in tables:
        return None
    start, end = tables[kind]
    if end - start < 8 or content[start] != 0:
        return None
    chunk_count = int.from_bytes(content[start + 4 : start + 8], "big")
    width = 8 if kind == b"co64" else 4
    if (
        not 0 < chunk_count <= count
        or end - start != 8 + chunk_count * width
        or chunks[-1][0] > chunk_count
    ):
        return None
    sample = 0
    mapping = 0
    descriptions = set()
    for chunk_index in range(1, chunk_count + 1):
        while mapping + 1 < len(chunks) and chunks[mapping + 1][0] <= chunk_index:
            mapping += 1
        number = chunks[mapping][1]
        descriptions.add(chunks[mapping][2])
        if sample + number > count:
            return None
        pos = start + 8 + (chunk_index - 1) * width
        offset = int.from_bytes(content[pos : pos + width], "big")
        length = sum(sizes[sample : sample + number])
        if not _range_in_media(offset, length, media_ranges):
            return None
        sample += number
    return descriptions if sample == count else None


def _iso_fragment_track_ids(content, boxes, media_ranges, sample_budget):
    defaults = {}
    for kind, start, end in boxes:
        if kind != b"moov":
            continue
        for child, child_start, child_end in (
            _iso_boxes(content, start=start, end=end) or []
        ):
            if child != b"mvex":
                continue
            for entry, entry_start, entry_end in (
                _iso_boxes(content, start=child_start, end=child_end) or []
            ):
                if (
                    entry == b"trex"
                    and entry_end - entry_start == 24
                    and content[entry_start] == 0
                ):
                    track = int.from_bytes(
                        content[entry_start + 4 : entry_start + 8], "big"
                    )
                    defaults[track] = (
                        int.from_bytes(
                            content[entry_start + 16 : entry_start + 20], "big"
                        ),
                        int.from_bytes(
                            content[entry_start + 8 : entry_start + 12], "big"
                        ),
                    )
    valid_tracks = {}
    previous_sequence = None
    for kind, moof_start, moof_end in boxes:
        if kind != b"moof":
            continue
        moof_offset = moof_start - (
            8 if content[moof_start - 4 : moof_start] == b"moof" else 16
        )
        implicit_base = moof_offset
        children = _iso_boxes(content, start=moof_start, end=moof_end)
        if children is None:
            return None
        movie_headers = [(a, b) for k, a, b in children if k == b"mfhd"]
        if len(movie_headers) != 1:
            return None
        a, b = movie_headers[0]
        if b - a != 8 or content[a : a + 4] != b"\x00" * 4:
            return None
        sequence = int.from_bytes(content[a + 4 : b], "big")
        if previous_sequence is not None and sequence <= previous_sequence:
            return None
        previous_sequence = sequence
        for child, start, end in children:
            if child != b"traf":
                continue
            fragment = _iso_boxes(content, start=start, end=end)
            if fragment is None:
                return None
            headers = [(a, b) for k, a, b in fragment if k == b"tfhd"]
            if len(headers) != 1:
                return None
            a, b = headers[0]
            if b - a < 8 or content[a] != 0:
                return None
            flags = int.from_bytes(content[a + 1 : a + 4], "big")
            track = int.from_bytes(content[a + 4 : a + 8], "big")
            cursor = a + 8
            base = moof_offset
            if flags & 1:
                if cursor + 8 > b:
                    return None
                base = int.from_bytes(content[cursor : cursor + 8], "big")
                cursor += 8
            elif not flags & 0x020000:
                # First traf inherits the moof position; later traf boxes
                # inherit the end of the previous fragment's sample data.
                if implicit_base is None:
                    return None
                base = implicit_base
            size, description = defaults.get(track, (0, 1))
            if flags & 2:
                if cursor + 4 > b:
                    return None
                description = int.from_bytes(content[cursor : cursor + 4], "big")
                cursor += 4
            cursor += 4 * bool(flags & 8)
            if flags & 0x10:
                if cursor + 4 > b:
                    return None
                size = int.from_bytes(content[cursor : cursor + 4], "big")
                cursor += 4
            cursor += 4 * bool(flags & 0x20)
            if cursor != b:
                return None
            if flags & 0x010000:
                if any(kind == b"trun" for kind, _, _ in fragment):
                    return None
                # A legal duration-is-empty fragment supplies no data-end base.
                implicit_base = None
                continue
            previous_end = None
            implicit_base = None
            for run_kind, a, b in fragment:
                if run_kind != b"trun":
                    continue
                if b - a < 8 or content[a] not in {0, 1}:
                    return None
                run_flags = int.from_bytes(content[a + 1 : a + 4], "big")
                count = int.from_bytes(content[a + 4 : a + 8], "big")
                if not 0 < count <= 100_000:
                    return None
                sample_budget[0] -= count
                if sample_budget[0] < 0:
                    return None
                cursor = a + 8
                offset = previous_end if previous_end is not None else base
                if run_flags & 1:
                    if cursor + 4 > b:
                        return None
                    offset = base + int.from_bytes(
                        content[cursor : cursor + 4], "big", signed=True
                    )
                    cursor += 4
                cursor += 4 * bool(run_flags & 4)
                width = 4 * sum(
                    bool(run_flags & mask) for mask in (0x100, 0x200, 0x400, 0x800)
                )
                if cursor + count * width != b:
                    return None
                lengths = []
                for _ in range(count):
                    cursor += 4 * bool(run_flags & 0x100)
                    length = size
                    if run_flags & 0x200:
                        length = int.from_bytes(content[cursor : cursor + 4], "big")
                        cursor += 4
                    lengths.append(length)
                    cursor += 4 * bool(run_flags & 0x400) + 4 * bool(run_flags & 0x800)
                if not all(length > 0 for length in lengths) or not _range_in_media(
                    offset, sum(lengths), media_ranges
                ):
                    # An invalid run cannot donate its base to a later implicit
                    # run, nor can earlier valid samples authorize this fragment.
                    return None
                valid_tracks.setdefault(track, set()).add(description)
                previous_end = offset + sum(lengths)
            implicit_base = previous_end
    return valid_tracks


def _iso_stbl_has_video_sample_entry(
    content: bytes,
    start: int,
    end: int,
    *,
    media_ranges,
    fragment_descriptions,
    sample_budget,
) -> bool:
    boxes = _iso_boxes(content, start=start, end=end)
    if not boxes:
        return False
    required_tables = {b"stsd", b"stsc", b"stsz", b"stts"}
    box_types = {box_type for box_type, _, _ in boxes}
    if not required_tables.issubset(box_types) or not box_types.intersection(
        {b"co64", b"stco"}
    ):
        return False
    descriptions = set(fragment_descriptions or ())
    sizes = next(box for box in boxes if box[0] == b"stsz")
    if sizes[2] - sizes[1] < 12:
        return False
    classic_count = int.from_bytes(content[sizes[1] + 8 : sizes[1] + 12], "big")
    if classic_count or not descriptions:
        classic_descriptions = _iso_classic_samples_in_media(
            content, boxes, media_ranges, sample_budget
        )
        if not classic_descriptions:
            return False
        descriptions.update(classic_descriptions)
    stsd = next(box for box in boxes if box[0] == b"stsd")
    _, stsd_start, stsd_end = stsd
    if stsd_end - stsd_start < 8 or content[stsd_start] != 0:
        return False
    entry_count = int.from_bytes(content[stsd_start + 4 : stsd_start + 8], "big")
    entries = _iso_boxes(content, start=stsd_start + 8, end=stsd_end)
    if not entries or entry_count != len(entries):
        return False
    if any(index < 1 or index > len(entries) for index in descriptions):
        return False
    for index in descriptions:
        sample_type, sample_start, sample_end = entries[index - 1]
        config_type = ISO_VIDEO_SAMPLE_CONFIGS.get(sample_type)
        if config_type is None or sample_end - sample_start < 78:
            return False
        width = int.from_bytes(content[sample_start + 24 : sample_start + 26], "big")
        height = int.from_bytes(content[sample_start + 26 : sample_start + 28], "big")
        codec_boxes = _iso_boxes(content, start=sample_start + 78, end=sample_end)
        if not (
            width > 0
            and height > 0
            and codec_boxes
            and any(
                box_type == config_type and payload_end > payload_start
                for box_type, payload_start, payload_end in codec_boxes
            )
        ):
            return False
    return True


def _iso_has_video_track(
    content: bytes,
    moov_start: int,
    moov_end: int,
    *,
    media_ranges,
    fragment_tracks,
    sample_budget,
) -> bool:
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
        tkhd = next((box for box in trak_boxes if box[0] == b"tkhd"), None)
        if tkhd is None:
            continue
        track_start = tkhd[1]
        id_offset = 20 if content[track_start] == 1 else 12
        track_id = int.from_bytes(
            content[track_start + id_offset : track_start + id_offset + 4], "big"
        )
        if track_id == 0:
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
                        content,
                        child_start,
                        child_end,
                        media_ranges=media_ranges,
                        fragment_descriptions=fragment_tracks.get(track_id),
                        sample_budget=sample_budget,
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
    compatible_brands = {ftyp[index : index + 4] for index in range(8, len(ftyp), 4)}
    brands = compatible_brands | {major_brand}
    if declared_mime_type == "video/quicktime":
        if QUICKTIME_BRAND not in brands:
            return False
    elif not brands.intersection(MP4_BRANDS) or QUICKTIME_BRAND == major_brand:
        return False

    moov_boxes = [box for box in boxes if box[0] == b"moov"]
    media_ranges = [
        (start, end) for kind, start, end in boxes if kind == b"mdat" and end > start
    ]
    sample_budget = [100_000]
    fragment_tracks = _iso_fragment_track_ids(
        content, boxes, media_ranges, sample_budget
    )
    if fragment_tracks is None:
        return False
    return bool(media_ranges) and any(
        _iso_has_video_track(
            content,
            payload_start,
            payload_end,
            media_ranges=media_ranges,
            fragment_tracks=fragment_tracks,
            sample_budget=sample_budget,
        )
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
    content: bytes, *, start: int, end: int, budget: list[int] | None = None
) -> list[tuple[int, int, int, bool]] | None:
    if budget is None:
        budget = [100_000]
    offset = start
    elements = []
    while offset < end:
        budget[0] -= 1
        if budget[0] < 0:
            return None
        element_id = _read_ebml_vint(content, offset, keep_marker=True, max_width=4)
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


def _valid_webm_info(content: bytes, start: int, end: int, budget: list[int]) -> bool:
    elements = _ebml_elements(content, start=start, end=end, budget=budget)
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


def _webm_video_track_numbers(
    content: bytes, start: int, end: int, budget: list[int]
) -> dict[int, bool] | None:
    tracks = _ebml_elements(content, start=start, end=end, budget=budget)
    if not tracks:
        return None
    video_tracks = {}
    for element_id, entry_start, entry_end, unknown_size in tracks:
        if element_id != 0xAE or unknown_size:
            continue
        entry = _ebml_elements(content, start=entry_start, end=entry_end, budget=budget)
        if not entry:
            continue
        track_type = None
        track_number = None
        track_uid = None
        codec_id = None
        video_dimensions = None
        lacing_allowed = True
        lacing_seen = False
        for child_id, payload_start, payload_end, child_unknown in entry:
            if child_unknown:
                return None
            payload = content[payload_start:payload_end]
            if child_id == 0xD7:
                track_number = _ebml_uint(content, payload_start, payload_end)
            elif child_id == 0x73C5:
                track_uid = _ebml_uint(content, payload_start, payload_end)
            elif child_id == 0x83:
                track_type = _ebml_uint(content, payload_start, payload_end)
            elif child_id == 0x86:
                codec_id = payload
            elif child_id == 0x9C:
                value = _ebml_uint(content, payload_start, payload_end)
                if lacing_seen or value not in {0, 1}:
                    return None
                lacing_seen = True
                lacing_allowed = bool(value)
            elif child_id == 0xE0:
                video = _ebml_elements(
                    content, start=payload_start, end=payload_end, budget=budget
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
            and all(
                dimension is not None and dimension > 0
                for dimension in video_dimensions
            )
        ):
            if track_number in video_tracks:
                return None
            video_tracks[track_number] = lacing_allowed
    return video_tracks


def _webm_block_has_frames(content: bytes, start: int, end: int, width: int) -> bool:
    cursor = start + width + 3
    if cursor >= end:
        return False
    lacing = content[cursor - 1] & 0x06
    if not lacing:
        return True
    count = content[cursor] + 1
    cursor += 1
    if count < 2:
        return False
    if lacing == 0x04:
        return end - cursor >= count and (end - cursor) % count == 0
    sizes = []
    if lacing == 0x02:
        for _ in range(count - 1):
            size = 0
            while True:
                if cursor >= end:
                    return False
                value = content[cursor]
                cursor += 1
                size += value
                if value != 255:
                    break
            if size <= 0:
                return False
            sizes.append(size)
    else:
        for index in range(count - 1):
            value = _read_ebml_vint(content, cursor, keep_marker=False, max_width=8)
            if value is None or cursor + value[1] > end:
                return False
            cursor += value[1]
            size = value[0] if index == 0 else sizes[-1] + value[0] - ((1 << (7 * value[1] - 1)) - 1)
            if size <= 0:
                return False
            sizes.append(size)
    return end - cursor > sum(sizes)


def _webm_cluster_has_frame(
    content: bytes, start: int, end: int, video_tracks: dict[int, bool], budget: list[int]
) -> bool:
    elements = _ebml_elements(content, start=start, end=end, budget=budget)
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
        if unknown_size:
            continue
        if element_id == 0xA0:
            group = _ebml_elements(
                content, start=payload_start, end=payload_end, budget=budget
            )
            if not group:
                continue
            block = next(
                (item for item in group if item[0] == 0xA1 and not item[3]), None
            )
            if block is None:
                continue
            _, payload_start, payload_end, _ = block
        elif element_id != 0xA3:
            continue
        if payload_end - payload_start <= 4:
            continue
        track_number = _read_ebml_vint(
            content, payload_start, keep_marker=False, max_width=8
        )
        if (
            track_number is not None
            and track_number[0] in video_tracks
            and _webm_block_has_frames(content, payload_start, payload_end, track_number[1])
            and (video_tracks[track_number[0]] or not content[payload_start + track_number[1] + 2] & 0x06)
        ):
            has_block = True
            break
    return has_timestamp and has_block


def _is_supported_webm_video(content: bytes) -> bool:
    budget = [100_000]
    root = _ebml_elements(content, start=0, end=len(content), budget=budget)
    if not root or root[0][0] != 0x1A45DFA3 or root[0][3]:
        return False
    _, header_start, header_end, _ = root[0]
    header = _ebml_elements(content, start=header_start, end=header_end, budget=budget)
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
        or header_uints.get(0x4286, 1) != 1
        or header_uints.get(0x42F7, 1) != 1
        or header_uints.get(0x42F2, 4) != 4
        or header_uints.get(0x42F3, 8) != 8
        or header_uints.get(0x4285, 1) not in {1, 2}
    ):
        return False
    segment = next((element for element in root[1:] if element[0] == 0x18538067), None)
    if segment is None:
        return False
    _, segment_start, segment_end, _ = segment
    children = _ebml_elements(
        content, start=segment_start, end=segment_end, budget=budget
    )
    if not children:
        return False
    has_info = any(
        element_id == 0x1549A966
        and not unknown_size
        and _valid_webm_info(content, payload_start, payload_end, budget)
        for element_id, payload_start, payload_end, unknown_size in children
    )
    video_tracks = {}
    for element_id, payload_start, payload_end, unknown_size in children:
        if element_id == 0x1654AE6B and not unknown_size:
            tracks = _webm_video_track_numbers(content, payload_start, payload_end, budget)
            if tracks is None or video_tracks.keys() & tracks.keys():
                return False
            video_tracks.update(tracks)
    has_cluster = any(
        element_id == 0x1F43B675
        and _webm_cluster_has_frame(
            content, payload_start, payload_end, video_tracks, budget
        )
        for element_id, payload_start, payload_end, _ in children
    )
    return has_info and has_cluster and bool(video_tracks) and budget[0] >= 0


def inspect_upload_content(
    *, content: bytes, declared_mime_type: str
) -> tuple[bool, str]:
    """Fail closed when uploaded bytes do not match the declared media type."""
    if (
        b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        in content
    ):
        return False, "malware_signature_detected"

    if declared_mime_type.startswith("image/"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
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
