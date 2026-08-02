import hashlib
import json

from django.core import signing
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
CURSOR_SALT = "identitycore.list-cursor.v1"


def pagination_params(query_params, *, default_page_size=DEFAULT_PAGE_SIZE):
    """Validate page-number pagination parameters supplied by an API request."""
    errors = {}
    try:
        page = int(query_params.get("page", 1))
        if page < 1:
            raise ValueError
    except (TypeError, ValueError):
        errors["page"] = "Must be a positive integer."
        page = 1

    try:
        page_size = int(query_params.get("page_size", default_page_size))
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError
    except (TypeError, ValueError):
        errors["page_size"] = f"Must be an integer between 1 and {MAX_PAGE_SIZE}."
        page_size = default_page_size

    if errors:
        raise ValidationError(errors)
    return page, page_size


def paginate_results(queryset, page: int, page_size: int):
    paginator = Paginator(queryset, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage as exc:
        raise ValidationError(
            {
                "page": f"Page {page} is out of range; the last page is {paginator.num_pages}."
            }
        ) from exc
    return page_obj, {
        "page": page_obj.number,
        "page_size": page_size,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
    }


def cursor_params(query_params, *, default_limit=DEFAULT_PAGE_SIZE):
    """Validate the shared cursor pagination parameters used by public lists."""
    try:
        limit = int(query_params.get("limit", default_limit))
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            {"limit": f"Must be an integer between 1 and {MAX_PAGE_SIZE}."}
        ) from exc
    return query_params.get("cursor", "").strip(), limit


def _filter_fingerprint(query_params):
    filters = {
        key: query_params.getlist(key)
        for key in sorted(query_params)
        if key not in {"cursor", "limit"}
    }
    encoded = json.dumps(filters, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def paginate_cursor_results(
    queryset, request, *, default_limit=DEFAULT_PAGE_SIZE, cursor_scope=""
):
    """Return a stable, forward-only page ordered by ``-created_at, -pk``.

    The signed cursor also binds the active filters, preventing callers from
    accidentally continuing a traversal with a different result set.
    """
    cursor, limit = cursor_params(request.query_params, default_limit=default_limit)
    fingerprint = _filter_fingerprint(request.query_params)
    if cursor:
        try:
            payload = signing.loads(cursor, salt=CURSOR_SALT)
            created_at = parse_datetime(payload["created_at"])
            pk = int(payload["pk"])
            if (
                payload.get("filters") != fingerprint
                or payload.get("scope") != cursor_scope
                or created_at is None
            ):
                raise ValueError
        except (signing.BadSignature, KeyError, TypeError, ValueError) as exc:
            raise ValidationError({"cursor": "Invalid cursor."}) from exc
        queryset = queryset.filter(
            Q(created_at__lt=created_at) | Q(created_at=created_at, pk__lt=pk)
        )

    items = list(queryset.order_by("-created_at", "-pk")[: limit + 1])
    has_more = len(items) > limit
    items = items[:limit]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = signing.dumps(
            {
                "created_at": last.created_at.isoformat(),
                "pk": last.pk,
                "filters": fingerprint,
                "scope": cursor_scope,
            },
            salt=CURSOR_SALT,
            compress=True,
        )
    return items, {
        "limit": limit,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }
