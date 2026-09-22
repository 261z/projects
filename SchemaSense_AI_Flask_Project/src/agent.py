from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from openai import OpenAI

from src.config import Settings, get_settings
from src.guardrails import check_input
from src.prompts import SYSTEM_PROMPT
from src.tools.schema_tools import OPENAI_TOOL_DEFINITIONS, SchemaTools


class AgentState(TypedDict, total=False):
    messages: list[dict[str, Any]]
    user_query: str
    pending_tool_calls: list[dict[str, Any]]
    tool_count: int
    tool_trace: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    diagram: str | None
    final_answer: str
    blocked: bool


class SchemaAnalysisAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.require_runtime_keys()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.tools = SchemaTools(self.settings)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("guardrails", self._guardrail_node)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tool_node)
        workflow.add_edge(START, "guardrails")
        workflow.add_conditional_edges(
            "guardrails",
            lambda state: "blocked" if state.get("blocked") else "continue",
            {"blocked": END, "continue": "agent"},
        )
        workflow.add_conditional_edges(
            "agent",
            lambda state: "tools" if state.get("pending_tool_calls") else "done",
            {"tools": "tools", "done": END},
        )
        workflow.add_edge("tools", "agent")
        return workflow.compile()

    def _guardrail_node(self, state: AgentState) -> dict:
        result = check_input(state["user_query"])
        if result.allowed:
            return {"blocked": False}
        return {
            "blocked": True,
            "final_answer": result.safe_message or "This request cannot be processed.",
            "pending_tool_calls": [],
        }

    def _agent_node(self, state: AgentState) -> dict:
        tool_count = state.get("tool_count", 0)
        request: dict[str, Any] = {
            "model": self.settings.openai_chat_model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *state["messages"]],
        }

        is_diagram_request = "diagram" in state["user_query"].lower()

        if tool_count < self.settings.max_tool_calls:
            request["tools"] = OPENAI_TOOL_DEFINITIONS

            if is_diagram_request:
                if state.get("diagram"):
                    request["tool_choice"] = "none"
                elif tool_count == 0:
                    request["tool_choice"] = {
                        "type": "function",
                        "function": {"name": "search_metadata"},
                    }
                else:
                    request["tool_choice"] = {
                        "type": "function",
                        "function": {"name": "generate_er_diagram"},
                    }
            else:
                request["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**request)
        message = response.choices[0].message
        serialized = message.model_dump(exclude_none=True)
        pending = [tool_call.model_dump() for tool_call in (message.tool_calls or [])]
        final_answer = message.content or ""

        if not pending and state.get("diagram"):
            final_answer = (
                "Here is the verified ER diagram. "
                "The diagram is rendered below using validated metadata."
            )

        if not pending and not final_answer:
            final_answer = "I could not produce a grounded answer from the available metadata."
            
        return {
            "messages": [*state["messages"], serialized],
            "pending_tool_calls": pending,
            "final_answer": final_answer if not pending else "",
        }

    def _tool_node(self, state: AgentState) -> dict:
        messages = list(state["messages"])
        trace = list(state.get("tool_trace", []))
        sources = list(state.get("sources", []))
        diagram = state.get("diagram")
        tool_count = state.get("tool_count", 0)

        for tool_call in state.get("pending_tool_calls", []):
            name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"].get("arguments") or "{}")
            try:
                result = self._execute_tool(name, arguments)
                status = "success"
            except Exception as exc:  # Tool errors are returned to the model safely.
                result = {"error": type(exc).__name__, "message": str(exc)}
                status = "error"

            if name == "search_metadata":
                for item in result.get("results", []):
                    if not any(
                        source.get("qualified_name") == item.get("qualified_name")
                        for source in sources
                    ):
                        sources.append(item)
            if name == "generate_er_diagram" and result.get("validated"):
                diagram = result.get("mermaid")

            trace.append(
                {
                    "tool": name,
                    "status": status,
                    "summary": self._safe_tool_summary(name, result),
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result),
                }
            )
            tool_count += 1

        return {
            "messages": messages,
            "pending_tool_calls": [],
            "tool_count": tool_count,
            "tool_trace": trace,
            "sources": sources,
            "diagram": diagram,
        }

    def _execute_tool(self, name: str, arguments: dict) -> dict:
        if name == "search_metadata":
            return self.tools.search_metadata(**arguments)
        if name == "get_relationships":
            return self.tools.get_relationships(**arguments)
        if name == "generate_er_diagram":
            return self.tools.generate_er_diagram(**arguments)
        raise ValueError(f"Unsupported tool: {name}")

    @staticmethod
    def _safe_tool_summary(name: str, result: dict) -> str:
        if result.get("error"):
            return f"{name} returned a controlled error."
        if name == "search_metadata":
            names = [item["qualified_name"] for item in result.get("results", [])]
            return f"Retrieved {len(names)} table(s): {', '.join(names) or 'none'}."
        if name == "get_relationships":
            return (
                f"Verified {len(result.get('relationships', []))} relationship(s) across "
                f"{len(result.get('tables', []))} table(s)."
            )
        if name == "generate_er_diagram":
            return f"Generated a validated ER diagram for {len(result.get('tables', []))} table(s)."
        return f"Completed {name}."

    def invoke(self, user_query: str, chat_history: list[dict]) -> AgentState:
        messages = [
            {"role": item["role"], "content": item["content"]}
            for item in chat_history[-10:]
            if item.get("role") in {"user", "assistant"}
        ]
        messages.append({"role": "user", "content": user_query})
        initial: AgentState = {
            "messages": messages,
            "user_query": user_query,
            "pending_tool_calls": [],
            "tool_count": 0,
            "tool_trace": [],
            "sources": [],
            "diagram": None,
            "final_answer": "",
            "blocked": False,
        }
        return self.graph.invoke(initial)

