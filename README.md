# Chat with your Data

AI-powered financial planning dashboard with a Copilot sidebar: browse client records from Airtable, view portfolio and liability summaries, and ask questions in natural language. By default, chat runs through a **LangGraph Python agent** on port 8000 (Azure OpenAI + Tavily web search); the Next.js app proxies CopilotKit traffic and exposes dashboard context to the model.

## Tech stack

- **Frontend:** Next.js `^15.5.18`, React `^19`, CopilotKit `@copilotkit/*` `^1.57.1`, Tailwind CSS `^4`, Recharts
- **Agent:** Python FastAPI + `copilotkit` / `ag-ui-langgraph` + LangChain `create_agent` + LangGraph (`agent/main.py`)
- **Data API:** Python FastAPI + Airtable (`backend/airtable_main.py`)
- **Providers:** Azure OpenAI, Tavily, Airtable

## How to run locally

1. Copy env and configure keys (see `.env.example` — Azure for the agent, Tavily, Airtable for the dashboard):

   ```bash
   cp .env.example .env
   ```

2. **Terminal 1 — LangGraph agent (port 8000):**

   ```bash
   cd agent
   pip install -r requirements.txt
   python main.py
   ```

   Health check: `curl http://localhost:8000/copilotkit/health` → `{"status":"ok","agent":{"name":"dashboard_agent"}}`

3. **Terminal 2 — Airtable API (port 8001):**

   Use a **virtualenv** and install **all** backend deps (includes **langgraph** for **Make plan**):

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate          # Windows — on macOS/Linux: source .venv/bin/activate
   pip install -r backend/requirements.txt
   # or from repo root: pip install -r requirements.txt
   python backend/airtable_main.py
   ```

   If **Make plan** returns `No module named 'langgraph'`, you are not using the venv where the line above ran — reinstall with `pip install -r backend/requirements.txt`.

   **Windows:** If `python backend/airtable_main.py` says the address is already in use on port 8001, an old API process is still running. Stop it (`netstat -ano | findstr :8001` then `taskkill /PID <pid> /F`) or set `FASTAPI_PORT` to another port in `.env`.

   Health check: `curl http://localhost:8001/health` → `{"status":"ok"}`

4. **Terminal 3 — Next.js (port 3000):**

   ```bash
   npm install
   npm run dev
   ```

   Set `LANGGRAPH_AGENT_URL=http://localhost:8000/copilotkit` in `.env` (recommended). Open [http://localhost:3000](http://localhost:3000).

Unset `LANGGRAPH_AGENT_URL` to use **direct Azure/OpenAI** from Next.js only (no Python agent required for chat).

## Full documentation

Architecture, request lifecycle, env vars, tools, failure modes, and non-obvious behavior:

**[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)**

## License

MIT — see [LICENSE](./LICENSE).
