from langchain.mcp import MCPAdapter
from config import get_project_root

class FilesystemMCP:
    def __init__(self):
        self.adapter = None
        self.tools = []

    async def start(self):
        config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        str(get_project_root()),
                    ],
                }
            }
        }

        self.adapter = MCPAdapter(config)
        await self.adapter.__aenter__()
        self.tools = await self.adapter.list_tools()
        return self.tools

    async def close(self):
        if self.adapter:
            await self.adapter.__aexit__(None, None, None)