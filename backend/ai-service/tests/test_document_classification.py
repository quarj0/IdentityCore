from app.document_classification import build_ocr_lines, classify_document, normalize_text
from app.document_classification.mrz import evaluate_td3_mrz


def _mrz_check_digit(value: str) -> str:
    weights = (7, 3, 1)
    total = 0
    for index, character in enumerate(value):
        if character == "<":
            digit = 0
        elif character.isdigit():
            digit = int(character)
        else:
            digit = ord(character) - 55
        total += digit * weights[index % 3]
    return str(total % 10)


def _build_valid_td3_mrz(passport_number: str = "A1234567") -> tuple[str, str]:
    passport_number = passport_number[:9].ljust(9, "<")
    birth = "900101"
    expiry = "300101"
    optional = "<<<<<<<<<<<<<<<"
    line1 = "P<UTOEXAMPLE<<TEST<<<<<<<<<<<<<<<<<<<<<<<<<<"
    line1 = line1[:44].ljust(44, "<")
    passport_check = _mrz_check_digit(passport_number)
    birth_check = _mrz_check_digit(birth)
    expiry_check = _mrz_check_digit(expiry)
    line2_body = (
        f"{passport_number}{passport_check}UTO"
        f"{birth}{birth_check}M"
        f"{expiry}{expiry_check}"
        f"{optional}"
    )
    final_check = _mrz_check_digit(
        f"{passport_number}{passport_check}{birth}{birth_check}{expiry}{expiry_check}{optional}"
    )
    line2 = f"{line2_body}{final_check}"
    return line1, line2[:44]


def test_normalize_text_preserves_letters_and_digits():
    assert normalize_text("Electoral Commission—of Ghana 123") == "ELECTORAL COMMISSION OF GHANA 123"


def test_build_ocr_lines_preserves_text_and_scores():
    lines = build_ocr_lines(["Hello", "", "World"], [0.91])

    assert len(lines) == 2
    assert lines[0].text == "Hello"
    assert lines[0].normalized_text == "HELLO"
    assert lines[0].confidence == 0.91
    assert lines[1].text == "World"
    assert lines[1].confidence is None


def test_classify_recognizes_ghana_national_id():
    result = classify_document(
        build_ocr_lines(
            ["Electoral Commission of Ghana", "Voter Card"],
            [0.97, 0.96],
        ),
        expected_document_type="voter_id",
        country_code="GH",
    )

    assert result["classification_status"] == "recognized"
    assert result["predicted_document_type"] == "voter_id"
    assert result["matched_expected_document_type"] is True
    assert result["workflow_action"] == "continue"
    assert result["manual_review"]["required"] is False
    assert result["recommendation"] == "continue"


def test_classify_marks_mismatch_without_rejection():
    line1, line2 = _build_valid_td3_mrz()
    result = classify_document(
        build_ocr_lines(["PASSPORT", line1, line2], [0.95, 0.98, 0.98]),
        expected_document_type="national_id",
        country_code="GH",
    )

    assert result["classification_status"] == "recognized"
    assert result["predicted_document_type"] == "passport"
    assert result["matched_expected_document_type"] is False
    assert result["workflow_action"] == "continue_with_review"
    assert result["manual_review"]["required"] is True
    assert "document_type_mismatch" in result["issues"]


def test_classify_reports_invalid_passport_mrz():
    line1, line2 = _build_valid_td3_mrz()
    tampered_line2 = "Z" + line2[1:]
    result = classify_document(
        build_ocr_lines(["PASSPORT", line1, tampered_line2], [0.95, 0.98, 0.98]),
        expected_document_type="passport",
        country_code="GH",
    )

    assert result["classification_status"] == "unknown"
    assert "passport_mrz_invalid" in result["issues"]
    assert result["matched_expected_document_type"] is None


def test_classify_returns_unknown_for_blank_ocr():
    result = classify_document(
        build_ocr_lines([], []),
        expected_document_type="national_id",
        country_code="GH",
    )

    assert result["classification_status"] in {"insufficient_evidence", "unknown"}
    assert result["matched_expected_document_type"] is None
    assert result["workflow_action"] == "continue_with_review"
    assert result["manual_review"]["required"] is True


def test_classify_returns_unsupported_when_registry_is_empty(monkeypatch):
    monkeypatch.setattr(
        "app.document_classification.classifier.list_definitions",
        lambda country_code=None: (),
    )

    result = classify_document(
        build_ocr_lines(["PASSPORT"], [0.9]),
        expected_document_type="passport",
        country_code="ZZ",
    )

    assert result["classification_status"] == "unsupported"
    assert result["matched_expected_document_type"] is None
    assert "unsupported_country_document_definition" in result["issues"]


def test_passport_mrz_validation_covers_common_failures():
    valid_line1, valid_line2 = _build_valid_td3_mrz()
    valid = evaluate_td3_mrz([valid_line1, valid_line2])
    assert valid.valid is True

    invalid_length = evaluate_td3_mrz([valid_line1, valid_line2[:-1]])
    assert invalid_length.valid is False
    assert "passport_mrz_invalid" in invalid_length.reason_codes

    invalid_chars = evaluate_td3_mrz([valid_line1, valid_line2[:10] + "?" + valid_line2[11:]])
    assert invalid_chars.valid is False

    tampered = list(valid_line2)
    tampered[0] = "Z" if tampered[0] != "Z" else "Y"
    invalid_checks = evaluate_td3_mrz([valid_line1, "".join(tampered)])
    assert invalid_checks.valid is False
    assert "passport_mrz_invalid" in invalid_checks.reason_codes


def test_passport_with_valid_mrz_is_recognized_even_with_weak_visible_wording():
    line1, line2 = _build_valid_td3_mrz()
    result = classify_document(
        build_ocr_lines(["passport", line1, line2], [0.4, 0.95, 0.95]),
        expected_document_type="passport",
        country_code="US",
    )

    assert result["classification_status"] == "recognized"
    assert result["predicted_document_type"] == "passport"
    assert result["matched_expected_document_type"] is True


def test_document_classification_policy_is_configurable(monkeypatch):
    class FakeSettings:
        document_classification_policy = type(
            "Policy",
            (),
            {
                "minimum_candidate_evidence": 0.99,
                "minimum_required_group_coverage": 0.5,
                "minimum_classification_margin": 0.08,
                "minimum_average_ocr_confidence": 0.35,
            },
        )()
        document_classification_scoring_config = type(
            "Config",
            (),
            {
                "required_evidence_weight": 0.77,
                "optional_evidence_weight": 0.10,
                "structural_evidence_weight": 0.20,
                "ocr_quality_weight": 0.10,
                "negative_evidence_weight": 0.20,
            },
        )()

    monkeypatch.setattr("app.document_classification.classifier._get_settings", lambda: FakeSettings())

    result = classify_document(
        build_ocr_lines(["Electoral Commission of Ghana", "Voter Card"], [0.97, 0.96]),
        expected_document_type="voter_id",
        country_code="GH",
    )

    assert result["classification_status"] == "unknown"

    monkeypatch.setattr(
        "app.document_classification.classifier._get_settings",
        lambda: type(
            "LowerThresholdSettings",
            (),
            {
                "document_classification_policy": type(
                    "Policy",
                    (),
                    {
                        "minimum_candidate_evidence": 0.0,
                        "minimum_required_group_coverage": 0.0,
                        "minimum_classification_margin": 0.08,
                        "minimum_average_ocr_confidence": 0.35,
                    },
                )(),
                "document_classification_scoring_config": FakeSettings.document_classification_scoring_config,
            },
        )(),
    )

    result = classify_document(
        build_ocr_lines(["Electoral Commission of Ghana", "Voter Card"], [0.97, 0.96]),
        expected_document_type="voter_id",
        country_code="GH",
    )

    assert result["classification_status"] == "recognized"
