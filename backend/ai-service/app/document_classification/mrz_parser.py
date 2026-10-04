"""ICAO TD1/TD2/TD3 evidence; fields never imply an authenticity decision."""

from __future__ import annotations

import re

from .mrz import _check_digit

VERSION = "icao-9303-v1"
ALLOWED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")


def parse_mrz(lines: list[str]) -> dict:
    candidates = [
        (index, "".join(text.upper().split()))
        for index, text in enumerate(lines[:100])
        if isinstance(text, str) and len(text) <= 128
    ]
    saw_candidate = False
    for offset, (index, first) in enumerate(candidates):
        if "<" not in first:
            continue
        saw_candidate = True
        length, count = (30, 3) if len(first) == 30 else (len(first), 2)
        fmt = {30: "TD1", 36: "TD2", 44: "TD3"}.get(length)
        if fmt is None or first[:1] not in ({"P"} if fmt == "TD3" else {"I", "A", "C"}):
            continue
        group = candidates[offset : offset + count]
        if len(group) != count or any(len(text) != length for _, text in group):
            return _result(fmt, "invalid", {}, {}, ["mrz_structure_invalid"])
        text = [line for _, line in group]
        if any(char not in ALLOWED for line in text for char in line):
            return _result(fmt, "invalid", {}, {}, ["mrz_characters_invalid"])
        a, b = text[:2]
        if fmt == "TD1":
            positions = {
                "document_number": (0, 5, 14),
                "issuing_country": (0, 2, 5),
                "nationality": (1, 15, 18),
                "date_of_birth_mrz": (1, 0, 6),
                "expiry_date_mrz": (1, 8, 14),
                "sex": (1, 7, 8),
                "name": (2, 0, 30),
            }
            checks = {
                "document_number": a[14] == _check_digit(a[5:14]),
                "birth": b[6] == _check_digit(b[:6]),
                "expiry": b[14] == _check_digit(b[8:14]),
                "composite": b[29]
                == _check_digit(a[5:30] + b[:7] + b[8:15] + b[18:29]),
            }
            extended = a[14] == "<"
        else:
            positions = {
                "document_number": (1, 0, 9),
                "issuing_country": (0, 2, 5),
                "nationality": (1, 10, 13),
                "date_of_birth_mrz": (1, 13, 19),
                "expiry_date_mrz": (1, 21, 27),
                "sex": (1, 20, 21),
                "name": (0, 5, length),
            }
            checks = {
                "document_number": b[9] == _check_digit(b[:9]),
                "birth": b[19] == _check_digit(b[13:19]),
                "expiry": b[27] == _check_digit(b[21:27]),
                "composite": b[-1] == _check_digit(b[:10] + b[13:20] + b[21:-1]),
            }
            if fmt == "TD3":
                checks["optional"] = b[42] == _check_digit(b[28:42]) or (
                    b[42] == "<" and set(b[28:42]) == {"<"}
                )
            extended = b[9] == "<"
        if extended:
            return _result(
                fmt, "unsupported", {}, checks, ["mrz_extended_number_unsupported"]
            )
        fields = {}
        for name, (line_index, start, end) in positions.items():
            raw = text[line_index][start:end]
            value = (
                raw
                if name.endswith("_mrz")
                else " ".join(raw.replace("<", " ").split())
            )
            fields[name] = {
                "value": value,
                "provenance": {
                    "source": "icao_mrz",
                    "format": fmt,
                    "rule_version": VERSION,
                    "ocr_line": group[line_index][0],
                    "start": start,
                    "end": end,
                },
            }
        raw_country = text[positions["issuing_country"][0]][
            positions["issuing_country"][1] : positions["issuing_country"][2]
        ]
        raw_nationality = text[positions["nationality"][0]][
            positions["nationality"][1] : positions["nationality"][2]
        ]
        raw_name = text[positions["name"][0]][
            positions["name"][1] : positions["name"][2]
        ]
        raw_number = text[positions["document_number"][0]][
            positions["document_number"][1] : positions["document_number"][2]
        ]
        mandatory_valid = bool(
            re.fullmatch(r"[A-Z0-9]+<*", raw_number)
            and re.fullmatch(r"[A-Z<]+", raw_name)
            and raw_name.split("<<", 1)[0].replace("<", "")
            and "<<" in raw_name
            and all(
                re.fullmatch(r"[A-Z]{3}|D<<", code)
                for code in (raw_country, raw_nationality)
            )
        )
        structure_valid = mandatory_valid and (
            all(
                set(fields[name]["value"].replace(" ", ""))
                <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                for name in ("issuing_country", "nationality", "name")
            )
            and all(
                set(fields[name]["value"].replace(" ", "")) <= set("0123456789<")
                for name in ("date_of_birth_mrz", "expiry_date_mrz")
            )
            and fields["sex"]["value"] in {"M", "F", ""}
        )
        if not structure_valid:
            return _result(fmt, "invalid", fields, checks, ["mrz_structure_invalid"])
        valid = all(checks.values())
        return _result(
            fmt,
            "valid" if valid else "invalid",
            fields,
            checks,
            [] if valid else ["mrz_checksum_invalid"],
        )
    return _result(
        None,
        "unsupported" if saw_candidate else "absent",
        {},
        {},
        ["mrz_format_unsupported"] if saw_candidate else [],
    )


def _result(fmt, status, fields, checks, issues):
    return {
        "format": fmt,
        "status": status,
        "rule_version": VERSION,
        "fields": fields,
        "checks": checks,
        "issues": issues,
    }
