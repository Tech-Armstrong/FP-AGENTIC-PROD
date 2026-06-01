# Plan 0001 — Fix client-list error message: port 8000 → 8001

- **Status:** ready-for-execution
- **Branch / PR:** fix/sidebar-port-8001-message
- **Owner:** Claude Code (planner)

## Goal
The client-list data-fetch error tells the user the FastAPI server runs on port **8000**, but the
data/plan API runs on **8001**. Correct the message so a failing dashboard sends the user to the right port.

## Context & rationale
`PROJECT_OVERVIEW.md` §17 ("Error says port 8000 for clients") and §24 ("Fix `ClientsDashboard`
port 8000 → 8001 error message") flag this as a known copy-paste bug — but they **mislocate it**.
The string does **not** live in `components/ClientsDashboard.tsx` (which has no port reference);
it lives in **`components/DashboardSidebar.tsx:209`**, inside the client-list `error` block:

```
Is the FastAPI server running on port 8000?
```

The data API default is `:8001` — `backend/airtable_main.py:704` (`FASTAPI_PORT` defaults to `8001`)
and the Next proxies (`lib/fastapi-proxy.ts:1`, `app/api/airtable/clients/route.ts:3`) all default to
`http://localhost:8001`. So `8000` is simply wrong here; :8000 is the chat agent. This is a display-only
one-word fix with no behavioral change — a good first plan to exercise the planner → Cursor loop.

## Affected files
- `components/DashboardSidebar.tsx` — **edit** (line ~209, the client-list error hint text).

## Implementation steps
1. In `components/DashboardSidebar.tsx`, locate the client-list error block (the `{error && (...)}`
   JSX, around line 199–211) and its hint `<span>`:
   ```tsx
   <span className="text-muted-foreground">
     Is the FastAPI server running on port 8000?
   </span>
   ```
   Change the literal `8000` to `8001` so it reads:
   ```tsx
   <span className="text-muted-foreground">
     Is the FastAPI server running on port 8001?
   </span>
   ```
   This is the **only** change. Do not alter the `error` state logic, the surrounding `cn(...)`
   classNames, or any other component.

## Contract / interface changes
None. Display-string only — no API, env var, state shape, or workflow change.

## Env / ports touched
None changed. The corrected text references port **8001** (the FastAPI data API,
`FASTAPI_BASE_URL` default). Ports 3000/8000/8001 are otherwise untouched.

## Acceptance criteria & how to verify
1. **Wrong-port string is gone:** grep the repo for `port 8000` in `components/` returns no match;
   `components/DashboardSidebar.tsx` now contains `running on port 8001?`.
2. **Error path shows 8001:** stop the :8001 backend (or it's already down), run `npm run dev`,
   load the dashboard so the client-list fetch fails; the red error box reads
   "…running on port **8001**?".
3. **No regression:** `npm test` (vitest) stays green.

## Tests
Manual only for the rendered string (it's a static literal with no logic). If the executor wants a
guard, an optional RTL test could force the `error` state in `DashboardSidebar` and assert the text
contains "8001" — but this is not required for a one-word display fix.

## Risks & rollback
Negligible risk — single display string, no logic. Rollback = revert the one-line edit (or the branch).

## Out of scope
- Do **not** touch the actual `:8001` wiring, proxies, or `FASTAPI_BASE_URL` handling.
- Do **not** edit `ClientsDashboard.tsx` or any other component.
- Do **not** "fix" other §24 cleanup items (dead `'END'` branch, emergency-fund node, etc.).

## Docs to update
`PROJECT_OVERVIEW.md` §17 and §24: change the file reference from `ClientsDashboard.tsx` to
`components/DashboardSidebar.tsx` (the message lives there), and mark the bug fixed. This corrects
drift item #1 from `AGENTS.md`'s "Known doc drift" list.
