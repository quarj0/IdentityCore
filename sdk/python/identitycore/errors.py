from typing import Any, Optional


class IdentityCoreError(Exception):
    """Base exception for IdentityCore SDK errors."""


class IdentityCoreConnectionError(IdentityCoreError):
    """Raised when IdentityCore cannot be reached."""


class IdentityCoreTimeoutError(IdentityCoreConnectionError):
    """Raised when an IdentityCore request exceeds its timeout."""


class IdentityCoreAPIError(IdentityCoreError):
    """Raised when IdentityCore returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "request_failed",
        status: int = 500,
        request_id: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.request_id = request_id
        self.details = details or {}

