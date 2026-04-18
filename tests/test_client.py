"""Tests for ZohoClient HTTP behavior."""

from __future__ import annotations

import httpx
import pytest

from zoho_crm_mcp.exceptions import APIError, AuthenticationError, NotFoundError, RateLimitError

from .conftest import build_client, make_config


def _token_response() -> httpx.Response:
    return httpx.Response(200, json={"access_token": "at-new", "expires_in": 3600})


@pytest.mark.asyncio
async def test_get_attaches_auth_header_and_returns_json():
    seen: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return _token_response()
        seen["api"] = request
        return httpx.Response(200, json={"data": [{"id": "1"}]})

    client = build_client(make_config(), handler)
    try:
        result = await client.get("/Leads")
    finally:
        await client.aclose()

    assert result == {"data": [{"id": "1"}]}
    assert seen["api"].headers["Authorization"] == "Zoho-oauthtoken at-new"
    assert seen["api"].url == httpx.URL("https://www.zohoapis.com/crm/v6/Leads")


@pytest.mark.asyncio
async def test_401_triggers_single_token_refresh_and_retry():
    tokens = iter(["at-stale", "at-fresh"])
    api_calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return httpx.Response(200, json={"access_token": next(tokens), "expires_in": 3600})
        api_calls.append(request.headers["Authorization"])
        if len(api_calls) == 1:
            return httpx.Response(401, json={"code": "INVALID_TOKEN"})
        return httpx.Response(200, json={"data": [{"id": "1"}]})

    client = build_client(make_config(), handler)
    try:
        result = await client.get("/Leads")
    finally:
        await client.aclose()

    assert result == {"data": [{"id": "1"}]}
    assert api_calls == ["Zoho-oauthtoken at-stale", "Zoho-oauthtoken at-fresh"]


@pytest.mark.asyncio
async def test_401_after_refresh_still_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return _token_response()
        return httpx.Response(401, json={"code": "INVALID_TOKEN"})

    client = build_client(make_config(), handler)
    try:
        with pytest.raises(AuthenticationError):
            await client.get("/Leads")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_429_raises_rate_limit_with_retry_after():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return _token_response()
        return httpx.Response(429, json={"code": "LIMIT_EXCEEDED"}, headers={"Retry-After": "42"})

    client = build_client(make_config(), handler)
    try:
        with pytest.raises(RateLimitError) as exc_info:
            await client.get("/Leads")
    finally:
        await client.aclose()

    assert exc_info.value.retry_after == 42.0


@pytest.mark.asyncio
async def test_404_raises_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return _token_response()
        return httpx.Response(404, json={"code": "INVALID_DATA"})

    client = build_client(make_config(), handler)
    try:
        with pytest.raises(NotFoundError):
            await client.get("/Leads/missing")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_generic_error_raises_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return _token_response()
        return httpx.Response(500, json={"code": "INTERNAL_ERROR"})

    client = build_client(make_config(), handler)
    try:
        with pytest.raises(APIError) as exc_info:
            await client.get("/Leads")
    finally:
        await client.aclose()
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_204_returns_none():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return _token_response()
        return httpx.Response(204)

    client = build_client(make_config(), handler)
    try:
        assert await client.delete("/Leads/1") is None
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_post_sends_json_body():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host.startswith("accounts"):
            return _token_response()
        captured["body"] = request.content.decode()
        return httpx.Response(201, json={"data": [{"code": "SUCCESS"}]})

    client = build_client(make_config(), handler)
    try:
        await client.post("/Leads", json={"data": [{"Last_Name": "Doe"}]})
    finally:
        await client.aclose()
    assert '"Last_Name"' in captured["body"]  # body sent as JSON
