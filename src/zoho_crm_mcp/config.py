"""Configuration for the Zoho CRM MCP server."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REGION_API_HOSTS: dict[str, str] = {
    "com": "https://www.zohoapis.com",
    "eu": "https://www.zohoapis.eu",
    "in": "https://www.zohoapis.in",
    "com.au": "https://www.zohoapis.com.au",
    "jp": "https://www.zohoapis.jp",
}

_REGION_ACCOUNTS_HOSTS: dict[str, str] = {
    "com": "https://accounts.zoho.com",
    "eu": "https://accounts.zoho.eu",
    "in": "https://accounts.zoho.in",
    "com.au": "https://accounts.zoho.com.au",
    "jp": "https://accounts.zoho.jp",
}


class ZohoConfig(BaseSettings):
    """Runtime configuration sourced from the ``ZOHO_`` env namespace."""

    model_config = SettingsConfigDict(
        env_prefix="ZOHO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    client_id: str = Field(default="", description="Zoho OAuth2 client id")
    client_secret: str = Field(default="", description="Zoho OAuth2 client secret")
    refresh_token: str = Field(default="", description="Zoho OAuth2 refresh token")
    region: str = Field(default="com", description="Zoho data-center region (com, eu, in, com.au, jp)")
    timeout: float = Field(default=30.0, ge=1.0, le=600.0, description="HTTP timeout in seconds")

    @field_validator("region")
    @classmethod
    def _validate_region(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in _REGION_API_HOSTS:
            valid = ", ".join(sorted(_REGION_API_HOSTS))
            raise ValueError(f"Unsupported Zoho region '{value}'. Valid options: {valid}")
        return normalized

    @property
    def api_base_url(self) -> str:
        """Base URL for the Zoho CRM v6 API in the configured region."""
        return f"{_REGION_API_HOSTS[self.region]}/crm/v6"

    @property
    def accounts_url(self) -> str:
        """OAuth2 token endpoint for the configured region."""
        return f"{_REGION_ACCOUNTS_HOSTS[self.region]}/oauth/v2/token"


__all__ = ["ZohoConfig"]
