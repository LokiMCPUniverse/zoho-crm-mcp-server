"""OAuth2 refresh-token exchange with in-memory caching."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx

from .config import ZohoConfig
from .exceptions import AuthenticationError


@dataclass
class _CachedToken:
    access_token: str
    expires_at: float


class ZohoAuth:
    """Manages access-token lifecycle for the Zoho CRM API.

    The refresh-token grant is used to obtain an access token which is cached
    for its returned lifetime (or 1 hour when the server omits ``expires_in``),
    minus a 60-second safety buffer. Concurrent callers share a single
    refresh using an ``asyncio.Lock``.
    """

    _DEFAULT_TTL = 3600.0
    _SAFETY_BUFFER = 60.0

    def __init__(self, config: ZohoConfig, http_client: httpx.AsyncClient) -> None:
        self._config = config
        self._http = http_client
        self._lock = asyncio.Lock()
        self._cached: _CachedToken | None = None

    def invalidate(self) -> None:
        """Drop any cached access token so the next call forces a refresh."""
        self._cached = None

    async def get_access_token(self, *, force_refresh: bool = False) -> str:
        """Return a valid access token, refreshing if needed."""
        if not force_refresh:
            token = self._valid_cached_token()
            if token is not None:
                return token

        async with self._lock:
            if not force_refresh:
                token = self._valid_cached_token()
                if token is not None:
                    return token
            return await self._refresh_locked()

    def _valid_cached_token(self) -> str | None:
        cached = self._cached
        if cached is None:
            return None
        if cached.expires_at <= time.monotonic():
            return None
        return cached.access_token

    async def _refresh_locked(self) -> str:
        if not self._config.refresh_token or not self._config.client_id or not self._config.client_secret:
            raise AuthenticationError(
                "Zoho OAuth credentials missing: ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, and ZOHO_REFRESH_TOKEN are required."
            )

        data = {
            "refresh_token": self._config.refresh_token,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "grant_type": "refresh_token",
        }

        try:
            response = await self._http.post(self._config.accounts_url, data=data)
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Failed to reach Zoho token endpoint: {exc}") from exc

        if response.status_code != 200:
            raise AuthenticationError(
                f"Zoho token endpoint returned HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise AuthenticationError(f"Zoho token endpoint returned non-JSON body: {exc}") from exc

        if "access_token" not in payload:
            error = payload.get("error") or payload
            raise AuthenticationError(f"Zoho token endpoint did not return an access_token: {error}")

        access_token = str(payload["access_token"])
        ttl = float(payload.get("expires_in", self._DEFAULT_TTL))
        expires_at = time.monotonic() + max(ttl - self._SAFETY_BUFFER, 1.0)
        self._cached = _CachedToken(access_token=access_token, expires_at=expires_at)
        return access_token


__all__ = ["ZohoAuth"]
