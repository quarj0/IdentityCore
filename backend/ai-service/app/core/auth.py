from typing import Annotated

from fastapi import Header, HTTPException, status

from app.settings import get_settings


def enforce_internal_token(
    x_internal_token: Annotated[str | None, Header()] = None,
) -> None:
    settings = get_settings()
    if settings.shared_token and x_internal_token != settings.shared_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized internal AI service request.",
        )
