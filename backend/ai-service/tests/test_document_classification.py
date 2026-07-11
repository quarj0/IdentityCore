from app.pipeline import _infer_document_type_from_texts


def test_infers_ghana_card_as_national_id():
    predicted, confidence = _infer_document_type_from_texts(
        ["REPUBLIC OF GHANA", "GHANA CARD", "PERSONAL ID NUMBER"],
        "capture.jpg",
        "GH",
    )

    assert predicted == "national_id"
    assert confidence >= 0.9


def test_driver_license_uses_catalog_code():
    predicted, _confidence = _infer_document_type_from_texts(
        ["DRIVER LICENCE"],
        "capture.jpg",
        "GH",
    )

    assert predicted == "driver_license"


def test_infers_identity_card_wording_as_national_id():
    predicted, _confidence = _infer_document_type_from_texts(
        ["NATIONAL IDENTITY CARD"],
        "capture.jpg",
    )

    assert predicted == "national_id"
