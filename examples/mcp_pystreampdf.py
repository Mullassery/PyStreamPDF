"""Example: PyStreamPDF MCP 2.0 Integration

By default the connector binds to 127.0.0.1 with no cross-origin access and
read-only permissions. Pass allow_remote=True (and review the security
implications first — this connector has no authentication of its own)
if you genuinely need to expose it beyond localhost.
"""

import asyncio
from pystreampdf._mcp_connector import PDFProcessor

async def main():
    # Initialize with MCP 2.0 support
    engine = PDFProcessor()

    # Start MCP connector (loopback-only by default; see docstring above)
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
