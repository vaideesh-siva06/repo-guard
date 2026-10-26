from llm.prompts import system_prompts
from llm.tools import web_search, read_page, read_file
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
import uuid
from langgraph.checkpoint.memory import InMemorySaver
from mcp_servers.fileMCPServer import FilesystemMCP
class CodingAgent:
    def __init__(self):
        self.coding_model = ChatOllama(model="qwen3-coder")
        self.tools = [web_search, read_page]
        self.memory = InMemorySaver()
        self.conversation_id = uuid.uuid4()
        self.config = {"configurable": {"thread_id": self.conversation_id}}
        self.file_system = FilesystemMCP()

        self.agent = self._create_agent(self.coding_model, system_prompts["CODING"], tools=self.tools)

    async def start(self):
        self.file_tools = await self.file_system.start()
        self.tools.extend(self.file_tools)

        self.agent = self._create_agent(
            self.coding_model,
            system_prompts["CODING"],
            tools=self.tools,
        )

        print("TOOLS")
        print(self.tools)

        return self

    def _create_agent(self, model, agent_system_prompt: str, tools):
        return create_agent(
            model=model,
            system_prompt=agent_system_prompt,
            tools=tools,
            checkpointer=self.memory
        )

    async def close(self):
        await self.file_system.close()
