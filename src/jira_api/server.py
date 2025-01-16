import asyncio
import os
import base64
from tempfile import NamedTemporaryFile

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from jira import JIRA

# Initialize server
server = Server("jira-api")

# Environment variables for Jira authentication
JIRA_HOST = os.getenv("JIRA_HOST")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise ValueError(
        "Missing required environment variables: JIRA_HOST, JIRA_EMAIL, and JIRA_API_TOKEN"
    )

# Initialize Jira client
jira = JIRA(
    server=f"https://{JIRA_HOST}",
    basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for JIRA integration."""
    return [
        types.Tool(
            name="delete_issue",
            description="Delete a Jira issue or subtask",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to delete"
                    }
                },
                "required": ["issueKey"]
            }
        ),
        # ... rest of the tools ...
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool execution requests for JIRA operations."""
    try:
        if not arguments:
            raise ValueError("Arguments are required")

        # ... rest of the implementation ...

        raise ValueError(f"Unknown tool: {name}")
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Operation failed: {str(e)}",
            isError=True
        )]

async def main():
    """Run the JIRA MCP server using stdin/stdout streams."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-api",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())