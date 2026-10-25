from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from typing import Any, Annotated, TypedDict
from langgraph.checkpoint.memory import InMemorySaver
import uuid
from llm.prompts import system_prompts
from llm.tools import web_search, read_page
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.messages import AIMessageChunk, ToolCallChunk
from typing import Literal
from langchain.messages import SystemMessage, HumanMessage, AIMessage
import json
from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from llm.coding_agent import CodingAgent

TOOL_STATUS = {
    "web_search": "Searching the web...",
    "list_files": "Looking through your project files...",
    "read_file": "Reading a file...",
    "edit_file": "Editing a file...",
    "write_file": "Writing a file...",
    "read_page": "Reading a page..."
}

class Decision(BaseModel):
    next: Literal["CODING", "DESIGN", "GENERAL", "FINISH"]
    task: str = Field(
        default="",
        description="Only when delegating: the full instruction for the specialist. Empty for FINISH.",
    )
    answer: str = Field(
        default="",
        description="Only for FINISH: the final reply to the user. Empty when delegating.",
    )

class State(TypedDict):
    messages: Annotated[list, add_messages]
    next: Literal["GENERAL", "CODING", "DESIGN", "FINISH"]

def route_next(state: State) -> str:
        destination = state.get("next")

        if destination not in {"GENERAL", "CODING", "DESIGN", "FINISH"}:
            raise ValueError(f"Invalid routing destination: {destination!r}")

        return destination

class LLM():

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = ChatOllama(model="qwen3:8b")
        self.coding_model = ChatOllama(model="qwen3-coder")
        self.conversation_id = uuid.uuid4()
        self.tools = [web_search, read_page]
        self.memory = InMemorySaver()
        self.config = {"configurable": {"thread_id": self.conversation_id}}
        self.agent = self._create_agent(self.model, system_prompts["GENERAL"], tools=self.tools)
        self.coding_agent = CodingAgent()
        self.orchestrator_model = self.model.with_structured_output(
            Decision,
            method="json_schema"
        )
        self.design_agent = self._create_agent(self.model, system_prompts["DESIGN"], tools=self.tools)
        self.graph = self._build_graph()
        self.orchestrator_chain = self._build_orchestrator_chain()

    def _create_agent(self, model, agent_system_prompt: str, tools):
        return create_agent(
            model=model,
            system_prompt=agent_system_prompt,
            tools=tools,
            checkpointer=self.memory
        )

    def _build_graph(self):
        graph = StateGraph(State)

        graph.add_node("orchestrator_agent", self.run_orchestrator)
        graph.add_node("coding_agent", self.coding_agent.agent)
        graph.add_node("design_agent", self.design_agent)
        graph.add_node("general_agent", self.agent)

        graph.add_edge(START, "orchestrator_agent")

        graph.add_conditional_edges(
            "orchestrator_agent",
            route_next,
            {
                "GENERAL": "general_agent",
                "CODING": "coding_agent",
                "DESIGN": "design_agent",
                "FINISH": END,
            },
        )

        graph.add_edge("coding_agent", "orchestrator_agent")
        graph.add_edge("design_agent", "orchestrator_agent")
        graph.add_edge("general_agent", "orchestrator_agent")

        return graph.compile(checkpointer=self.memory)

    def _build_orchestrator_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompts["ORCHESTRATOR"]),
            MessagesPlaceholder("messages"),
        ])

        def to_update(decision: Decision) -> dict:
            print(f"[DEBUG] Next agent: {decision.next} | task: {decision.task!r}")
            updates = {"next": decision.next}
            if decision.next == "FINISH":
                updates["messages"] = [AIMessage(content=decision.answer)]
            return updates

        fallback = RunnableLambda(lambda _: {
            "next": "FINISH",
            "messages": [AIMessage(
                content="Sorry, I couldn't decide how to route that. Please rephrase."
            )],
        })

        return (
            prompt
            | self.orchestrator_model
            | RunnableLambda(to_update)
        ).with_retry(
            retry_if_exception_type=(OutputParserException,),
            stop_after_attempt=2,
        ).with_fallbacks(
            [fallback],
            exceptions_to_handle=(OutputParserException,),
        )

    def run_orchestrator(self, state: State):
            # A worker just answered, so the turn is done.
            if isinstance(state["messages"][-1], AIMessage):
                return {"next": "FINISH"}
            return self.orchestrator_chain.invoke({"messages": state["messages"]})

    def invoke(self, query: str) -> dict[str, Any] | str:
        """Allows agent to invoke user query."""

        response = self.graph.invoke({
            "messages": [{"role": "user", "content": query}]
        }, config=self.config)

        return response['messages'][-1].content

    
    def stream(self, query: str):
        streamed = False
        seen_calls = set()

        for ns, mode, chunk in self.graph.stream(
            {"messages": [{"role": "user", "content": query}]},
            config=self.config,
            stream_mode=["messages", "updates"],
            subgraphs=True,
        ):
            inner = bool(ns)  # True for events from inside a worker agent

            if mode == "messages":
                message, metadata = chunk
                if metadata.get("langgraph_node") == "orchestrator_agent":
                    continue
                if isinstance(message, AIMessageChunk) and message.content:
                    streamed = True
                    yield {"type": "message", "content": message.content}
                continue

            # mode == "updates"
            for node_name, update in chunk.items():
                if node_name == "__interrupt__" or not isinstance(update, dict):
                    continue

                msgs = update.get("messages", [])
                msgs = msgs if isinstance(msgs, list) else [msgs]

                # Tool status: fires live from the inner agent, deduped by call id.
                for m in msgs:
                    for call in getattr(m, "tool_calls", None) or []:
                        key = call.get("id") or str(call)
                        print(f"[DEBUG] Tool call: {call['name']} | Args: {call.get('args')}")
                        if key not in seen_calls:
                            seen_calls.add(key)
                            status = TOOL_STATUS.get(
                                call["name"], f"Using {call['name']}..."
                            )

                            yield {
                                "type": "status",
                                "content": f"{status}",
                            }
                    if inner and getattr(m, "type", None) == "tool":
                        yield {"type": "tool_result", "tool": m.name}

                if inner:
                    continue  # the outer update repeats these messages

                # Top-level updates
                if node_name == "orchestrator_agent":
                    if update.get("next") == "FINISH":
                        for m in msgs:
                            if isinstance(m, AIMessage) and m.content:
                                yield {"type": "message", "content": m.content}
                    continue

                # A worker finished: show its answer if no tokens streamed.
                if not streamed:
                    final = next(
                        (m for m in reversed(msgs)
                        if isinstance(m, AIMessage)
                        and m.content
                        and not getattr(m, "tool_calls", None)),
                        None,
                    )
                    if final:
                        yield {"type": "message", "content": final.content}
                streamed = False

client = LLM("Personal")
out = client.agent.invoke({"messages": [("user", "latest Python release")]}, config={"configurable": {"thread_id": "1"}})
for m in out["messages"]:
    print(type(m).__name__, getattr(m, "tool_calls", None))