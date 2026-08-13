"""Markers for routes that are part of the supported public REST contract."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.urls import path


PUBLIC_METHODS_ATTRIBUTE = "_identitycore_public_methods"
API_VISIBILITY_ATTRIBUTE = "_identitycore_api_visibility"


def public_api_path(
    route: str,
    view: Any,
    *,
    methods: Iterable[str],
    name: str | None = None,
):
    """Register a URL and identify the methods OpenAPI must document.

    Dashboard-only methods may share a view with public operations, so methods are
    declared at the URL boundary rather than inferred from the view class.
    """

    normalized_methods = frozenset(method.upper() for method in methods)
    if not normalized_methods:
        raise ValueError("A public API route must declare at least one HTTP method.")
    setattr(view, PUBLIC_METHODS_ATTRIBUTE, normalized_methods)
    setattr(view, API_VISIBILITY_ATTRIBUTE, "public")
    return path(route, view, name=name)


def internal_api_path(route: str, view: Any, *, name: str | None = None):
    """Register an explicitly non-public route inside a contract-managed prefix."""

    setattr(view, API_VISIBILITY_ATTRIBUTE, "internal")
    return path(route, view, name=name)
