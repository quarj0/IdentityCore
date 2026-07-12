from __future__ import annotations

from ..models import DocumentDefinition

DEFINITIONS = (
    DocumentDefinition(
        definition_id="gh.ecowas_identity_card.v1",
        document_type="national_id",
        country_code="GH",
        languages=("en",),
        required_phrase_groups=(
            ("ECOWAS IDENTITY CARD",),
            ("REPUBLIC OF GHANA",),
        ),
        source_notes="Verified Ghana ECOWAS identity card wording.",
    ),
    DocumentDefinition(
        definition_id="gh.voter_card.v1",
        document_type="voter_id",
        country_code="GH",
        languages=("en",),
        required_phrase_groups=(
            ("ELECTORAL COMMISSION OF GHANA",),
            ("VOTER CARD",),
        ),
        source_notes="Verified Ghana voter card wording.",
    ),
    DocumentDefinition(
        definition_id="gh.nhis_membership_card.v1",
        document_type="health_id",
        country_code="GH",
        languages=("en",),
        required_phrase_groups=(
            ("REPUBLIC OF GHANA",),
            ("NATIONAL HEALTH INSURANCE SCHEME",),
            ("MEMBERSHIP IDENTIFICATION CARD",),
            ("NHIS",),
        ),
        source_notes="Verified Ghana NHIS membership card wording.",
    ),
)
