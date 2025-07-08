[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/lokimcpuniverse-zoho-crm-mcp-server-badge.png)](https://mseep.ai/app/lokimcpuniverse-zoho-crm-mcp-server)

# Zoho CRM MCP Server

<div align="center">

# Zoho Crm Mcp Server

[![GitHub stars](https://img.shields.io/github/stars/LokiMCPUniverse/zoho-crm-mcp-server?style=social)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/LokiMCPUniverse/zoho-crm-mcp-server?style=social)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/network)
[![GitHub watchers](https://img.shields.io/github/watchers/LokiMCPUniverse/zoho-crm-mcp-server?style=social)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/watchers)

[![License](https://img.shields.io/github/license/LokiMCPUniverse/zoho-crm-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/blob/main/LICENSE)
[![Issues](https://img.shields.io/github/issues/LokiMCPUniverse/zoho-crm-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/LokiMCPUniverse/zoho-crm-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/pulls)
[![Last Commit](https://img.shields.io/github/last-commit/LokiMCPUniverse/zoho-crm-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/commits)

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-DC143C?style=for-the-badge)](https://modelcontextprotocol.io)

[![Commit Activity](https://img.shields.io/github/commit-activity/m/LokiMCPUniverse/zoho-crm-mcp-server?style=flat-square)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/pulse)
[![Code Size](https://img.shields.io/github/languages/code-size/LokiMCPUniverse/zoho-crm-mcp-server?style=flat-square)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server)
[![Contributors](https://img.shields.io/github/contributors/LokiMCPUniverse/zoho-crm-mcp-server?style=flat-square)](https://github.com/LokiMCPUniverse/zoho-crm-mcp-server/graphs/contributors)

</div>

A Model Context Protocol (MCP) server for integrating Zoho CRM with GenAI applications.

## Overview

Complete CRM suite integration

## Features

- Comprehensive Zoho CRM API coverage
- Multiple authentication methods
- Enterprise-ready with rate limiting
- Full error handling and retry logic
- Async support for better performance

## Installation

```bash
pip install zoho-crm-mcp-server
```

Or install from source:

```bash
git clone https://github.com/asklokesh/zoho-crm-mcp-server.git
cd zoho-crm-mcp-server
pip install -e .
```

## Configuration

Create a `.env` file or set environment variables according to Zoho CRM API requirements.

## Quick Start

```python
from zoho_crm_mcp import ZohoCrmMCPServer

# Initialize the server
server = ZohoCrmMCPServer()

# Start the server
server.start()
```

## License

MIT License - see LICENSE file for details
