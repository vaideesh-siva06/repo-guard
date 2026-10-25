from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from typing import Any, Annotated, TypedDict
from langgraph.checkpoint.memory import InMemorySaver
import uuid
from llm.prompts import system_prompts
from llm.tools import web_search
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.messages import AIMessageChunk, ToolCallChunk

TOOL_STATUS = {
    "web_search": "Searching the web...",
    "list_files": "Looking through your project files...",
    "read_file": "Reading a file...",
    "edit_file": "Editing a file...",
    "write_file": "Writing a file...",
}

class State(TypedDict):
    messages: Annotated[list, add_messages]

class LLM():

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = ChatOllama(model="qwen3:8b", temperature=0)
        self.conversation_id = uuid.uuid4()
        self.system_prompt = system_prompts[self.model_name]
        self.tools = [web_search]
        self.memory = InMemorySaver()
        self.config = {"configurable": {"thread_id": self.conversation_id}}

        self.agent = self._create_agent()

    def _create_agent(self):
        return create_agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=self.tools,
            checkpointer=self.memory
        )


    def invoke(self, query: str) -> dict[str, Any] | str:
        """Allows agent to invoke user query."""

        response = self.agent.invoke({
            "messages": [{"role": "user", "content": query}]
        }, config=self.config)

        return response['messages'][-1].content

    def stream(self, query: str):
        for mode, chunk in self.agent.stream(
            {"messages": [{"role": "user", "content": query}]},
            config=self.config,
            stream_mode=["messages", "updates"],
        ):
            if mode == "messages":
                message, metadata = chunk

                # Stream assistant text as before.
                if isinstance(message, AIMessageChunk) and message.content:
                    yield {
                        "type": "message",
                        "content": message.content,
                    }

                # Show tool calls as progress events.
                if isinstance(message, AIMessageChunk):
                    for tool_call in getattr(message, "tool_calls", []):
                        yield {
                            "type": "status",
                            "content": f"Using tool: {tool_call['name']}",
                        }

            elif mode == "updates":
                for node_name, update in chunk.items():
                    for message in update.get("messages", []):
                        if getattr(message, "tool_calls", None):
                            for call in message.tool_calls:
                                name = call['name']

                                yield {
                                    "type": "status",
                                    "content": TOOL_STATUS.get(
                                        name, f"Using {name}..."
                                    ),
                                }
                        elif getattr(message, "type", None) == "tool":
                            yield {
                                "type": "tool_result",
                                "tool": message.name
                            }


