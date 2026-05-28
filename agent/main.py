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
from datetime import date
from pathlib import Path

import uvicorn
from ag_ui.core import EventType, RunAgentInput, RunErrorEvent
from ag_ui.encoder import EventEncoder
from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from tavily import TavilyClient

from policy_document_tool import finalize_client_upload, request_policy_document

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

SYSTEM_PROMPT = """You are an AI assistant for a financial planning dashboard.

When you give a report about data, use markdown formatting and tables when helpful.
Be concise unless the user asks for more detail.

**Monetary amounts:** Write large Indian currency values in short form: lakh as L and crore as Cr
(e.g. ₹7L, ₹10L, ₹1.5Cr, ₹7.5Cr). Use full comma-grouped amounts below ₹1 lakh (e.g. ₹45,000).
Do not abbreviate years (2026), percentages, IDs, or small counts.

You receive dashboard context from the app via CopilotKit (client list, selected client
Airtable data, financial plan output after Make plan).

## Insurance policies and ULIPs

When the user asks about THEIR insurance policy, life insurance, term plan, ULIP,
unit-linked plan, policy document, coverage, premiums, charges, surrender value, fund
allocation, or wants a policy/ULIP reviewed:

1. If no policy document has been uploaded in this thread yet, you MUST call
   `request_policy_document` with the correct document_type and a short reason.
   Do NOT guess policy terms, coverage amounts, charges, or fund values.

2. After `request_policy_document` returns with policy_summary (or already_uploaded),
   answer ONLY using that OCR summary for policy-specific facts. If the answer is not in the
   summary, say clearly that it is not stated in the uploaded document.

3. If the user skipped upload, give general educational information and state you do
   not have their actual policy document.

4. Do NOT call `request_policy_document` again if a document is already on file for
   this thread.

For unrelated questions (markets, NIFTY, general finance, dashboard metrics without
policy/ULIP intent), answer normally and do not request uploads.

Use searchInternet when the user needs information beyond dashboard data and uploaded
policy documents.

## Date-based calculations (current age, years to retirement, time to goals)

You do NOT have access to the current date in your context. You MUST call `getCurrentDate`
before answering ANY question that involves:
- The client's current age (from date of birth)
- Years remaining to a goal or retirement
- Any calculation using "today" or the current calendar year

Never assume or guess the date from training data. Always call the tool first.

## Charts in chat (frontend components — you MUST call the tool)

When the user asks to show, visualize, or chart data, call the matching component tool.
Do not only describe the chart in text — invoke the tool so the UI renders inline.

- `barChart` — compare values across categories (goal amounts, funding by period, counts).
  Args: `title` (optional), `data` array of `{label, value}` from readables/plan only.
- `pieChart` — parts-of-a-whole (asset allocation, portfolio mix, expense share).
  Args: `title` (optional), `data` array of `{label, value}` slices; values are portions of a total.

Never invent numbers. If the user says "pie chart" or "allocation", call `pieChart`. If they
ask for a bar chart or category comparison, call `barChart`."""


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


@tool("getCurrentDate")
def get_current_date() -> str:
    """Returns today's date (ISO) and calendar year for age, retirement, and time-to-goal calculations."""
    today = date.today()
    payload = {
        "date": today.isoformat(),
        "year": today.year,
        "month": today.month,
        "day": today.day,
    }
    log.info("getCurrentDate tool called - returning %s", payload)
    print(f"[getCurrentDate] tool called - returning date: {today.isoformat()}")
    return json.dumps(payload)


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
    bound_tools = [
        get_current_date.name,
        search_internet.name,
        request_policy_document.name,
    ]
    log.info("Bound backend tools: %s (barChart/pieChart are frontend useComponent tools)", bound_tools)
    for required in (
        "getCurrentDate",
        "searchInternet",
        "request_policy_document",
    ):
        if required not in bound_tools:
            raise SystemExit(
                f"Expected tool name {required!r}, got {bound_tools!r}"
            )
    yield


@wrap_model_call
async def force_get_current_date_first(request, handler):
    """Force getCurrentDate once per thread before the model can answer date-based questions."""
    already_has_date = any(
        isinstance(m, ToolMessage) and m.name == "getCurrentDate"
        for m in request.messages
    )
    if not already_has_date:
        log.info("Forcing getCurrentDate tool call (first turn in thread)")
        request = request.override(tool_choice="getCurrentDate")
    return await handler(request)


def build_graph():
    return create_agent(
        create_model(),
        tools=[get_current_date, search_internet, request_policy_document],
        middleware=[force_get_current_date_first, CopilotKitMiddleware()],
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


class ParsePolicyDocumentBody(BaseModel):
    filename: str | None = None
    fileType: str | None = None
    fileData: str | None = Field(None, description="Deprecated — raw PDF not accepted")
    policy_summary: dict | None = None
    thread_id: str | None = None
    document_type: str = "insurance_policy"


@app.post("/parse-policy-document")
def parse_policy_document_endpoint(body: ParsePolicyDocumentBody):
    """Finalize OCR policy summary for chat (legacy agent-side entry)."""
    if body.fileData and not body.policy_summary:
        return JSONResponse(
            status_code=400,
            content={
                "detail": (
                    "Raw PDF parsing is disabled. Upload via the chat UI so the "
                    "OCR microservice can summarize the document first."
                ),
            },
        )

    if body.policy_summary:
        summary = body.policy_summary
    else:
        return JSONResponse(
            status_code=400,
            content={"detail": "Missing policy_summary from OCR service"},
        )

    try:
        tid = (body.thread_id or "default").strip() or "default"
        doc_type = body.document_type or "insurance_policy"
        context_text = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
        tool_result = finalize_client_upload(
            {
                "uploaded": True,
                "filename": body.filename,
                "fileType": body.fileType or "application/pdf",
                "policySummary": summary,
            },
            thread_id=tid,
            document_type=doc_type,
        )
        return {
            "policy_summary": summary,
            "char_count": len(context_text),
            "thread_id": tid,
            "tool_result": json.loads(tool_result),
        }
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})


if __name__ == "__main__":
    port = int(os.getenv("LANGGRAPH_AGENT_PORT", "8000"))
    log.info("Starting agent server on :%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
