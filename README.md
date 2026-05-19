# Chat with your data

AI-powered dashboard assistant built with [CopilotKit](https://copilotkit.ai), Next.js, and Tremor. Ask questions about sample sales metrics in natural language, search the web via Tavily, and see answers in a Copilot sidebar.

![Chat with your data](./preview.gif)

This folder is a **standalone app** — copy it to your own repository; it does not depend on the CopilotKit monorepo.

## Prerequisites

- **Node.js 20+**
- **npm**, **pnpm**, or **yarn**
- An **Azure OpenAI** or **OpenAI** API key
- A **[Tavily](https://tavily.com)** API key (for the `searchInternet` backend action)

## Quick start

1. **Copy or clone** this directory into your project.

2. **Install dependencies:**

   ```bash
   npm install
   ```

   ```bash
   # or
   pnpm install
   ```

3. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at least:

   - **Azure OpenAI** — `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_DEPLOYMENT_NAME`, and optionally `AZURE_API_VERSION`
   - **or OpenAI** — `OPENAI_API_KEY` (used when Azure variables are unset)
   - **Tavily** — `TAVILY_API_KEY`

4. **(Recommended) Start the LangGraph agent** so the LLM runs in the graph, not directly from Next.js:

   ```bash
   cd agent
   pip install -r requirements.txt
   python main.py
   ```

   In the repo root `.env`, set `LANGGRAPH_AGENT_URL=http://localhost:8000/copilotkit` (see `.env.example`).

5. **Run the dev server** (separate terminal, repo root):

   ```bash
   npm run dev
   ```

6. Open [http://localhost:3000](http://localhost:3000).

### Optional query parameter

- `?openCopilot=true` — opens the Copilot sidebar on load.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_API_KEY` | Azure path | Azure OpenAI API key |
| `AZURE_API_BASE` | Azure path | Resource URL, e.g. `https://your-resource.openai.azure.com` |
| `AZURE_DEPLOYMENT_NAME` | Azure path | Deployment name, e.g. `gpt-4o` |
| `AZURE_API_VERSION` | No | API version (default `2024-08-01-preview`) |
| `OPENAI_API_KEY` | OpenAI path | Used when Azure vars are not set |
| `TAVILY_API_KEY` | Yes* | Tavily search for `searchInternet` action |
| `LANGGRAPH_AGENT_URL` | LangGraph path | e.g. `http://localhost:8000/copilotkit` — proxies chat to the Python agent |
| `NEXT_PUBLIC_LANGGRAPH_AGENT_ID` | No | Defaults to `dashboard_agent` (must match `agent/main.py`) |

\*Chat works without Tavily, but web search actions will fail.

Unset `LANGGRAPH_AGENT_URL` to fall back to **direct** Azure/OpenAI from Next.js (original demo behavior).

> **Azure note:** The API route uses the **Chat Completions** API (`provider.chat()`), not OpenAI’s Responses API, because Azure deployments typically do not expose `/responses`.

## Project structure

```
├── agent/
│   ├── main.py                   # LangGraph agent + FastAPI AG-UI endpoint
│   └── requirements.txt
├── app/
│   ├── api/copilotkit/route.ts   # CopilotKit runtime → LangGraph or Azure/OpenAI
│   ├── layout.tsx                # CopilotKit provider
│   └── page.tsx                  # Dashboard + CopilotSidebar
├── components/                   # UI, charts, generative search results
├── data/dashboard-data.ts        # Sample metrics (no external DB)
├── lib/prompt.ts                 # Copilot instructions
├── .env.example
└── package.json
```

## Production build

```bash
# Ensure a standard production env (required for `next build`)
export NODE_ENV=production   # Git Bash / macOS / Linux
# PowerShell: $env:NODE_ENV = "production"

npm run build
npm run start
```

This repo includes `package-lock.json` and `.npmrc` (`legacy-peer-deps=true`) so `npm ci` reproduces the same install on CI and other machines.

Deploy to [Vercel](https://vercel.com) or any Node host; set the same environment variables in the project settings.

## How it works

With **`LANGGRAPH_AGENT_URL`** set (default in `.env.example`):

1. **`agent/main.py`** runs a LangGraph agent (Azure/OpenAI + Tavily + `CopilotKitMiddleware`) at `http://localhost:8000/copilotkit`.
2. **`CopilotKit`** in `app/layout.tsx` uses `agent="dashboard_agent"` and talks to `/api/copilotkit`.
3. **`app/api/copilotkit/route.ts`** uses `LangGraphHttpAgent` — no direct LLM calls from Next.js.

Without `LANGGRAPH_AGENT_URL`, the app calls Azure/OpenAI directly from the API route (legacy path).

- **`useCopilotReadable`** in `components/Dashboard.tsx` exposes dashboard JSON to the model (via CopilotKit → LangGraph when the agent is running).
- **`searchInternet`** — tool on the LangGraph agent; UI still renders via `useCopilotAction` in `Dashboard.tsx`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **Resource not found** (Azure) | Confirm deployment name and base URL; ensure Chat Completions is enabled for the deployment. |
| **Agent not found** | Start `python agent/main.py`, confirm `LANGGRAPH_AGENT_URL`, and that `agent="dashboard_agent"` matches `agent/main.py`. |
| **LangGraph / agent connection errors** | Check `http://localhost:8000/health` and that nothing else uses port 8000. |
| **ECONNREFUSED** | Ensure `npm run dev` is running; check `runtimeUrl` is `/api/copilotkit`. |
| Tavily errors | Set `TAVILY_API_KEY` in `.env`. |

## License

MIT — see [LICENSE](./LICENSE).

Based on the [CopilotKit chat-with-your-data example](https://github.com/CopilotKit/CopilotKit/tree/main/examples/v1/chat-with-your-data).
