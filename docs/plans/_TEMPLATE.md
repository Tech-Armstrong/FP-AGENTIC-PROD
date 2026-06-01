# Plan NNNN — <short title>

- **Status:** draft | ready-for-execution | executed | superseded
- **Branch / PR:** <branch name, one plan = one branch>
- **Owner:** Claude Code (planner)

## Goal
<One sentence. What changes and why it matters.>

## Context & rationale
<Why this approach. Link the relevant PROJECT_OVERVIEW.md sections. Note any tradeoff.>

## Affected files
<Exact paths. Mark each: edit / create / delete.>

## Implementation steps
<Ordered. File by file, function by function. Each step: which file, which function/symbol, what changes, before → after if non-obvious. This is the part Cursor follows literally — be specific enough that there is no design left to do.>

## Contract / interface changes
<API routes (method, path, body, response), env vars added/renamed, React state shape, workflow node additions/removals/edges. "None" if none.>

## Env / ports touched
<Which of AZURE_OPENAI_* vs AZURE_API_* / TAVILY / AIRTABLE_* / LANGGRAPH_* / FASTAPI_* are involved. Which of ports 3000/8000/8001. "None" if none.>

## Acceptance criteria & how to verify
<Concrete checks. Reuse the curl/health checks from PROJECT_OVERVIEW.md §16 where relevant, e.g. `curl :8001/health`, "Make plan populates summary tables, Network shows POST /api/financial-plan/run 200".>

## Tests
<What to add/run, or "manual only — <why>".>

## Risks & rollback
<What could break; how to revert.>

## Out of scope
<Explicitly what NOT to touch, so Cursor doesn't wander.>

## Docs to update
<Which PROJECT_OVERVIEW.md sections to update, or "none — no architecture change".>
