#!/usr/bin/env python3

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Same defaults as the old git FastMCP: safe behind Modal (Host header, load-balanced containers).
mcp = FastMCP(
    "codemcp",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

__all__ = [
    "mcp",
]
