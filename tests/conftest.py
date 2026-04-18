"""Shared fixtures for zoho-crm-mcp tests."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from zoho_crm_mcp.auth import ZohoAuth
from zoho_crm_mcp.client import ZohoClient
from zoho_crm_mcp.config import ZohoConfig


def make_config(**overrides) -> ZohoConfig:
    base = {
        "client_id": "cid",
        "client_secret": "secret",
        "refresh_token": "rtoken",
        "region": "com",
        "timeout": 5.0,
    }
    base.update(overrides)
    return ZohoConfig(**base)


@pytest.fixture
def config() -> ZohoConfig:
    return make_config()


def build_client(config: ZohoConfig, handler: Callable[[httpx.Request], httpx.Response]) -> ZohoClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, timeout=config.timeout)
    auth = ZohoAuth(config, http)
    return ZohoClient(config, http_client=http, auth=auth)
