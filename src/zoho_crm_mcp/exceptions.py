"""Typed exceptions for the Zoho CRM MCP server."""

from __future__ import annotations


class ZohoError(Exception):
    """Base class for all Zoho CRM errors."""


class AuthenticationError(ZohoError):
    """Raised when the OAuth2 refresh-token exchange or access-token use fails."""


class NotFoundError(ZohoError):
    """Raised when a record, module, or resource cannot be found (HTTP 404)."""


class APIError(ZohoError):
    """Raised for non-success HTTP responses that are not handled specifically."""

    def __init__(self, message: str, status_code: int | None = None, payload: object = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class RateLimitError(ZohoError):
    """Raised when Zoho CRM returns HTTP 429 (rate limited)."""

    def __init__(self, message: str = "Zoho CRM rate limit exceeded", retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


__all__ = [
    "ZohoError",
    "AuthenticationError",
    "NotFoundError",
    "APIError",
    "RateLimitError",
]
