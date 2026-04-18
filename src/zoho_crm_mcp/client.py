"""Async HTTP client for the Zoho CRM v6 API."""

from __future__ import annotations

from typing import Any

import httpx

from .auth import ZohoAuth
from .config import ZohoConfig
from .exceptions import APIError, AuthenticationError, NotFoundError, RateLimitError


class ZohoClient:
    """Thin async wrapper around ``httpx.AsyncClient`` for Zoho CRM.

    Automatically attaches the ``Authorization: Zoho-oauthtoken ...`` header,
    refreshes the access token once on an HTTP 401 response, and raises typed
    exceptions for 404 and 429.
    """

    def __init__(
        self,
        config: ZohoConfig,
        http_client: httpx.AsyncClient | None = None,
        auth: ZohoAuth | None = None,
    ) -> None:
        self._config = config
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=config.timeout)
        self._auth = auth or ZohoAuth(config, self._http)

    @property
    def config(self) -> ZohoConfig:
        return self._config

    @property
    def auth(self) -> ZohoAuth:
        return self._auth

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> ZohoClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    # HTTP verbs -----------------------------------------------------------------
    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("POST", path, json=json, params=params)

    async def put(
        self,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("PUT", path, json=json, params=params)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._request("DELETE", path, params=params)

    # Internals ------------------------------------------------------------------
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = self._build_url(path)

        response = await self._send(method, url, json=json, params=params, force_refresh=False)
        if response.status_code == 401:
            # Access token may have been revoked or expired out-of-band: refresh once.
            self._auth.invalidate()
            response = await self._send(method, url, json=json, params=params, force_refresh=True)

        return self._handle_response(response)

    async def _send(
        self,
        method: str,
        url: str,
        *,
        json: Any | None,
        params: dict[str, Any] | None,
        force_refresh: bool,
    ) -> httpx.Response:
        access_token = await self._auth.get_access_token(force_refresh=force_refresh)
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Accept": "application/json",
        }
        return await self._http.request(method, url, json=json, params=params, headers=headers)

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._config.api_base_url}{path}"

    def _handle_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        if status == 204:
            return None
        if 200 <= status < 300:
            if not response.content:
                return None
            try:
                return response.json()
            except ValueError as exc:
                raise APIError(f"Zoho returned non-JSON body: {exc}", status_code=status) from exc

        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if status == 401:
            raise AuthenticationError(f"Zoho authentication failed: {payload}")
        if status == 404:
            raise NotFoundError(f"Zoho resource not found: {payload}")
        if status == 429:
            retry_after_header = response.headers.get("Retry-After")
            retry_after: float | None = None
            if retry_after_header is not None:
                try:
                    retry_after = float(retry_after_header)
                except ValueError:
                    retry_after = None
            raise RateLimitError(retry_after=retry_after)
        raise APIError(f"Zoho API error (HTTP {status}): {payload}", status_code=status, payload=payload)


__all__ = ["ZohoClient"]
