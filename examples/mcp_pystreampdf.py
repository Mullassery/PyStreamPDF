"""Example: PyStreamPDF MCP 2.0 Integration

By default the connector binds to 127.0.0.1 with no cross-origin access and
read-only permissions. To expose it beyond localhost, pass allow_remote=True
with a non-empty auth_token: DAB stays on loopback and a stdlib reverse proxy
requires ``Authorization: Bearer <token>`` before forwarding. That proxy still
speaks plaintext HTTP, so terminate TLS in a real reverse proxy in front of it
for untrusted networks.
"""

import asyncio

from pystreampdf._mcp_connector import PDFProcessor


async def main():
    # Initialize with MCP 2.0 support
    engine = PDFProcessor()

    # Start MCP connector (loopback-only by default; see docstring above).
    # For remote exposure:
    # mcp_url = engine.start_mcp_connector(
    #     host="0.0.0.0", allow_remote=True,
    #     auth_token="replace-with-a-long-random-token",
    # )
    mcp_url = engine.start_mcp_connector()
    print(f"✓ PyStreamPDF MCP 2.0 running at {mcp_url}")

    # Use the tools
    # Example: handler = YourHandler(engine)
    # result = await handler.your_tool(...)

    # Keep server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        engine.stop_mcp_connector()
        print("✓ MCP server stopped")

if __name__ == "__main__":
    asyncio.run(main())
