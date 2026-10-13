"""A real MCP server with in-memory state, NOT a desktop simulator."""
from mcp.server.fastmcp import FastMCP

server = FastMCP('test-fixture')
state = {'text': ''}

@server.tool()
def inspect() -> dict[str, str]:
    """Read the fixture state."""
    return dict(state)

@server.tool()
def type_text(text: str) -> dict[str, bool]:
    """Set the fixture text."""
    state['text'] = text
    return {'delivered': True}

@server.tool()
def fail() -> str:
    raise ValueError('fixture error')

if __name__ == '__main__':
    server.run(transport='stdio')
