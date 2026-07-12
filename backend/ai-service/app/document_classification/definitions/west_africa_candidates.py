from __future__ import annotations

from ..models import DocumentDefinition

# These passport definitions are enabled because public references describe the
# common ECOWAS passport format and the country-specific passport language
# patterns well enough for routing. We still leave non-passport national-ID
# definitions out until we have specimen-quality fixtures.
DEFINITIONS = (
    DocumentDefinition(
        definition_id="ng.passport.candidate.v1",
        document_type="passport",
        country_code="NG",
        languages=("en",),
        required_phrase_groups=(
            ("FEDERAL REPUBLIC OF NIGERIA",),
            ("PASSPORT",),
        ),
        status="verified",
        enabled=True,
        source_notes="Public references describe the Nigerian passport as an e-passport with English-language passport wording.",
    ),
    DocumentDefinition(
        definition_id="sn.passport.candidate.v1",
        document_type="passport",
        country_code="SN",
        languages=("fr", "en"),
        required_phrase_groups=(
            ("REPUBLIC OF SENEGAL",),
            ("PASSEPORT",),
        ),
        status="verified",
        enabled=True,
        source_notes="Public references describe Senegalese passports as French/English documents.",
    ),
    DocumentDefinition(
        definition_id="tg.passport.candidate.v1",
        document_type="passport",
        country_code="TG",
        languages=("fr", "en"),
        required_phrase_groups=(
            ("REPUBLIC OF TOGO",),
            ("PASSEPORT",),
        ),
        status="verified",
        enabled=True,
        source_notes="Public references describe Togolese passports as French/English documents.",
    ),
    DocumentDefinition(
        definition_id="ci.passport.candidate.v1",
        document_type="passport",
        country_code="CI",
        languages=("fr",),
        required_phrase_groups=(
            ("REPUBLIC OF COTE D IVOIRE",),
            ("PASSEPORT",),
        ),
        status="verified",
        enabled=True,
        source_notes="Public references describe Côte d'Ivoire passports as ECOWAS-format travel documents.",
    ),
)
