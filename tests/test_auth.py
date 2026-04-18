"""Tests for OAuth2 refresh-token exchange and caching."""

from __future__ import annotations

import httpx
import pytest

from zoho_crm_mcp.auth import ZohoAuth
from zoho_crm_mcp.exceptions import AuthenticationError

from .conftest import make_config


@pytest.mark.asyncio
async def test_refresh_returns_and_caches_token():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        assert request.url == httpx.URL("https://accounts.zoho.com/oauth/v2/token")
        body = request.content.decode()
        assert "refresh_token=rtoken" in body
        assert "client_id=cid" in body
        assert "client_secret=secret" in body
        assert "grant_type=refresh_token" in body
        return httpx.Response(200, json={"access_token": "at-1", "expires_in": 3600})

    config = make_config()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        auth = ZohoAuth(config, http)
        token1 = await auth.get_access_token()
        token2 = await auth.get_access_token()
    assert token1 == "at-1"
    assert token2 == "at-1"
    assert calls["count"] == 1  # cached the second time


@pytest.mark.asyncio
async def test_force_refresh_fetches_new_token():
    tokens = iter(["at-1", "at-2"])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": next(tokens), "expires_in": 3600})

    config = make_config()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        auth = ZohoAuth(config, http)
        assert await auth.get_access_token() == "at-1"
        assert await auth.get_access_token(force_refresh=True) == "at-2"


@pytest.mark.asyncio
async def test_missing_credentials_raise():
    config = make_config(client_id="", client_secret="", refresh_token="")
    async with httpx.AsyncClient() as http:
        auth = ZohoAuth(config, http)
        with pytest.raises(AuthenticationError):
            await auth.get_access_token()


@pytest.mark.asyncio
async def test_http_error_raises_authentication_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    config = make_config()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        auth = ZohoAuth(config, http)
        with pytest.raises(AuthenticationError):
            await auth.get_access_token()


@pytest.mark.asyncio
async def test_missing_access_token_field_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "invalid_client"})

    config = make_config()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        auth = ZohoAuth(config, http)
        with pytest.raises(AuthenticationError):
            await auth.get_access_token()


@pytest.mark.asyncio
async def test_invalidate_forces_new_fetch():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, json={"access_token": f"at-{calls['count']}", "expires_in": 3600})

    config = make_config()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        auth = ZohoAuth(config, http)
        assert await auth.get_access_token() == "at-1"
        auth.invalidate()
        assert await auth.get_access_token() == "at-2"
    assert calls["count"] == 2
