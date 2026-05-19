"""
LangGraph agent exposed via AG-UI (FastAPI) for CopilotKit.

Run:  python main.py
      (from this directory, with repo-root .env loaded)

CopilotKit frontend connects through Next.js /api/copilotkit → LANGGRAPH_AGENT_URL.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from ag_ui.core import EventType, RunAgentInput, RunErrorEvent
from ag_ui.encoder import EventEncoder
from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from tavily import TavilyClient

# Unbuffered stdout/stderr (python -u equivalent)
os.environ.setdefault("PYTHONUNBUFFERED", "1")

# Load env from repo root (parent of agent/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
    force=True,
)
log = logging.getLogger("agent")

SYSTEM_PROMPT = """You are an AI assistant built for helping users understand their data.

When you give a report about data, use markdown formatting and tables when helpful.
Be concise unless the user asks for more detail.

You receive dashboard context from the app via CopilotKit. Use searchInternet when
the user needs information beyond the dashboard data."""


def _env(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default


def _mask_key(key: str | None) -> str:
    if not key:
        return "<missing>"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def load_azure_config() -> dict[str, str]:
    endpoint = _env(
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_API_BASE",
    )
    api_key = _env("AZURE_OPENAI_API_KEY", "AZURE_API_KEY")
    deployment = _env(
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_DEPLOYMENT_NAME",
        default="gpt-4o",
    )
    api_version = _env(
        "OPENAI_API_VERSION",
        "AZURE_API_VERSION",
        default="2024-08-01-preview",
    )
    return {
        "azure_endpoint": (endpoint or "").rstrip("/"),
        "api_key": api_key or "",
        "azure_deployment": deployment or "gpt-4o",
        "api_version": api_version or "2024-08-01-preview",
    }


def log_azure_config(cfg: dict[str, str]) -> None:
    log.info(
        "Azure config loaded: endpoint=%s deployment=%s api_version=%s api_key=%s",
        cfg["azure_endpoint"] or "<missing>",
        cfg["azure_deployment"],
        cfg["api_version"],
        _mask_key(cfg["api_key"]),
    )


class LoggingAzureChatOpenAI(AzureChatOpenAI):
    """Azure LLM wrapper that logs and re-raises on failure."""

    async def ainvoke(self, input, config=None, **kwargs):
        try:
            return await super().ainvoke(input, config=config, **kwargs)
        except Exception:
            log.exception("Azure OpenAI ainvoke failed")
            raise

    def invoke(self, input, config=None, **kwargs):
        try:
            return super().invoke(input, config=config, **kwargs)
        except Exception:
            log.exception("Azure OpenAI invoke failed")
            raise


def create_model() -> LoggingAzureChatOpenAI:
    cfg = load_azure_config()
    if not cfg["api_key"] or not cfg["azure_endpoint"]:
        raise RuntimeError(
            "Set AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT "
            "(or AZURE_API_KEY + AZURE_API_BASE) in .env"
        )
    return LoggingAzureChatOpenAI(
        azure_endpoint=cfg["azure_endpoint"],
        api_key=cfg["api_key"],
        azure_deployment=cfg["azure_deployment"],
        api_version=cfg["api_version"],
    )


_llm: LoggingAzureChatOpenAI | None = None


async def run_startup_self_test() -> None:
    global _llm
    cfg = load_azure_config()
    log_azure_config(cfg)
    if not cfg["api_key"] or not cfg["azure_endpoint"]:
        raise SystemExit(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_API_KEY and "
            "AZURE_OPENAI_ENDPOINT in .env"
        )
    _llm = create_model()
    try:
        await _llm.ainvoke([HumanMessage(content="ping")])
        log.info("Azure OpenAI startup ping succeeded")
    except Exception as exc:
        log.exception("Azure OpenAI startup ping failed")
        raise SystemExit(
            f"Azure OpenAI startup self-test failed: {exc}. "
            "Fix AZURE_OPENAI_* / OPENAI_API_VERSION in .env and restart."
        ) from exc


@tool("searchInternet")
def search_internet(query: str) -> str:
    """Searches the internet for information."""
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return json.dumps({"error": "TAVILY_API_KEY is not configured"})
        client = TavilyClient(api_key=api_key)
        return json.dumps(client.search(query=query, max_results=5))
    except Exception:
        log.exception("searchInternet (Tavily) failed for query=%r", query)
        raise


def _log_run_agent_input(input_data: RunAgentInput) -> None:
    tool_names = [t.name for t in input_data.tools]
    state_keys = (
        list(input_data.state.keys())
        if isinstance(input_data.state, dict)
        else type(input_data.state).__name__
    )
    log.info(
        "RunAgentInput: thread_id=%s run_id=%s messages=%d tools=%s state_keys=%s",
        input_data.thread_id,
        input_data.run_id,
        len(input_data.messages),
        tool_names,
        state_keys,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_startup_self_test()
    bound_tools = [search_internet.name]
    log.info("Bound tools: %s", bound_tools)
    if "searchInternet" not in bound_tools:
        raise SystemExit(
            f"Expected tool name 'searchInternet', got {bound_tools!r}"
        )
    yield


def build_graph():
    return create_agent(
        create_model(),
        tools=[search_internet],
        middleware=[CopilotKitMiddleware()],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )


agui_agent = LangGraphAGUIAgent(
    name="dashboard_agent",
    description="Helps users understand dashboard sales and metrics data.",
    graph=build_graph(),
)

app = FastAPI(
    title="Chat with your data — LangGraph agent",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def all_exceptions(request: Request, exc: Exception):
    log.error("Unhandled agent error on %s %s", request.method, request.url.path, exc_info=exc)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__},
    )


@app.post("/copilotkit")
async def langgraph_agent_endpoint(input_data: RunAgentInput, request: Request):
    _log_run_agent_input(input_data)
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)
    request_agent = agui_agent.clone()

    async def event_generator():
        try:
            async for event in request_agent.run(input_data):
                yield encoder.encode(event)
        except Exception as exc:
            log.error("Agent run failed during SSE stream", exc_info=exc)
            traceback.print_exc()
            error_event = RunErrorEvent(
                type=EventType.RUN_ERROR,
                message=str(exc),
            )
            yield encoder.encode(error_event)

    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type(),
    )


@app.get("/copilotkit/health")
def copilotkit_health():
    return {"status": "ok", "agent": {"name": agui_agent.name}}


@app.get("/health")
def health():
    return {"status": "ok", "agent": "dashboard_agent"}


if __name__ == "__main__":
    port = int(os.getenv("LANGGRAPH_AGENT_PORT", "8000"))
    log.info("Starting agent server on :%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
