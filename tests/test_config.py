"""Tests for ZohoConfig."""

from __future__ import annotations

import pytest

from zoho_crm_mcp.config import ZohoConfig


def test_default_region_is_com():
    config = ZohoConfig(client_id="a", client_secret="b", refresh_token="c")
    assert config.region == "com"
    assert config.api_base_url == "https://www.zohoapis.com/crm/v6"
    assert config.accounts_url == "https://accounts.zoho.com/oauth/v2/token"


@pytest.mark.parametrize(
    "region,api_host,accounts_host",
    [
        ("eu", "https://www.zohoapis.eu/crm/v6", "https://accounts.zoho.eu/oauth/v2/token"),
        ("in", "https://www.zohoapis.in/crm/v6", "https://accounts.zoho.in/oauth/v2/token"),
        ("com.au", "https://www.zohoapis.com.au/crm/v6", "https://accounts.zoho.com.au/oauth/v2/token"),
        ("jp", "https://www.zohoapis.jp/crm/v6", "https://accounts.zoho.jp/oauth/v2/token"),
    ],
)
def test_region_urls(region, api_host, accounts_host):
    config = ZohoConfig(client_id="a", client_secret="b", refresh_token="c", region=region)
    assert config.api_base_url == api_host
    assert config.accounts_url == accounts_host


def test_region_rejects_unknown():
    with pytest.raises(ValueError):
        ZohoConfig(client_id="a", client_secret="b", refresh_token="c", region="us")


def test_env_prefix(monkeypatch):
    monkeypatch.setenv("ZOHO_CLIENT_ID", "envcid")
    monkeypatch.setenv("ZOHO_CLIENT_SECRET", "envsecret")
    monkeypatch.setenv("ZOHO_REFRESH_TOKEN", "envrtoken")
    monkeypatch.setenv("ZOHO_REGION", "eu")
    monkeypatch.setenv("ZOHO_TIMEOUT", "15")
    config = ZohoConfig()
    assert config.client_id == "envcid"
    assert config.client_secret == "envsecret"
    assert config.refresh_token == "envrtoken"
    assert config.region == "eu"
    assert config.timeout == 15.0
