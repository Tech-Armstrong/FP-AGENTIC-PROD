"""
Agentic LLM Framework - Tool-Enabled Workflow

What this file does:
This script implements a reactive agent framework that can use tools to accomplish tasks.
It creates a LangGraph-based agent that iteratively calls LLMs and executes tools until completion.

What this file contains:
- Agent class: LangGraph-based agentic workflow with tool binding
  - __init__: Initializes agent with model, tools, and system prompt
  - exists_action: Checks if LLM response contains tool calls
  - call_openai: Invokes LLM with messages and system prompt
  - take_action: Executes tool calls and returns results
  - graph: Compiled StateGraph for agent execution loop
"""

from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import logging
import os
from Financial_Planning.Models.client_data_state import AgentState
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, ToolMessage
from Financial_Planning.Toools.custom_tools import clarify_with_user

load_dotenv()

log = logging.getLogger(__name__)

AZURE_API_KEY=os.getenv('AZURE_API_KEY')
AZURE_API_BASE=os.getenv('AZURE_API_BASE')
AZURE_API_VERSION=os.getenv('AZURE_API_VERSION')
AZURE_DEPLOYMENT_NAME=os.getenv('AZURE_DEPLOYMENT_NAME')

llm_azure = AzureChatOpenAI(
    api_key=AZURE_API_KEY,  # AZURE_API_KEY
    azure_endpoint=AZURE_API_BASE,  # AZURE_API_BASE
    api_version=AZURE_API_VERSION,  # AZURE_API_VERSION
    deployment_name=AZURE_DEPLOYMENT_NAME,  # AZURE_DEPLOYMENT_NAME
    temperature=0  # Optional
) 

class Agent:

    def __init__(self, model, tools: list, system: str, force_first_tool: str | None = None):
        self.system = system
        self._first_turn = True
        self._force_first_tool = force_first_tool
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
        self._model_forced = (
            model.bind_tools(tools, tool_choice=force_first_tool)
            if force_first_tool
            else None
        )

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        log.info("Agent LLM invoke — tools available: %s", list(self.tools.keys()))
        if self._first_turn and self._model_forced is not None:
            log.info("Forcing first-turn tool call: %s", self._force_first_tool)
            message = self._model_forced.invoke(messages)
            self._first_turn = False
        else:
            message = self.model.invoke(messages)
        log.info(
            "Agent LLM response — tool_calls=%s content_preview=%r",
            getattr(message, "tool_calls", []),
            (message.content or "")[:200],
        )
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            log.info("Agent executing tool: %s args=%s", t.get("name"), t.get("args"))
            if not t['name'] in self.tools:
                log.warning("Unknown tool name from LLM: %s", t['name'])
                result = "bad tool name, retry"
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        return {'messages': results}
    