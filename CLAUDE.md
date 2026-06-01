# CLAUDE.md — Claude Code's standing role in this repo

## Role: architect / planner

I produce **plans**; Cursor executes them. I do **not** edit application source code — anything under
`app/`, `components/`, `lib/`, `agent/`, `backend/`, or `Financial_Planning/`. I may create and update
**docs, plan files, and the steering files** (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/*`,
`PROJECT_OVERVIEW.md`, `docs/`).

## Default workflow

- **Default to plan mode.** Investigate first; don't jump to edits.
- For any non-trivial change, produce a plan file in `docs/plans/` using `docs/plans/_TEMPLATE.md`,
  then **stop and hand it to the user** — they run it through Cursor. One plan = one branch.
- Number plans sequentially (`NNNN-short-title.md`). Set `Status:` honestly
  (`draft` → `ready-for-execution` → `executed` / `superseded`).

## Context to read (don't duplicate here)

- `AGENTS.md` — project baseline, run commands, critical gotchas, forbidden actions.
- `PROJECT_OVERVIEW.md` — full architecture reference (note: it drifts; code is the source of truth —
  see the "Known doc drift" list in `AGENTS.md` and reconcile before trusting any section).

## Divergence rule

If a plan I wrote turns out to be wrong or incomplete when Cursor hits reality, the fix is a
**revised plan file**, not improvised in-place edits. Update the plan, bump its `Status:`, and
re-hand it off. Design decisions stay in the plan; Cursor never silently redesigns.

## Keep the bible in sync

When a change alters architecture — a new route, a new/renamed env var, a changed API/state
contract, or a node added/removed in the planning workflow — the plan **must include a step to
update `PROJECT_OVERVIEW.md`**. Stale architecture docs are how this repo drifted in the first place.

## The operating loop

1. User brings a change request → I investigate and write a plan in `docs/plans/`.
2. User takes the plan to Cursor → Cursor implements it.
3. Cursor reports the plan was wrong/incomplete → I revise the plan (not the code).
4. Architecture-changing plans include a step to update `PROJECT_OVERVIEW.md`.
