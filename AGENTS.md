# AGENTS.md — Project baseline (read this first)

Shared, vendor-neutral brief for **any** agent working in this repo (Claude Code = planner,
Cursor = executor). Read this before touching anything. Depth lives in `PROJECT_OVERVIEW.md`.

## What this app is

A financial-planning dashboard. Users browse a client list and per-client portfolio / net-worth
views (Airtable → Python API → Next.js), press **Make plan** to run a multi-node LangGraph
pipeline that produces an allocation/goal-funding summary, and use a **Copilot chat sidebar** for
natural-language Q&A over the dashboard data and the generated plan.

## Topology — 3 ports, 2 runtimes, 2 AI paths

- **:3000** — Next.js (UI + API proxy routes under `app/api/`).
- **:8000** — chat agent (`agent/main.py`), AG-UI/CopilotKit ReAct loop.
- **:8001** — financial data + planning API (`backend-airtable/main.py`); Airtable reads + `POST /financial-plan/run`.

Two **independent** AI paths:
1. **Chat** — Copilot sidebar → `/api/copilotkit` → chat agent on :8000 (or direct-Azure in Next).
2. **Financial plan** — **Make plan** button → `/api/financial-plan/run` → :8001 → `Financial_Planning/Workflow/workflow.py`.

**The chat agent CANNOT run the planning workflow.** No tool, no subgraph, no shared endpoint. Chat
can only *read* a generated plan's `summary` via `useCopilotReadable`. Don't wire them together
unless a plan explicitly says to.

## Run locally

Three terminals (full experience):
```bash
# Terminal 1 — chat agent :8000
cd agent && pip install -r requirements.txt && python main.py
# Terminal 2 — financial API :8001 (Airtable + Make plan)
pip install -r backend/requirements.txt && python backend-airtable/main.py
# Terminal 3 — Next :3000
npm install && npm run dev
```
Helper: `npm run dev:all` (→ `scripts/start-dev.ps1`) starts the stack on Windows.
Chat-only needs terminals 1+3; Make plan needs terminal 2. Set repo-root `.env` from `.env.example`.

Tests: `npm test` (vitest), `npm run test:agent` (pytest in `agent/tests`).

## Critical gotchas — never get these wrong

- **Dual Azure env naming.** Chat agent uses `AZURE_OPENAI_*` (with `AZURE_API_*` aliases in
  `agent/main.py`). Planning LLM nodes (`Financial_Planning/Nodes/agentic_nodes.py`) and direct-Next
  chat (`app/api/copilotkit/route.ts`) use `AZURE_API_*`. Use the right set for the right stack; don't merge them.
- **Port :8001, not :8000, for client/data/plan APIs.** `FASTAPI_BASE_URL` defaults to
  `http://localhost:8001`. :8000 is the chat agent only.
- **No plan persistence.** A generated plan lives in browser React state only; refresh loses it. No DB, no Airtable write-back.
- **No auth; CORS `*` on :8001.** Treat as a trusted-network demo, not internet-facing.

## Forbidden actions (any agent)

- **Don't invent npm/pip packages.** This repo has declared-but-unused deps (`@tremor/react`,
  `@hookform/resolvers`, `react-hook-form`, `react-day-picker`, `zod`, etc.). Verify a package is
  actually installed (in `node_modules` / the active venv) **before** importing it.
- **Don't delete `.env`, `package.json`, or lockfiles** without explicit confirmation.
- **Don't commit without review.**

## Known doc drift (verify before trusting PROJECT_OVERVIEW.md)

The overview is the architecture bible but has drifted from code in places. Confirmed as of this writing:
1. ~~Port 8000 client-list error message~~ — fixed in `components/DashboardSidebar.tsx` (was misdocumented as `ClientsDashboard.tsx`).
2. The chat agent exposes **3 tools** (`getCurrentDate`, `searchInternet`, `request_policy_document`), not just `searchInternet` (overview §13).
3. The planning workflow has **added nodes** (`calculate_term_insurance_requirement`, `wealth_at_retirement`); graph now ends `wealth_at_retirement → END`, not at 20 nodes (overview §5.3).
4. New components exist that the file inventory (§9) doesn't list (`DashboardSidebar`, `SpouseDetailsPanel`, `RealEstateTable`, `MarriageGoalsSection`, `EducationPlanningSection`, `agent/policy_document_tool.py`, …).
5. A test stack now exists (vitest + testing-library, `agent/tests`); overview §19 says there is none.

When code and overview disagree, **code wins** — and a plan should include updating the overview.

---

Full architecture reference: `PROJECT_OVERVIEW.md`. Implementation plans to execute: `docs/plans/`.
