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
import os
from Financial_Planning.Models.client_data_state import AgentState
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, ToolMessage
from Financial_Planning.Toools.custom_tools import clarify_with_user

load_dotenv() 

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

    def __init__(self, model, tools: list, system: str):
        self.system = system
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

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}
    