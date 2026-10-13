"""Driver-neutral contract; native tool schemas remain intact."""
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Protocol

from jsonschema import validate
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class Driver(Protocol):
    async def tools(self) -> list[dict]: ...
    async def call(self, name: str, arguments: dict) -> dict: ...


class MCPDriver:
    def __init__(self, session: ClientSession):
        self.session = session
        self.catalog = None

    async def tools(self):
        if self.catalog is None:
            self.catalog = []
            cursor = None
            seen = set()
            while True:
                page = await self.session.list_tools(cursor=cursor)
                self.catalog.extend(t.model_dump(by_alias=True, exclude_none=True) for t in page.tools)
                cursor = page.nextCursor
                if cursor is None:
                    break
                if cursor in seen:
                    raise RuntimeError("Driver repeated a tools pagination cursor")
                seen.add(cursor)
        return self.catalog

    async def call(self, name, arguments):
        tool = next((t for t in await self.tools() if t['name'] == name), None)
        if tool is None:
            raise ValueError(f"Driver does not advertise tool: {name}")
        validate(arguments, tool['inputSchema'])
        result = await self.session.call_tool(name, arguments)
        return result.model_dump(by_alias=True, exclude_none=True)


@asynccontextmanager
async def connect(config):
    # A replacement driver only needs this contract; MCP is the first transport.
    if config.get('transport', 'stdio') != 'stdio':
        raise ValueError('Only stdio MCP transport is implemented')
    params = StdioServerParameters(command=config['command'], args=config.get('args', []))
    async with stdio_client(params) as streams:
        async with ClientSession(*streams, read_timeout_seconds=timedelta(seconds=config.get('timeout', 30))) as session:
            await session.initialize()
            yield MCPDriver(session)
