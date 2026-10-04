import pytest
from app.document_classification.mrz_parser import parse_mrz
from app.document_classification.mrz import evaluate_td3_mrz

TD1 = [
    "I<UTOD231458907<<<<<<<<<<<<<<<",
    "7408122F1204159UTO<<<<<<<<<<<6",
    "ERIKSSON<<ANNA<MARIA<<<<<<<<<<",
]
TD2 = [
    "I<UTOERIKSSON<<ANNA<MARIA".ljust(36, "<"),
    "D231458907UTO7408122F1204159<<<<<<<6",
]
TD3 = [
    "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
    "L898902C36UTO7408122F1204159ZE184226B<<<<<10",
]


@pytest.mark.parametrize("lines,fmt", [(TD1, "TD1"), (TD2, "TD2"), (TD3, "TD3")])
def test_icao_reference_fixtures(lines, fmt):
    # Canonical examples padded to their ICAO line lengths.
    length = {"TD1": 30, "TD2": 36, "TD3": 44}[fmt]
    lines = [line.ljust(length, "<") for line in lines]
    result = parse_mrz(lines)
    assert result["status"] == "valid", result
    assert result["format"] == fmt
    assert result["fields"]["issuing_country"]["value"] == "UTO"
    assert result["fields"]["name"]["value"] == "ERIKSSON ANNA MARIA"
    provenance = result["fields"]["document_number"]["provenance"]
    assert provenance["rule_version"] == "icao-9303-v1"
    assert provenance["source"] == "icao_mrz"


@pytest.mark.parametrize("lines", [TD1, TD2, TD3])
def test_tampering_a_checksummed_field_is_invalid(lines):
    length = 30 if len(lines) == 3 else (36 if lines[0].startswith("I") else 44)
    lines = [line.ljust(length, "<") for line in lines]
    index, start = (0, 5) if len(lines) == 3 else (1, 0)
    line = lines[index]
    lines[index] = (
        line[:start] + ("Z" if line[start] != "Z" else "A") + line[start + 1 :]
    )
    result = parse_mrz(lines)
    assert result["status"] == "invalid"
    assert result["issues"] == ["mrz_checksum_invalid"]


def test_absent_and_unsupported_formats_are_explicit():
    assert parse_mrz(["ordinary OCR text"])["status"] == "absent"
    assert parse_mrz(["V<UTO" + "<" * 39, "<" * 44])["status"] == "unsupported"
    assert parse_mrz(["I<UTO" + "<" * 25])["status"] == "invalid"


def test_issuing_country_comes_from_header_not_document_number():
    lines = [line.ljust(44, "<") for line in TD3]
    assert evaluate_td3_mrz(lines).issuing_country == "UTO"
    lines[1] = lines[1][:42] + "2" + lines[1][43:]
    assert not evaluate_td3_mrz(lines).valid
