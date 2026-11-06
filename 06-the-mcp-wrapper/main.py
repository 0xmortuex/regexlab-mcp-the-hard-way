"""Module 06: launch the server over stdio, list its tools, call them, read its errors."""

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")


async def run() -> None:
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        init = await session.initialize()
        assert init.server_info.name == "regexlab-tutorial"
        tools = (await session.list_tools()).tools
        assert {t.name for t in tools} == {"test_regex", "explain_regex", "check_backtracking"}
        # the docstring is the only documentation the model gets
        assert all(t.description and "regex" in t.description.lower() for t in tools)

        res = await session.call_tool("test_regex", {"pattern": r"^\d+$", "subject": ["12", "12\n"]})
        text = res.content[0].text
        print(text)
        assert not res.is_error
        assert "ENGINES DIFFER" in text           # python accepts "12\n", javascript does not

        res = await session.call_tool("explain_regex", {"pattern": r"(a|b)+"})
        assert "start of capture group 1" in res.content[0].text

        res = await session.call_tool("check_backtracking", {"pattern": r"(a+)+$"})
        print(res.content[0].text)
        assert res.content[0].text.startswith("EXPONENTIAL")

        # errors the agent can act on arrive intact
        res = await session.call_tool("explain_regex", {"pattern": "(oops"})
        print(res.content[0].text)
        assert res.is_error and "missing )" in res.content[0].text
        res = await session.call_tool("test_regex", {"pattern": "(?<y>a)", "subject": "a"})
        assert "python: ERROR" in res.content[0].text   # one engine failing is a result, not a crash


if __name__ == "__main__":
    asyncio.run(run())
    print("\nmodule 06 ok")
