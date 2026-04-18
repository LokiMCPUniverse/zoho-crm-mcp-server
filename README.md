# Zoho CRM MCP Server

A Model Context Protocol (MCP) server that exposes the Zoho CRM v6 REST API
as structured tools for LLM agents. Built on FastMCP with async httpx,
pydantic v2 configuration, and an OAuth2 refresh-token flow.

## Features

- OAuth2 refresh-token exchange with in-memory access-token caching (1 hour TTL)
- Automatic retry once on HTTP 401 after forcing a token refresh
- Typed errors (`AuthenticationError`, `NotFoundError`, `RateLimitError`, `APIError`)
- Region-aware endpoints: `com`, `eu`, `in`, `com.au`, `jp`
- Full CRUD for any CRM module, plus search, COQL, module metadata,
  user listing, and related-list traversal

## Requirements

- Python 3.10+
- `mcp>=1.27,<2`
- `httpx>=0.27.1,<1.0.0`
- `pydantic>=2.12`, `pydantic-settings>=2.5.2`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

All settings use the `ZOHO_` env prefix (or a `.env` file):

| Variable              | Default | Description                                          |
| --------------------- | ------- | ---------------------------------------------------- |
| `ZOHO_CLIENT_ID`      | -       | OAuth2 client id                                     |
| `ZOHO_CLIENT_SECRET`  | -       | OAuth2 client secret                                 |
| `ZOHO_REFRESH_TOKEN`  | -       | OAuth2 refresh token                                 |
| `ZOHO_REGION`         | `com`   | One of `com`, `eu`, `in`, `com.au`, `jp`             |
| `ZOHO_TIMEOUT`        | `30`    | HTTP timeout in seconds                              |

## Run

```bash
zoho-crm-mcp
```

Or register it in an MCP-capable client with the stdio command above.

## Tools

| Tool                    | Zoho CRM endpoint                                |
| ----------------------- | ------------------------------------------------ |
| `list_records`          | `GET /crm/v6/{module}`                           |
| `get_record`            | `GET /crm/v6/{module}/{id}`                      |
| `create_record`         | `POST /crm/v6/{module}`                          |
| `update_record`         | `PUT /crm/v6/{module}/{id}`                      |
| `delete_record`         | `DELETE /crm/v6/{module}/{id}`                   |
| `search_records`        | `GET /crm/v6/{module}/search`                    |
| `list_modules`          | `GET /crm/v6/settings/modules`                   |
| `get_module`            | `GET /crm/v6/settings/modules/{module}`          |
| `list_users`            | `GET /crm/v6/users`                              |
| `coql_query`            | `POST /crm/v6/coql`                              |
| `list_related_records`  | `GET /crm/v6/{module}/{id}/{related_list}`       |

## Test

```bash
pytest -x --tb=short
```

## License

MIT
