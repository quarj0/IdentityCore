from apps.uploads.test_helpers import seal_test_upload
from datetime import timedelta
from unittest.mock import ANY, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import serializers, status
from rest_framework.test import APITestCase

from apps.audit.models import AuditEvent
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.uploads.tasks import cleanup_expired_uploads_task
from apps.uploads.scanning import inspect_upload_content
from apps.verification_sessions.serializers import resolve_session_upload
from apps.verifications.models import (
    VERIFICATION_SESSION_ACTIONS,
    Verification,
    VerificationSession,
    VerificationStatus,
)
from apps.verification_subjects.models import VerificationSubject


def _iso_box(box_type: bytes, payload: bytes) -> bytes:
    return (len(payload) + 8).to_bytes(4, "big") + box_type + payload


def _iso_video(
    *,
    major_brand: bytes = b"isom",
    handler_type: bytes = b"vide",
    description_index=None,
    supported_entry=1,
) -> bytes:
    ftyp = _iso_box(b"ftyp", major_brand + b"\x00\x00\x00\x00" + major_brand)
    sample_entry = bytearray(78)
    sample_entry[6:8] = (1).to_bytes(2, "big")
    sample_entry[24:26] = (640).to_bytes(2, "big")
    sample_entry[26:28] = (480).to_bytes(2, "big")
    sample_entry[40:42] = (1).to_bytes(2, "big")
    sample_entry[74:76] = (24).to_bytes(2, "big")
    entries = _iso_box(b"avc1", bytes(sample_entry) + _iso_box(b"avcC", b"\x01"))
    if description_index is not None:
        unsupported = _iso_box(b"mp4a", b"\x00" * 78)
        entries = (
            entries + unsupported if supported_entry == 1 else unsupported + entries
        )
    sample_description = _iso_box(
        b"stsd",
        b"\x00" * 4
        + (1 if description_index is None else 2).to_bytes(4, "big")
        + entries,
    )
    sample_table = _iso_box(
        b"stbl",
        sample_description
        + _iso_box(
            b"stts",
            b"\x00" * 4
            + (1).to_bytes(4, "big")
            + (1).to_bytes(4, "big")
            + (1000).to_bytes(4, "big"),
        )
        + _iso_box(
            b"stsc",
            b"\x00" * 4
            + (1).to_bytes(4, "big") * 3
            + (1 if description_index is None else description_index).to_bytes(
                4, "big"
            ),
        )
        + _iso_box(
            b"stsz",
            b"\x00" * 8 + (1).to_bytes(4, "big") + (11).to_bytes(4, "big"),
        )
        + _iso_box(
            b"stco",
            b"\x00" * 4 + (1).to_bytes(4, "big") + (100).to_bytes(4, "big"),
        ),
    )
    handler = _iso_box(b"hdlr", b"\x00" * 8 + handler_type + b"\x00" * 12)
    media_info = _iso_box(
        b"minf",
        _iso_box(b"vmhd", b"\x00" * 12)
        + _iso_box(b"dinf", _iso_box(b"dref", b"\x00" * 8))
        + sample_table,
    )
    media = _iso_box(b"mdia", _iso_box(b"mdhd", b"\x00" * 24) + handler + media_info)
    track = _iso_box(
        b"trak",
        _iso_box(b"tkhd", b"\x00" * 12 + (1).to_bytes(4, "big") + b"\x00" * 68) + media,
    )
    movie = _iso_box(b"moov", _iso_box(b"mvhd", b"\x00" * 100) + track)
    movie = movie.replace(
        (100).to_bytes(4, "big"), (len(ftyp) + len(movie) + 8).to_bytes(4, "big")
    )
    return ftyp + movie + _iso_box(b"mdat", b"video-frame")


def _fragmented_iso_video(
    *,
    invalid_offset=False,
    implicit_base=False,
    description_index=1,
    tfhd_description=None,
    supported_entry=1,
):
    from apps.uploads.scanning import _iso_boxes

    source = _iso_video()
    top = _iso_boxes(source)

    def init_box(kind, start, end):
        if kind in {b"moov", b"trak", b"mdia", b"minf", b"stbl"}:
            payload = b"".join(
                init_box(k, a, b)
                for k, a, b in _iso_boxes(source, start=start, end=end)
            )
            if kind == b"moov":
                payload += _iso_box(
                    b"mvex",
                    _iso_box(
                        b"trex",
                        b"\x00" * 4
                        + (1).to_bytes(4, "big")
                        + description_index.to_bytes(4, "big")
                        + (1000).to_bytes(4, "big")
                        + (11).to_bytes(4, "big")
                        + b"\x00" * 4,
                    ),
                )
            return _iso_box(kind, payload)
        if kind == b"stsd":
            original = source[start + 8 : end]
            unsupported = _iso_box(b"mp4a", b"\x00" * 78)
            entries = (
                original + unsupported
                if supported_entry == 1
                else unsupported + original
            )
            return _iso_box(kind, b"\x00" * 4 + (2).to_bytes(4, "big") + entries)
        if kind in {b"stts", b"stsc", b"stco"}:
            return _iso_box(kind, b"\x00" * 8)
        if kind == b"stsz":
            return _iso_box(kind, b"\x00" * 12)
        return _iso_box(kind, source[start:end])

    init = b"".join(init_box(k, a, b) for k, a, b in top if k in {b"ftyp", b"moov"})

    def fragment(offset):
        return _iso_box(
            b"moof",
            _iso_box(b"mfhd", b"\x00" * 4 + (1).to_bytes(4, "big"))
            + _iso_box(
                b"traf",
                _iso_box(
                    b"tfhd",
                    (
                        (0 if implicit_base else 0x020000)
                        | (2 if tfhd_description is not None else 0)
                    ).to_bytes(4, "big")
                    + (1).to_bytes(4, "big")
                    + (
                        b""
                        if tfhd_description is None
                        else tfhd_description.to_bytes(4, "big")
                    ),
                )
                + _iso_box(
                    b"trun",
                    b"\x00\x00\x02\x01"
                    + (1).to_bytes(4, "big")
                    + offset.to_bytes(4, "big", signed=True)
                    + (11).to_bytes(4, "big"),
                ),
            ),
        )

    offset = len(fragment(0)) + 8
    return (
        init
        + fragment(offset + (1000 if invalid_offset else 0))
        + _iso_box(b"mdat", b"video-frame")
    )


def _ebml_element(element_id: bytes, payload: bytes) -> bytes:
    if len(payload) >= 0x7F:
        raise ValueError("Test EBML payload is too large for its one-byte size.")
    return element_id + bytes([0x80 | len(payload)]) + payload


def _webm_video(*, track_type: int = 1, codec_id: bytes = b"V_VP9") -> bytes:
    header = _ebml_element(
        b"\x1a\x45\xdf\xa3",
        _ebml_element(b"\x42\x86", b"\x01")
        + _ebml_element(b"\x42\xf7", b"\x01")
        + _ebml_element(b"\x42\xf2", b"\x04")
        + _ebml_element(b"\x42\xf3", b"\x08")
        + _ebml_element(b"\x42\x82", b"webm")
        + _ebml_element(b"\x42\x85", b"\x02"),
    )
    info = _ebml_element(
        b"\x15\x49\xa9\x66",
        _ebml_element(b"\x2a\xd7\xb1", b"\x0f\x42\x40")
        + _ebml_element(b"\x4d\x80", b"IdentityCore")
        + _ebml_element(b"\x57\x41", b"IdentityCore"),
    )
    video = _ebml_element(
        b"\xe0",
        _ebml_element(b"\xb0", (640).to_bytes(2, "big"))
        + _ebml_element(b"\xba", (480).to_bytes(2, "big")),
    )
    track_entry = _ebml_element(
        b"\xae",
        _ebml_element(b"\xd7", b"\x01")
        + _ebml_element(b"\x73\xc5", b"\x01")
        + _ebml_element(b"\x83", bytes([track_type]))
        + _ebml_element(b"\x86", codec_id)
        + video,
    )
    tracks = _ebml_element(b"\x16\x54\xae\x6b", track_entry)
    cluster = _ebml_element(
        b"\x1f\x43\xb6\x75",
        _ebml_element(b"\xe7", b"\x00")
        + _ebml_element(b"\xa3", b"\x81\x00\x00\x80video-frame"),
    )
    return header + _ebml_element(b"\x18\x53\x80\x67", info + tracks + cluster)


class UploadVideoInspectionTests(TestCase):
    def test_media_range_lookup_is_logarithmic(self):
        from apps.uploads.scanning import _range_in_media

        class CountedRanges(list):
            reads = 0

            def __getitem__(self, index):
                self.reads += 1
                return super().__getitem__(index)

        ranges = CountedRanges((i * 9 + 8, i * 9 + 9) for i in range(99_999))
        for _ in range(100):
            self.assertTrue(_range_in_media(ranges[-1][0], 1, ranges))
        self.assertLess(ranges.reads, 2000)
        self.assertFalse(_range_in_media(0, 1, ranges))
        self.assertFalse(_range_in_media(ranges[-1][0], 2, ranges))
        self.assertFalse(_range_in_media(ranges[1][0] - 1, 1, ranges))

    def test_accepts_fragmented_mp4_with_implicit_moof_base(self):
        self.assert_video_result(
            _fragmented_iso_video(implicit_base=True), "video/mp4", expected_safe=True
        )

    def test_later_fragment_inherits_previous_sample_end(self):
        from apps.uploads.scanning import _iso_boxes, _iso_fragment_track_ids

        def traf(track, offset=None):
            header = _iso_box(
                b"tfhd",
                b"\x00\x00\x00\x10" + track.to_bytes(4, "big") + (3).to_bytes(4, "big"),
            )
            payload = (b"\x00\x00\x00\x01" if offset is not None else b"\x00" * 4) + (
                1
            ).to_bytes(4, "big")
            if offset is not None:
                payload += offset.to_bytes(4, "big", signed=True)
            return _iso_box(b"traf", header + _iso_box(b"trun", payload))

        def movie(offset):
            return _iso_box(b"moof", traf(1, offset) + traf(2))

        content = movie(len(movie(0)) + 8) + _iso_box(b"mdat", b"abcdef")
        boxes = _iso_boxes(content)
        media_ranges = [(a, b) for kind, a, b in boxes if kind == b"mdat"]
        self.assertEqual(
            _iso_fragment_track_ids(content, boxes, media_ranges, [100_000]),
            {1: {1}, 2: {1}},
        )

    def test_fragment_resolves_selected_sample_description(self):
        for tfhd in (False, True):
            for supported_entry in (1, 2):
                for selected in (0, 1, 2, 3):
                    with self.subTest(
                        tfhd=tfhd, supported_entry=supported_entry, selected=selected
                    ):
                        kwargs = (
                            {"tfhd_description": selected}
                            if tfhd
                            else {"description_index": selected}
                        )
                        self.assert_video_result(
                            _fragmented_iso_video(
                                supported_entry=supported_entry, **kwargs
                            ),
                            "video/mp4",
                            expected_safe=selected == supported_entry,
                        )

    def test_classic_resolves_selected_sample_description(self):
        for supported in (1, 2):
            for selected in (0, 1, 2, 3):
                with self.subTest(supported=supported, selected=selected):
                    self.assert_video_result(
                        _iso_video(
                            description_index=selected, supported_entry=supported
                        ),
                        "video/mp4",
                        expected_safe=selected == supported,
                    )

    def test_invalid_fragment_run_cannot_restart_following_run_at_base(self):
        from apps.uploads.scanning import _iso_boxes, _iso_fragment_track_ids

        def movie(base):
            header = _iso_box(
                b"tfhd",
                b"\x00\x00\x00\x11"
                + (1).to_bytes(4, "big")
                + base.to_bytes(8, "big")
                + (3).to_bytes(4, "big"),
            )
            invalid = _iso_box(
                b"trun",
                b"\x00\x00\x00\x01"
                + (1).to_bytes(4, "big")
                + (1000).to_bytes(4, "big", signed=True),
            )
            following = _iso_box(b"trun", b"\x00" * 4 + (1).to_bytes(4, "big"))
            return _iso_box(b"moof", _iso_box(b"traf", header + invalid + following))

        content = movie(len(movie(0)) + 8) + _iso_box(b"mdat", b"abcdef")
        boxes = _iso_boxes(content)
        ranges = [(a, b) for k, a, b in boxes if k == b"mdat"]
        self.assertIsNone(_iso_fragment_track_ids(content, boxes, ranges, [100_000]))

    def test_malformed_fragment_run_cannot_authorize_following_implicit_run(self):
        from apps.uploads.scanning import _iso_boxes, _iso_fragment_track_ids

        malformed = [
            b"\x00" * 4 + (0).to_bytes(4, "big"),
            b"\x00" * 4 + (100_001).to_bytes(4, "big"),
            b"\x00" * 7,
            b"\x02" + b"\x00" * 3 + (1).to_bytes(4, "big"),
            b"\x00\x00\x00\x01" + (1).to_bytes(4, "big"),
            b"\x00\x00\x02\x00" + (1).to_bytes(4, "big"),
        ]
        for preceding_valid in (False, True):
            for payload in malformed:
                with self.subTest(preceding_valid=preceding_valid, payload=payload):
                    def movie(base):
                        header = _iso_box(b"tfhd", b"\x00\x00\x00\x11"
                            + (1).to_bytes(4, "big") + base.to_bytes(8, "big") + (3).to_bytes(4, "big"))
                        valid = _iso_box(b"trun", b"\x00" * 4 + (1).to_bytes(4, "big"))
                        runs = (valid if preceding_valid else b"") + _iso_box(b"trun", payload) + valid
                        return _iso_box(b"moof", _iso_box(b"traf", header + runs))
                    content = movie(len(movie(0)) + 8) + _iso_box(b"mdat", b"abcdefghi")
                    boxes = _iso_boxes(content)
                    ranges = [(a, b) for kind, a, b in boxes if kind == b"mdat"]
                    self.assertIsNone(_iso_fragment_track_ids(content, boxes, ranges, [100_000]))

    def test_malformed_traf_cannot_donate_an_earlier_implicit_base(self):
        from apps.uploads.scanning import _iso_boxes, _iso_fragment_track_ids
        valid_run = _iso_box(b"trun", b"\x00" * 4 + (1).to_bytes(4, "big"))
        implicit_header = _iso_box(b"tfhd", b"\x00\x00\x00\x10" + (2).to_bytes(4, "big") + (3).to_bytes(4, "big"))
        malformed_headers = [b"", implicit_header * 2,
            _iso_box(b"tfhd", b"\x00" * 7),
            _iso_box(b"tfhd", b"\x01" + b"\x00" * 3 + (2).to_bytes(4, "big")),
            _iso_box(b"tfhd", b"\x00\x00\x00\x01" + (2).to_bytes(4, "big")),
            _iso_box(b"tfhd", b"\x00\x00\x00\x02" + (2).to_bytes(4, "big"))]
        for malformed in malformed_headers:
            with self.subTest(malformed=malformed):
                def movie(base):
                    explicit = _iso_box(b"tfhd", b"\x00\x00\x00\x11" + (1).to_bytes(4, "big")
                        + base.to_bytes(8, "big") + (3).to_bytes(4, "big"))
                    return _iso_box(b"moof", _iso_box(b"traf", explicit + valid_run)
                        + _iso_box(b"traf", malformed + valid_run)
                        + _iso_box(b"traf", implicit_header + valid_run))
                content = movie(len(movie(0)) + 8) + _iso_box(b"mdat", b"abcdefghi")
                boxes = _iso_boxes(content)
                ranges = [(a, b) for kind, a, b in boxes if kind == b"mdat"]
                self.assertIsNone(_iso_fragment_track_ids(content, boxes, ranges, [100_000]))

    def test_duration_empty_fragment_rejects_any_track_run(self):
        from apps.uploads.scanning import _iso_boxes, _iso_fragment_track_ids
        for run in [b"", b"\x00" * 4 + (0).to_bytes(4, "big"),
            b"\x00\x00\x00\x01" + (1).to_bytes(4, "big") + (1000).to_bytes(4, "big")]:
            with self.subTest(run=run):
                empty_header = _iso_box(b"tfhd", b"\x00\x01\x00\x00" + (1).to_bytes(4, "big"))
                invalid_empty = _iso_box(b"traf", empty_header + _iso_box(b"trun", run))
                def movie(offset):
                    header = _iso_box(b"tfhd", b"\x00\x02\x00\x10" + (2).to_bytes(4, "big") + (3).to_bytes(4, "big"))
                    valid = _iso_box(b"trun", b"\x00\x00\x00\x01" + (1).to_bytes(4, "big") + offset.to_bytes(4, "big"))
                    return _iso_box(b"moof", invalid_empty + _iso_box(b"traf", header + valid))
                content = movie(len(movie(0)) + 8) + _iso_box(b"mdat", b"abc")
                boxes = _iso_boxes(content)
                ranges = [(a, b) for kind, a, b in boxes if kind == b"mdat"]
                self.assertIsNone(_iso_fragment_track_ids(content, boxes, ranges, [100_000]))

    def test_fragment_sample_budget_is_shared_across_runs(self):
        from apps.uploads.scanning import _iso_boxes, _iso_fragment_track_ids

        def fragment(offset):
            header = _iso_box(
                b"tfhd",
                b"\x00\x02\x00\x10" + (1).to_bytes(4, "big") + (11).to_bytes(4, "big"),
            )
            run = _iso_box(
                b"trun",
                b"\x00\x00\x00\x01"
                + (60_000).to_bytes(4, "big")
                + offset.to_bytes(4, "big", signed=True),
            )
            return _iso_box(b"moof", _iso_box(b"traf", header + run + run))

        movie = fragment(len(fragment(0)) + 8)
        content = movie + _iso_box(b"mdat", b"x" * 660_000)
        boxes = _iso_boxes(content)
        media_ranges = [(a, b) for kind, a, b in boxes if kind == b"mdat"]
        self.assertIsNone(
            _iso_fragment_track_ids(content, boxes, media_ranges, [100_000])
        )

    def test_accepts_fragmented_mp4_with_samples_inside_media_data(self):
        self.assert_video_result(
            _fragmented_iso_video(), "video/mp4", expected_safe=True
        )

    def test_fragmented_mp4_rejects_samples_outside_media_data(self):
        self.assert_video_result(
            _fragmented_iso_video(invalid_offset=True), "video/mp4", expected_safe=False
        )

    def test_classic_mp4_rejects_out_of_range_chunk_offsets_and_short_media(self):
        content = _iso_video()
        chunk = content.index(b"stco") + 12
        wrong_offset = (
            content[:chunk]
            + (len(content) + 1).to_bytes(4, "big")
            + content[chunk + 4 :]
        )
        self.assert_video_result(wrong_offset, "video/mp4", expected_safe=False)
        short_media = content.replace(
            _iso_box(b"mdat", b"video-frame"), _iso_box(b"mdat", b"x")
        )
        self.assert_video_result(short_media, "video/mp4", expected_safe=False)

    def test_webm_blocks_must_reference_a_supported_video_track(self):
        content = _webm_video().replace(
            b"\x81\x00\x00\x80video-frame", b"\x82\x00\x00\x80video-frame"
        )
        self.assert_video_result(content, "video/webm", expected_safe=False)

    def test_webm_accepts_block_group_frames(self):
        content = _webm_video()
        old = _ebml_element(b"\xa3", b"\x81\x00\x00\x80video-frame")
        new = _ebml_element(
            b"\xa0", _ebml_element(b"\xa1", b"\x81\x00\x00\x80video-frame")
        )
        # Rebuild the enclosing cluster and segment lengths through the fixture.
        cluster = _ebml_element(
            b"\x1f\x43\xb6\x75", _ebml_element(b"\xe7", b"\x00") + old
        )
        replacement = _ebml_element(
            b"\x1f\x43\xb6\x75", _ebml_element(b"\xe7", b"\x00") + new
        )
        content = content.replace(cluster, replacement)
        segment = content.index(b"\x18\x53\x80\x67")
        content = (
            content[: segment + 4]
            + bytes([content[segment + 4] + len(new) - len(old)])
            + content[segment + 5 :]
        )
        self.assert_video_result(content, "video/webm", expected_safe=True)

    def test_webm_lacing_requires_complete_nonempty_frames(self):
        # Rebuild both enclosing sizes so inspection reaches the lace payload.
        original = _ebml_element(b"\xa3", b"\x81\x00\x00\x80video-frame")
        old_cluster = _ebml_element(b"\x1f\x43\xb6\x75", _ebml_element(b"\xe7", b"\x00") + original)
        layouts = [
            (b"\x04\xff", False), (b"\x04\x01a", False),
            (b"\x04\x01abcd", True), (b"\x04\x00a", False),
            (b"\x02\x01\xff", False), (b"\x02\x01\x05abcd", False),
            (b"\x02\x01\x02abcd", True), (b"\x02\x01\x00abcd", False),
            (b"\x06\x01\x82abcd", True), (b"\x06\x01\x82ab", False),
            (b"\x06\x02\x82\xbfabcdef", True),
            (b"\x06\x02\x82\xbcd", False), (b"\x06\x01\x00abc", False),
        ]
        for grouped in (False, True):
            for lace, safe in layouts:
                with self.subTest(grouped=grouped, lace=lace):
                    payload = b"\x81\x00\x00" + lace
                    block = _ebml_element(b"\xa1" if grouped else b"\xa3", payload)
                    if grouped:
                        block = _ebml_element(b"\xa0", block)
                    cluster = _ebml_element(b"\x1f\x43\xb6\x75", _ebml_element(b"\xe7", b"\x00") + block)
                    content = _webm_video().replace(old_cluster, cluster)
                    segment = content.index(b"\x18\x53\x80\x67")
                    content = content[:segment + 4] + bytes([content[segment + 4] + len(cluster) - len(old_cluster)]) + content[segment + 5:]
                    self.assert_video_result(content, "video/webm", expected_safe=safe)

    def test_webm_accepts_omitted_default_header_values(self):
        content = _webm_video()
        header_end = 5 + (content[4] & 0x7F)
        header = _ebml_element(b"\x1a\x45\xdf\xa3", _ebml_element(b"\x42\x82", b"webm"))
        self.assert_video_result(
            header + content[header_end:], "video/webm", expected_safe=True
        )

    def test_webm_element_budget_rejects_memory_amplification(self):
        from apps.uploads.scanning import _ebml_elements

        self.assertIsNone(_ebml_elements(b"\xec\x80" * 100_001, start=0, end=200_002))

    def test_image_decompression_warning_is_rejected(self):
        import warnings

        def oversized_image(*args, **kwargs):
            warnings.warn("Synthetic oversized image", Image.DecompressionBombWarning)

        with patch("apps.uploads.scanning.Image.open", side_effect=oversized_image):
            self.assertEqual(
                inspect_upload_content(
                    content=b"synthetic", declared_mime_type="image/png"
                ),
                (False, "image_decompression_bomb"),
            )

    def assert_video_result(
        self, content: bytes, mime_type: str, *, expected_safe: bool
    ) -> None:
        safe, reason = inspect_upload_content(
            content=content,
            declared_mime_type=mime_type,
        )
        self.assertEqual(safe, expected_safe)
        self.assertEqual(
            reason, "" if expected_safe else "video_container_unrecognized"
        )

    def test_accepts_structurally_valid_supported_video_containers(self):
        fixtures = (
            (_iso_video(), "video/mp4"),
            (_iso_video(major_brand=b"qt  "), "video/quicktime"),
            (_webm_video(), "video/webm"),
        )

        for content, mime_type in fixtures:
            with self.subTest(mime_type=mime_type):
                self.assert_video_result(content, mime_type, expected_safe=True)

    def test_rejects_magic_byte_only_video_impostors(self):
        fixtures = (
            (b"\x00\x00\x00\x0cftypisom", "video/mp4"),
            (b"\x1a\x45\xdf\xa3", "video/webm"),
        )

        for content, mime_type in fixtures:
            with self.subTest(mime_type=mime_type):
                self.assert_video_result(content, mime_type, expected_safe=False)

    def test_rejects_truncated_iso_box(self):
        content = _iso_video()[:-1]

        self.assert_video_result(content, "video/mp4", expected_safe=False)

    def test_rejects_iso_audio_only_track(self):
        self.assert_video_result(
            _iso_video(handler_type=b"soun"),
            "video/mp4",
            expected_safe=False,
        )

    def test_rejects_iso_brand_that_does_not_match_declared_type(self):
        self.assert_video_result(
            _iso_video(major_brand=b"qt  "),
            "video/mp4",
            expected_safe=False,
        )

    def test_rejects_webm_without_video_track(self):
        self.assert_video_result(
            _webm_video(track_type=2, codec_id=b"A_OPUS"),
            "video/webm",
            expected_safe=False,
        )

    def test_rejects_webm_with_unsupported_video_codec(self):
        self.assert_video_result(
            _webm_video(codec_id=b"V_MPEG4"),
            "video/webm",
            expected_safe=False,
        )


class UploadCreateTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Example Bank", slug="example-bank"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Example Tenant",
            slug="example-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="ops@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Akosua Owusu",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding verification",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now() + timedelta(hours=24),
            created_by=self.user,
        )
        self.session = VerificationSession(
            verification=self.verification,
            tenant=self.tenant,
            expires_at=self.verification.expires_at,
            allowed_actions_json=list(VERIFICATION_SESSION_ACTIONS),
        )
        self.raw_session_token = "portal-secret-token"
        self.session.set_session_token(self.raw_session_token)
        self.session.save()

    def auth_headers(self, token=None, session_id=None):
        return {
            "HTTP_AUTHORIZATION": f"Bearer {token or self.raw_session_token}",
            "HTTP_X_SESSION_ID": session_id or self.session.public_id,
        }

    def test_create_upload_returns_expiring_upload_url(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["upload_id"].startswith("upl_"))
        self.assertIn(
            response.data["data"]["upload_id"], response.data["data"]["upload_url"]
        )
        self.assertEqual(
            response.data["data"]["upload_headers"],
            {
                "Content-Type": "image/jpeg",
                "x-amz-server-side-encryption": "AES256",
            },
        )
        self.assertEqual(
            response.data["data"]["upload_transfer_path"],
            f"/uploads/{response.data['data']['upload_id']}/transfer",
        )
        upload = Upload.objects.get(public_id=response.data["data"]["upload_id"])
        self.assertEqual(upload.tenant, self.tenant)
        self.assertEqual(upload.verification, self.verification)
        self.assertEqual(upload.verification_session, self.session)
        self.assertEqual(upload.purpose, UploadPurpose.DOCUMENT_CAPTURE)
        self.assertEqual(upload.status, UploadStatus.INITIATED)
        self.assertEqual(
            response.data["data"]["upload_complete_path"],
            f"/uploads/{upload.public_id}/complete",
        )
        self.assertEqual(
            upload.storage_key,
            (
                f"organizations/{self.organization.public_id}"
                f"/verifications/{self.verification.public_id}"
                f"/documents/{upload.public_id}"
            ),
        )

    @patch("apps.uploads.views.inspect_upload_content", return_value=(True, ""))
    @patch("apps.uploads.views.put_object_bytes")
    def test_transfer_upload_proxies_file_to_private_storage(
        self, put_object_bytes, inspect_upload_content
    ):
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["upload_id"], upload_id)
        put_object_bytes.assert_called_once()
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.UPLOADED)
        self.assertEqual(
            upload.checksum_sha256,
            "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        )

        duplicate_response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(duplicate_response.status_code, status.HTTP_200_OK)
        put_object_bytes.assert_called_once()

        upload.status = UploadStatus.CONSUMED
        upload.consumed_at = timezone.now()
        upload.save(update_fields=["status", "consumed_at", "updated_at"])
        consumed_retry = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(consumed_retry.status_code, status.HTTP_200_OK)
        put_object_bytes.assert_called_once()

    @patch("apps.uploads.views.inspect_upload_content", return_value=(True, ""))
    @patch("apps.uploads.views.put_object_bytes")
    def test_duplicate_transfer_with_different_content_is_rejected(
        self, put_object_bytes, inspect_upload_content
    ):
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]
        self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"nope", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        put_object_bytes.assert_called_once()

    @patch("apps.uploads.views.inspect_upload_content")
    @patch("apps.uploads.views.put_object_bytes")
    def test_unsafe_retry_is_scanned_but_does_not_quarantine_validated_upload(
        self, put_object_bytes, inspect_upload_content
    ):
        inspect_upload_content.side_effect = [
            (True, ""),
            (False, "image_content_unrecognized"),
        ]
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]
        self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"nope", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "upload_quarantined")
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.UPLOADED)
        self.assertEqual(upload.quarantine_reason, "")
        self.assertEqual(inspect_upload_content.call_count, 2)
        put_object_bytes.assert_called_once()

    @patch("apps.uploads.views.put_object_bytes")
    def test_unrecognized_content_is_quarantined_before_processing(
        self, put_object_bytes
    ):
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.QUARANTINED)
        self.assertEqual(upload.quarantine_reason, "image_content_unrecognized")
        put_object_bytes.assert_not_called()

    @patch("apps.uploads.views.put_object_bytes")
    def test_magic_only_liveness_video_is_quarantined_before_processing(
        self, put_object_bytes
    ):
        content = b"\x1a\x45\xdf\xa3"
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "liveness_capture",
                "mime_type": "video/webm",
                "file_size_bytes": len(content),
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "liveness.webm", content, content_type="video/webm"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "upload_quarantined")
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.QUARANTINED)
        self.assertEqual(upload.quarantine_reason, "video_container_unrecognized")
        put_object_bytes.assert_not_called()

    @patch("apps.uploads.views.delete_object")
    @patch("apps.uploads.views.put_object_bytes")
    @patch("apps.uploads.views.inspect_upload_content", return_value=(True, ""))
    @patch(
        "apps.uploads.views.get_object_bytes",
        return_value=(b"test", "image/jpeg"),
    )
    def test_complete_validates_direct_upload_into_immutable_key(
        self,
        get_object_bytes,
        inspect_upload_content,
        put_object_bytes,
        delete_object,
    ):
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]
        upload = Upload.objects.get(public_id=upload_id)
        original_key = upload.storage_key

        response = self.client.post(
            reverse("upload-complete", kwargs={"upload_id": upload_id}),
            {},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        upload.refresh_from_db()
        self.assertEqual(upload.status, UploadStatus.UPLOADED)
        self.assertNotEqual(upload.storage_key, original_key)
        self.assertTrue(upload.storage_key.startswith(f"{original_key}.validated."))
        get_object_bytes.assert_called_once_with(
            bucket_name=ANY,
            key=original_key,
            tenant_scope=upload.tenant.public_id,
            environment="sandbox",
            max_bytes=4,
        )
        put_object_bytes.assert_called_once_with(
            bucket_name=ANY,
            key=upload.storage_key,
            tenant_scope=upload.tenant.public_id,
            environment="sandbox",
            content=b"test",
            content_type="image/jpeg",
        )
        delete_object.assert_called_once_with(bucket_name=ANY, key=original_key)

        retry = self.client.post(
            reverse("upload-complete", kwargs={"upload_id": upload_id}),
            {},
            format="json",
            **self.auth_headers(),
        )
        self.assertEqual(retry.status_code, status.HTTP_200_OK)
        get_object_bytes.assert_called_once()

    @patch("apps.uploads.views.delete_object")
    @patch("apps.uploads.views.put_object_bytes")
    @patch(
        "apps.uploads.views.get_object_bytes",
        return_value=(b"test", "image/jpeg"),
    )
    def test_unsafe_direct_upload_is_quarantined_without_copying_bytes(
        self, get_object_bytes, put_object_bytes, delete_object
    ):
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]

        response = self.client.post(
            reverse("upload-complete", kwargs={"upload_id": upload_id}),
            {},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "upload_quarantined")
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.QUARANTINED)
        self.assertEqual(upload.quarantine_reason, "image_content_unrecognized")
        get_object_bytes.assert_called_once()
        put_object_bytes.assert_not_called()
        delete_object.assert_not_called()

    def test_initiated_direct_upload_cannot_be_submitted_as_evidence(self):
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )

        with self.assertRaisesMessage(
            serializers.ValidationError,
            "Upload must be completed and validated before submission.",
        ):
            resolve_session_upload(
                verification_session=self.session,
                upload_id=create_response.data["data"]["upload_id"],
                purpose=UploadPurpose.DOCUMENT_CAPTURE,
            )

    @patch(
        "apps.uploads.scanning.Image.open",
        side_effect=Image.DecompressionBombError("oversized image"),
    )
    def test_decompression_bomb_is_quarantined(self, _image_open):
        safe, reason = inspect_upload_content(
            content=b"oversized-image",
            declared_mime_type="image/jpeg",
        )

        self.assertFalse(safe)
        self.assertEqual(reason, "image_decompression_bomb")

    def test_create_upload_requires_session_authentication(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 1024,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_upload_requires_upload_action_scope(self):
        self.session.allowed_actions_json = ["session:read"]
        self.session.save(update_fields=["allowed_actions_json", "updated_at"])

        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_upload_rejects_unsupported_mime_type(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "application/pdf",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_upload_rejects_video_for_selfie_capture(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "selfie_capture",
                "mime_type": "video/mp4",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mime_type", response.data["error"]["details"])

    def test_create_upload_rejects_image_for_liveness_capture(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "liveness_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mime_type", response.data["error"]["details"])

    def test_create_upload_accepts_video_for_liveness_capture(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "liveness_capture",
                "mime_type": "video/mp4",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["upload_id"].startswith("upl_"))


class UploadRetentionTaskTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Example Bank", slug="example-bank-retention"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Example Tenant Retention",
            slug="example-tenant-retention",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="ops-retention@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Akosua Owusu",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding verification",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now() + timedelta(hours=24),
            created_by=self.user,
        )
        self.session = VerificationSession(
            verification=self.verification,
            tenant=self.tenant,
            expires_at=self.verification.expires_at,
            allowed_actions_json=list(VERIFICATION_SESSION_ACTIONS),
        )
        self.session.set_session_token("retention-secret-token")
        self.session.save()

    def test_cleanup_expired_uploads_marks_temporary_upload_expired_and_deleted(self):
        expired_upload = seal_test_upload(
            Upload.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                verification_session=self.session,
                purpose=UploadPurpose.DOCUMENT_CAPTURE,
                storage_key=(
                    f"organizations/{self.organization.public_id}"
                    f"/verifications/{self.verification.public_id}/documents/upl_expired"
                ),
                storage_provider="local",
                mime_type="image/jpeg",
                file_size_bytes=1024,
                status=UploadStatus.INITIATED,
                expires_at=timezone.now() - timedelta(minutes=1),
            )
        )
        active_upload = seal_test_upload(
            Upload.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                verification_session=self.session,
                purpose=UploadPurpose.SELFIE_CAPTURE,
                storage_key=(
                    f"organizations/{self.organization.public_id}"
                    f"/verifications/{self.verification.public_id}/selfies/upl_active"
                ),
                storage_provider="local",
                mime_type="image/jpeg",
                file_size_bytes=2048,
                status=UploadStatus.INITIATED,
                expires_at=timezone.now() + timedelta(minutes=10),
            )
        )

        cleaned = cleanup_expired_uploads_task(limit=10)

        expired_upload.refresh_from_db()
        active_upload.refresh_from_db()
        self.assertEqual(cleaned, 1)
        self.assertEqual(expired_upload.status, UploadStatus.EXPIRED)
        self.assertIsNotNone(expired_upload.deleted_at)
        self.assertEqual(active_upload.status, UploadStatus.INITIATED)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="retention.temporary_upload_deleted",
                target_id=expired_upload.public_id,
            ).exists()
        )

    def test_cleanup_expired_uploads_deletes_consumed_temp_upload_after_retention_window(
        self,
    ):
        consumed_upload = seal_test_upload(
            Upload.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                verification_session=self.session,
                purpose=UploadPurpose.SELFIE_CAPTURE,
                storage_key=(
                    f"organizations/{self.organization.public_id}"
                    f"/verifications/{self.verification.public_id}/selfies/upl_consumed"
                ),
                storage_provider="local",
                mime_type="image/jpeg",
                file_size_bytes=1024,
                status=UploadStatus.CONSUMED,
                expires_at=timezone.now() + timedelta(minutes=10),
                consumed_at=timezone.now() - timedelta(hours=25),
            )
        )

        cleaned = cleanup_expired_uploads_task(limit=10)

        consumed_upload.refresh_from_db()
        self.assertEqual(cleaned, 1)
        self.assertEqual(consumed_upload.status, UploadStatus.EXPIRED)
        self.assertIsNotNone(consumed_upload.deleted_at)

    def _expired_upload(self, status=UploadStatus.INITIATED):
        return seal_test_upload(
            Upload.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                verification_session=self.session,
                purpose=UploadPurpose.DOCUMENT_CAPTURE,
                storage_key=f"private/{Upload.objects.count()}.jpg",
                storage_provider="s3",
                mime_type="image/jpeg",
                file_size_bytes=100,
                status=status,
                expires_at=timezone.now() - timedelta(days=2),
                consumed_at=timezone.now() - timedelta(days=2)
                if status == UploadStatus.CONSUMED
                else None,
            )
        )

    @patch(
        "apps.uploads.tasks.get_object_storage_temp_bucket_name",
        return_value="temporary",
    )
    @patch("apps.uploads.tasks.delete_object")
    def test_active_holds_protect_all_temporary_upload_states(self, delete, _bucket):
        from apps.verifications.models import RetentionLegalHold

        for scope in (None, self.verification):
            hold = RetentionLegalHold.objects.create(
                tenant=self.tenant, verification=scope, reason="incident"
            )
            for upload_status in (
                UploadStatus.INITIATED,
                UploadStatus.UPLOADED,
                UploadStatus.QUARANTINED,
                UploadStatus.CONSUMED,
            ):
                upload = self._expired_upload(upload_status)
                self.assertEqual(cleanup_expired_uploads_task(limit=10), 0)
                upload.refresh_from_db()
                self.assertIsNone(upload.deleted_at)
            delete.assert_not_called()
            hold.released_at = timezone.now()
            hold.save(update_fields=["released_at"])
            self.assertEqual(cleanup_expired_uploads_task(limit=10), 4)
            delete.reset_mock()

    @patch(
        "apps.uploads.tasks.get_object_storage_temp_bucket_name",
        return_value="temporary",
    )
    @patch("apps.uploads.tasks.delete_object")
    def test_expired_and_other_tenant_holds_do_not_block_cleanup(self, delete, _bucket):
        from apps.verifications.models import RetentionLegalHold

        other_org = Organization.objects.create(name="Other", slug="other-retention")
        other = Tenant.objects.create(
            organization=other_org,
            name="Other",
            slug="other-retention",
            status="active",
        )
        RetentionLegalHold.objects.create(tenant=other, reason="other tenant")
        RetentionLegalHold.objects.create(
            tenant=self.tenant,
            reason="expired",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        upload = self._expired_upload()
        self.assertEqual(cleanup_expired_uploads_task(limit=10), 1)
        delete.assert_called_once_with(bucket_name="temporary", key=upload.storage_key)

    @patch(
        "apps.uploads.tasks.get_object_storage_temp_bucket_name",
        return_value="temporary",
    )
    @patch(
        "apps.uploads.tasks.delete_object",
        side_effect=RuntimeError("private-storage-error"),
    )
    def test_storage_failure_remains_retryable(self, delete, _bucket):
        upload = self._expired_upload()
        self.assertEqual(cleanup_expired_uploads_task(limit=10), 0)
        upload.refresh_from_db()
        self.assertIsNone(upload.deleted_at)
        self.assertEqual(upload.status, UploadStatus.INITIATED)
        self.assertEqual(upload.deletion_attempt_count, 1)
        self.assertGreater(upload.deletion_retry_at, timezone.now())
        failure = AuditEvent.objects.get(
            action="retention.temporary_upload_deletion_failed",
            target_id=upload.public_id,
        )
        self.assertNotIn(upload.storage_key, str(failure.metadata_json))
        delete.side_effect = None
        upload.deletion_retry_at = timezone.now() - timedelta(seconds=1)
        upload.save(update_fields=["deletion_retry_at", "updated_at"])
        self.assertEqual(cleanup_expired_uploads_task(limit=10), 1)

    @patch(
        "apps.uploads.tasks.get_object_storage_temp_bucket_name",
        return_value="temporary",
    )
    @patch("apps.uploads.tasks.delete_object")
    def test_failed_oldest_upload_does_not_monopolize_cleanup_batch(
        self, delete, _bucket
    ):
        oldest = self._expired_upload()
        oldest.expires_at = timezone.now() - timedelta(days=3)
        oldest.save(update_fields=["expires_at", "updated_at"])
        later = self._expired_upload()
        delete.side_effect = [RuntimeError("storage unavailable"), None]

        self.assertEqual(cleanup_expired_uploads_task(limit=1), 0)
        self.assertEqual(cleanup_expired_uploads_task(limit=1), 1)

        oldest.refresh_from_db()
        later.refresh_from_db()
        self.assertIsNone(oldest.deleted_at)
        self.assertIsNotNone(oldest.deletion_retry_at)
        self.assertIsNotNone(later.deleted_at)

    @patch("apps.uploads.tasks.get_object_storage_temp_bucket_name", return_value="")
    def test_missing_remote_storage_configuration_does_not_claim_deletion(
        self, _bucket
    ):
        upload = self._expired_upload()
        self.assertEqual(cleanup_expired_uploads_task(limit=10), 0)
        upload.refresh_from_db()
        self.assertIsNone(upload.deleted_at)
