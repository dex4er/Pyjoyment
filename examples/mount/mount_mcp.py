from Pyjoyment.Lite import *

from mcp.server.mcpserver import MCPServer


# A server of the MCP SDK with a tool, whose transport of Streamable HTTP is an ASGI application of Starlette, under
# /mcp/, as uv run --group servers python examples/mount/mount_mcp.py daemon serves it on http://localhost:3000/mcp/
mcp = MCPServer('Pyjoyment')


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


plugin('Mount', {'/mcp': mcp.streamable_http_app(streamable_http_path='/')})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
