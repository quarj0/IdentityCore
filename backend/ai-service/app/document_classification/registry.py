from __future__ import annotations

from .definitions import (
    GH_DEFINITIONS,
    GLOBAL_DEFINITIONS,
    WEST_AFRICA_CANDIDATE_DEFINITIONS,
)
from .models import DocumentDefinition

ALL_DEFINITIONS: tuple[DocumentDefinition, ...] = tuple(
    definition
    for definition in (*GH_DEFINITIONS, *GLOBAL_DEFINITIONS, *WEST_AFRICA_CANDIDATE_DEFINITIONS)
    if definition.enabled and definition.status == "verified"
)


def _get_settings():
    try:
        from app.settings import get_settings

        return get_settings()
    except ModuleNotFoundError:
        return None


def _active_country_codes() -> tuple[str, ...]:
    settings = _get_settings()
    if settings is None:
        return ()
    return settings.document_classification_enabled_country_codes


def list_definitions(country_code: str | None = None) -> tuple[DocumentDefinition, ...]:
    active_country_codes = _active_country_codes()
    if not country_code:
        return tuple(
            definition
            for definition in ALL_DEFINITIONS
            if not active_country_codes
            or definition.country_code is None
            or definition.country_code in active_country_codes
        )
    return tuple(
        definition
        for definition in ALL_DEFINITIONS
        if (definition.country_code is None or definition.country_code == country_code)
        and (
            not active_country_codes
            or definition.country_code is None
            or definition.country_code in active_country_codes
        )
    )
