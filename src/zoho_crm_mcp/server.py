"""FastMCP server exposing Zoho CRM v6 tools."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP

from .auth import ZohoAuth
from .client import ZohoClient
from .config import ZohoConfig


@dataclass
class ZohoContext:
    """Runtime context shared with every tool via FastMCP's lifespan."""

    client: ZohoClient


def _get_client(ctx: Context) -> ZohoClient:
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, ZohoContext):
        raise RuntimeError("Zoho lifespan context is not initialised")
    return lifespan_ctx.client


def create_server(client: ZohoClient | None = None) -> FastMCP:
    """Build a FastMCP server wired to Zoho CRM.

    Pass ``client`` to inject a pre-built client (useful for tests). Otherwise
    a fresh :class:`ZohoClient` is constructed at server startup from
    environment-based configuration.
    """

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[ZohoContext]:
        if client is not None:
            yield ZohoContext(client=client)
            return

        config = ZohoConfig()
        http_client = httpx.AsyncClient(timeout=config.timeout)
        auth = ZohoAuth(config, http_client)
        owned_client = ZohoClient(config, http_client=http_client, auth=auth)
        try:
            yield ZohoContext(client=owned_client)
        finally:
            await http_client.aclose()

    mcp = FastMCP(
        name="zoho-crm-mcp",
        instructions=(
            "Tools to read and modify records in Zoho CRM v6. "
            "All calls authenticate via an OAuth2 refresh token."
        ),
        lifespan=lifespan,
    )

    @mcp.tool()
    async def list_records(
        ctx: Context,
        module: str,
        fields: list[str] | None = None,
        page: int = 1,
        per_page: int = 200,
    ) -> dict[str, Any]:
        """List records from a Zoho CRM module.

        Args:
            module: API name of the module (e.g. ``Leads``, ``Contacts``).
            fields: Optional subset of API field names to return.
            page: Page number, 1-indexed.
            per_page: Page size (max 200 per Zoho CRM v6).
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if fields:
            params["fields"] = ",".join(fields)
        client = _get_client(ctx)
        result = await client.get(f"/{module}", params=params)
        return result if isinstance(result, dict) else {"data": result}

    @mcp.tool()
    async def get_record(ctx: Context, module: str, record_id: str) -> dict[str, Any]:
        """Fetch a single record by id from the given module."""
        client = _get_client(ctx)
        result = await client.get(f"/{module}/{record_id}")
        return result if isinstance(result, dict) else {"data": result}

    @mcp.tool()
    async def create_record(
        ctx: Context,
        module: str,
        data: dict[str, Any] | list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create one or more records in the given module."""
        records = data if isinstance(data, list) else [data]
        body = {"data": records}
        client = _get_client(ctx)
        result = await client.post(f"/{module}", json=body)
        return result if isinstance(result, dict) else {"data": result}

    @mcp.tool()
    async def update_record(
        ctx: Context,
        module: str,
        record_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a single record with a partial payload."""
        body = {"data": [data]}
        client = _get_client(ctx)
        result = await client.put(f"/{module}/{record_id}", json=body)
        return result if isinstance(result, dict) else {"data": result}

    @mcp.tool()
    async def delete_record(ctx: Context, module: str, record_id: str) -> dict[str, Any]:
        """Delete a single record by id."""
        client = _get_client(ctx)
        result = await client.delete(f"/{module}/{record_id}")
        return result if isinstance(result, dict) else {"data": result}

    @mcp.tool()
    async def search_records(
        ctx: Context,
        module: str,
        criteria: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        word: str | None = None,
        page: int = 1,
        per_page: int = 200,
    ) -> dict[str, Any]:
        """Search records by ``criteria``, ``email``, ``phone``, or ``word``.

        Exactly one of the four search parameters must be supplied.
        """
        provided = [name for name, value in (
            ("criteria", criteria),
            ("email", email),
            ("phone", phone),
            ("word", word),
        ) if value]
        if len(provided) != 1:
            raise ValueError(
                "Provide exactly one of: criteria, email, phone, word. "
                f"Got: {provided or 'none'}"
            )

        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if criteria:
            params["criteria"] = criteria
        if email:
            params["email"] = email
        if phone:
            params["phone"] = phone
        if word:
            params["word"] = word

        client = _get_client(ctx)
        result = await client.get(f"/{module}/search", params=params)
        return result if isinstance(result, dict) else {"data": result}

    @mcp.tool()
    async def list_modules(ctx: Context) -> dict[str, Any]:
        """List every available module in the connected Zoho CRM org."""
        client = _get_client(ctx)
        result = await client.get("/settings/modules")
        return result if isinstance(result, dict) else {"modules": result}

    @mcp.tool()
    async def get_module(ctx: Context, module: str) -> dict[str, Any]:
        """Fetch metadata for a single module."""
        client = _get_client(ctx)
        result = await client.get(f"/settings/modules/{module}")
        return result if isinstance(result, dict) else {"modules": result}

    @mcp.tool()
    async def list_users(ctx: Context, type: str = "AllUsers") -> dict[str, Any]:
        """List users visible to the authenticated principal.

        Args:
            type: Zoho user filter, e.g. ``AllUsers``, ``ActiveUsers``,
                  ``DeactiveUsers``, ``AdminUsers``.
        """
        client = _get_client(ctx)
        result = await client.get("/users", params={"type": type})
        return result if isinstance(result, dict) else {"users": result}

    @mcp.tool()
    async def coql_query(ctx: Context, query: str) -> dict[str, Any]:
        """Run a COQL ``SELECT`` query against Zoho CRM."""
        client = _get_client(ctx)
        result = await client.post("/coql", json={"select_query": query})
        return result if isinstance(result, dict) else {"data": result}

    @mcp.tool()
    async def list_related_records(
        ctx: Context,
        module: str,
        record_id: str,
        related_list: str,
        page: int = 1,
        per_page: int = 200,
    ) -> dict[str, Any]:
        """List records from a related list of a parent record."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        client = _get_client(ctx)
        result = await client.get(f"/{module}/{record_id}/{related_list}", params=params)
        return result if isinstance(result, dict) else {"data": result}

    return mcp


def run() -> None:
    """Run the server over stdio (used by the console script)."""
    create_server().run()


__all__ = ["create_server", "run", "ZohoContext"]
