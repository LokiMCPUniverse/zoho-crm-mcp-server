"""Zoho CRM MCP Server - Model Context Protocol server for Zoho CRM integration."""

from __future__ import annotations

__version__ = "0.1.0"


def main() -> None:
    """Entry point for the ``zoho-crm-mcp`` console script."""
    from .server import run

    run()


__all__ = ["__version__", "main"]
