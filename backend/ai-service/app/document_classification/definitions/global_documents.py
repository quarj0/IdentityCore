from __future__ import annotations

from ..models import DocumentDefinition, PatternRule, PhraseRule

DEFINITIONS = (
    DocumentDefinition(
        definition_id="global.passport.v1",
        document_type="passport",
        country_code=None,
        languages=("en",),
        required_phrase_groups=(
            ("PASSPORT",),
        ),
        optional_phrases=(
            PhraseRule("REPUBLIC OF", 0.4),
            PhraseRule("PASSPORT NO", 0.4),
        ),
        structural_patterns=(
            PatternRule("td3_mrz", "TD3_MRZ", 1.0),
        ),
        source_notes="Global passport evidence relies on visible wording and MRZ structure.",
    ),
)
