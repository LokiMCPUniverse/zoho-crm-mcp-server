"""End-to-end tests of every tool exposed by the FastMCP server."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from zoho_crm_mcp.server import create_server

from .conftest import build_client, make_config


def _token_handler(request: httpx.Request) -> httpx.Response | None:
    if request.url.host.startswith("accounts"):
        return httpx.Response(200, json={"access_token": "at-test", "expires_in": 3600})
    return None


def _handler_for(
    route: Callable[[httpx.Request], httpx.Response],
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        token = _token_handler(request)
        if token is not None:
            return token
        return route(request)

    return handler


def _tool_result_to_json(result) -> object:
    """Extract structured/JSON output from a FastMCP tool call result."""
    if getattr(result, "structuredContent", None):
        data = result.structuredContent
        # FastMCP wraps plain-dict tool results as {"result": <value>}.
        if isinstance(data, dict) and set(data.keys()) == {"result"}:
            return data["result"]
        return data
    assert result.content, "expected structured or text content"
    text = result.content[0].text  # type: ignore[attr-defined]
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return text


async def _call(tool_name: str, args: dict, route: Callable[[httpx.Request], httpx.Response]):
    client = build_client(make_config(), _handler_for(route))
    server = create_server(client=client)
    try:
        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            return await session.call_tool(tool_name, args)
    finally:
        await client.aclose()


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_records_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/crm/v6/Leads"
        assert request.url.params["page"] == "1"
        assert request.url.params["per_page"] == "50"
        assert request.url.params["fields"] == "id,Last_Name"
        return httpx.Response(200, json={"data": [{"id": "1"}], "info": {"more_records": False}})

    result = await _call(
        "list_records",
        {"module": "Leads", "fields": ["id", "Last_Name"], "page": 1, "per_page": 50},
        route,
    )
    assert not result.isError
    body = _tool_result_to_json(result)
    assert body == {"data": [{"id": "1"}], "info": {"more_records": False}}


@pytest.mark.asyncio
async def test_get_record_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/crm/v6/Leads/123"
        return httpx.Response(200, json={"data": [{"id": "123", "Last_Name": "Doe"}]})

    result = await _call("get_record", {"module": "Leads", "record_id": "123"}, route)
    body = _tool_result_to_json(result)
    assert body["data"][0]["id"] == "123"


@pytest.mark.asyncio
async def test_create_record_happy_single():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/crm/v6/Leads"
        body = json.loads(request.content)
        assert body == {"data": [{"Last_Name": "Doe"}]}
        return httpx.Response(201, json={"data": [{"code": "SUCCESS", "details": {"id": "777"}}]})

    result = await _call(
        "create_record", {"module": "Leads", "data": {"Last_Name": "Doe"}}, route
    )
    body = _tool_result_to_json(result)
    assert body["data"][0]["details"]["id"] == "777"


@pytest.mark.asyncio
async def test_create_record_happy_list():
    def route(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body == {"data": [{"Last_Name": "A"}, {"Last_Name": "B"}]}
        return httpx.Response(201, json={"data": [{"code": "SUCCESS"}, {"code": "SUCCESS"}]})

    result = await _call(
        "create_record",
        {"module": "Leads", "data": [{"Last_Name": "A"}, {"Last_Name": "B"}]},
        route,
    )
    assert not result.isError


@pytest.mark.asyncio
async def test_update_record_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path == "/crm/v6/Leads/123"
        body = json.loads(request.content)
        assert body == {"data": [{"Last_Name": "Doe"}]}
        return httpx.Response(200, json={"data": [{"code": "SUCCESS"}]})

    result = await _call(
        "update_record",
        {"module": "Leads", "record_id": "123", "data": {"Last_Name": "Doe"}},
        route,
    )
    assert not result.isError


@pytest.mark.asyncio
async def test_delete_record_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/crm/v6/Leads/123"
        return httpx.Response(200, json={"data": [{"code": "SUCCESS"}]})

    result = await _call("delete_record", {"module": "Leads", "record_id": "123"}, route)
    assert not result.isError


@pytest.mark.asyncio
async def test_search_records_happy_email():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/crm/v6/Leads/search"
        assert request.url.params["email"] == "jane@example.com"
        return httpx.Response(200, json={"data": [{"id": "1"}]})

    result = await _call(
        "search_records", {"module": "Leads", "email": "jane@example.com"}, route
    )
    assert not result.isError


@pytest.mark.asyncio
async def test_search_records_rejects_multiple_params():
    async def go():
        return await _call(
            "search_records",
            {"module": "Leads", "email": "a@b", "phone": "123"},
            lambda r: httpx.Response(500),
        )

    result = await go()
    # FastMCP should mark the tool call as an error because the tool raised ValueError.
    assert result.isError


@pytest.mark.asyncio
async def test_list_modules_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/crm/v6/settings/modules"
        return httpx.Response(200, json={"modules": [{"api_name": "Leads"}]})

    result = await _call("list_modules", {}, route)
    body = _tool_result_to_json(result)
    assert body["modules"][0]["api_name"] == "Leads"


@pytest.mark.asyncio
async def test_get_module_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/crm/v6/settings/modules/Leads"
        return httpx.Response(200, json={"modules": [{"api_name": "Leads"}]})

    result = await _call("get_module", {"module": "Leads"}, route)
    assert not result.isError


@pytest.mark.asyncio
async def test_list_users_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/crm/v6/users"
        assert request.url.params["type"] == "ActiveUsers"
        return httpx.Response(200, json={"users": [{"id": "1"}]})

    result = await _call("list_users", {"type": "ActiveUsers"}, route)
    body = _tool_result_to_json(result)
    assert body["users"][0]["id"] == "1"


@pytest.mark.asyncio
async def test_coql_query_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/crm/v6/coql"
        body = json.loads(request.content)
        assert body == {"select_query": "select id from Leads limit 1"}
        return httpx.Response(200, json={"data": [{"id": "1"}]})

    result = await _call(
        "coql_query", {"query": "select id from Leads limit 1"}, route
    )
    body = _tool_result_to_json(result)
    assert body["data"][0]["id"] == "1"


@pytest.mark.asyncio
async def test_list_related_records_happy():
    def route(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/crm/v6/Leads/1/Notes"
        return httpx.Response(200, json={"data": [{"id": "n1"}]})

    result = await _call(
        "list_related_records",
        {"module": "Leads", "record_id": "1", "related_list": "Notes"},
        route,
    )
    body = _tool_result_to_json(result)
    assert body["data"][0]["id"] == "n1"


# ---------------------------------------------------------------------------
# 404 paths
# ---------------------------------------------------------------------------


def _not_found(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(404, json={"code": "INVALID_DATA", "message": "record not found"})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool,args",
    [
        ("list_records", {"module": "Missing"}),
        ("get_record", {"module": "Leads", "record_id": "missing"}),
        ("create_record", {"module": "Missing", "data": {"x": 1}}),
        ("update_record", {"module": "Leads", "record_id": "missing", "data": {"x": 1}}),
        ("delete_record", {"module": "Leads", "record_id": "missing"}),
        ("search_records", {"module": "Missing", "email": "a@b"}),
        ("get_module", {"module": "Missing"}),
        ("list_related_records", {"module": "Leads", "record_id": "1", "related_list": "Bad"}),
        ("coql_query", {"query": "select id from Unknown"}),
        ("list_modules", {}),
        ("list_users", {}),
    ],
)
async def test_tool_404_returns_error(tool: str, args: dict):
    result = await _call(tool, args, _not_found)
    assert result.isError
