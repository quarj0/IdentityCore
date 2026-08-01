from django.core.paginator import EmptyPage, Paginator
from rest_framework.exceptions import ValidationError

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


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
