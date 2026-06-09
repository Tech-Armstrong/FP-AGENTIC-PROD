# Plan 0003 — Retirement annuity (income-preservation) node + Make-plan section

- **Status:** ready-for-execution
- **Branch / PR:** `feat/retirement-annuity` (one plan = one branch)
- **Owner:** Claude Code (planner) — execution by Cursor

## Goal
Add a retirement **annuity** calculation as a new workflow node after `wealth_at_retirement`, and
render its result in the Make-plan UI right below the "Wealth at retirement" section — answering
"can the client achieve a desired monthly annuity, and if not, how much can they get?"

## Context & rationale
A client wants a target monthly income (annuity) in retirement (e.g. ₹50k/month) from retirement
age until life expectancy (85). We must show whether their portfolio supports it.

**Decided model (confirmed with user):**
- **Income-preservation, NOT drawdown.** The annuity is funded by the *income/yield* assets throw
  off (FD interest, fund yield), **principal is never spent**. So per asset:
  `annual_income = future_value_at_retirement × yield_rate`. We do **not** use
  `calculate_present_value_annuity` to deplete a corpus.
- **Recurring passive income covers the annuity first.** If `other_income(rental/interest/other)`
  ≥ desired annuity → goal met, **no assets touched** (the example: ₹50k rent covers ₹50k annuity).
- **Shortfall is met by asset income in priority order FD → mutual funds → (RSU/ESOP).**
  Mutual funds are a single bucket (no BAF/large-cap tag exists in the data today), so the literal
  "FD > BAF > large-cap" collapses to FD → MF. RSU/ESOP are extra *corpus* whose income is tapped
  after FD/MF. Priority only decides which assets' income is "required" (for the breakdown); since
  principal is preserved and income just sums, no asset is consumed.
- If total available income < desired → report **max achievable annuity** and the monthly shortfall.
- **Inputs `desired_monthly_annuity` and `retirement_age` are user-given** (for testing): delivered
  via the existing `overrides` payload **and** new UI input fields, mirroring the rate-override pattern.

Relevant architecture: PROJECT_OVERVIEW §5.3 (node DAG — currently ends `wealth_at_retirement → END`),
§5.5 (per-node table), §11 (`summary` shape + `PlanOverrides`), §7 (overrides plumbing).

### Assumptions (tunable; call out in code comments)
- Desired annuity is a **retirement-year nominal** monthly figure (not inflation-adjusted in v1).
- Recurring `other_income` is used at face value (not grown to retirement) — it already conflates
  rental/interest/other, which is acceptable per the decision.
- Yield rates: **FD** = its `interest_rate` (default 6.5%); **MF** = `expected_annual_return`
  (default 12%, also settable via existing `mf_expected_return` override) — flag as optimistic;
  **ESOP** = 12%; **RSU** = `get_rsu_growth_rate(...)`.
- `life_expectancy = 85` (existing constant). In an income-preservation model income is effectively
  perpetual, so 85 is informational/horizon only (kept for display and future drawdown fallback).

## Affected files
- `Financial_Planning/Models/client_data_state.py` — **edit** (new state key)
- `Financial_Planning/Nodes/retirement_nodes.py` — **edit** (new node `calculate_retirement_annuity`)
- `Financial_Planning/Workflow/workflow.py` — **edit** (register node, rewire end edges)
- `backend/financial_plan_runner.py` — **edit** (`summarize_plan_state`: build + return `annuity_preview`)
- `backend-airtable/main.py` — **edit** (`PlanOverrides` fields + `apply_plan_overrides` injection)
- `components/FinancialPlanPanel.tsx` — **edit** (summary type, overrides type, new section, input fields)
- `components/ClientsDashboard.tsx` — **edit** (input state + include in run overrides)
- `Financial_Planning/tests/test_retirement_annuity.py` — **create** (unit test)
- `PROJECT_OVERVIEW.md`, `AGENTS.md` — **edit** (doc sync)

## Implementation steps

### 1. State — `Financial_Planning/Models/client_data_state.py`
Add to `ClientState` TypedDict (last-write-wins, no reducer): `retirement_annuity: dict`.

### 2. New node — `Financial_Planning/Nodes/retirement_nodes.py`
Add `calculate_retirement_annuity(state: ClientState)` after `wealth_at_retirement`. Reuse
`calculate_future_value` from `Utilities/utility_functions.py`; reuse FD figures already computed by
`wealth_at_retirement`. Read inputs (the whole payload is `state['client_data']`):

- `personal = state['client_data']['client_data']` → `retirement_age`,
  `desired_monthly_annuity` (new field injected by override; default 0 / skip section if absent).
- `invest = state['client_data']['investment_details']`.
- `surplus_income_monthly = invest['financial_summary'][0]['other_income(rental/interest/other)']` (default 0).
- `years_to_ret = state['required_retirement_corpus']['client_info']['years_to_retirement']`.
- `retirement_year = state['wealth_at_retirement']['retirement_year']` (fallback `date.today().year + years_to_ret`).

Compute per-source **future value at retirement** and **annual income = FV × rate**:
- **FD:** reuse `state['wealth_at_retirement']['breakdown']['fixed_deposits']` →
  `fd_fv = future_value`, `fd_rate` parsed from its `rate` string (fallback 0.065).
  `fd_income = fd_fv * fd_rate`.
- **Mutual funds (single bucket):** `mf_fv = Σ calculate_future_value(cv, r, years_to_ret)` and
  `mf_income = Σ fv * r` over `invest['mutual_funds']` using `current_value` (cv) and
  `expected_annual_return` (r, default 0.12).
- **RSU/ESOP corpus:** ESOP `esop_fv = Σ calculate_future_value(vested_esops_value, 0.12, years_to_ret)`,
  income `= esop_fv * 0.12`. RSU best-effort: total RSU value grown at
  `get_rsu_growth_rate(invest)` to retirement (reuse existing RSU helpers in
  `Nodes/allocations_nodes.py` / `RSU/constants.py`; if not readily callable, approximate from
  vested tranche values and flag with a `# TODO` comment), income `= rsu_fv * rsu_rate`. Combine into
  one `rsu_esop` source. (Example has none → contributes 0; keep this path non-blocking.)

Algorithm (annualize everything; `desired_annual = desired_monthly_annuity * 12`,
`surplus_annual = surplus_income_monthly * 12`):
```
need = desired_annual - surplus_annual
ordered = [fixed_deposits, mutual_funds, rsu_esop]   # priority; rental is separate/always-on
cumulative = surplus_annual
for src in ordered:
    src.required = cumulative < desired_annual        # was this asset's income needed?
    cumulative += src.annual_income
total_available_annual = surplus_annual + sum(src.annual_income for src in ordered)
achievable = total_available_annual >= desired_annual
max_monthly = total_available_annual / 12
shortfall_monthly = max(0.0, desired_monthly_annuity - max_monthly)
achievable_monthly = desired_monthly_annuity if achievable else max_monthly
```
Return:
```python
return {'retirement_annuity': {
  "model": "income_preservation",           # principal not consumed
  "retirement_year": retirement_year,
  "retirement_age": retirement_age,
  "life_expectancy": 85,
  "desired_monthly_annuity": round(desired_monthly_annuity, 2),
  "achievable": achievable,
  "achievable_monthly_annuity": round(achievable_monthly, 2),
  "max_monthly_annuity": round(max_monthly, 2),
  "shortfall_monthly": round(shortfall_monthly, 2),
  "surplus_income_monthly": round(surplus_income_monthly, 2),
  "total_available_monthly": round(max_monthly, 2),
  "sources": [
    {"key":"rental_other_income","label":"Rental / other income","rate":"-",
     "monthly_income":..,"annual_income":..,"corpus_fv":None,"required":True},
    {"key":"fixed_deposits","label":"FD interest","rate":fd_rate_str,
     "monthly_income":..,"annual_income":..,"corpus_fv":fd_fv,"required":bool},
    {"key":"mutual_funds","label":"Mutual fund yield","rate":mf_rate_str,
     "monthly_income":..,"annual_income":..,"corpus_fv":mf_fv,"required":bool},
    {"key":"rsu_esop","label":"RSU / ESOP yield","rate":rsu_rate_str,
     "monthly_income":..,"annual_income":..,"corpus_fv":rsu_esop_fv,"required":bool},
  ],
}}
```
Match the existing node's `print(...)` debug style. Skip/return empty `{}` cleanly if
`desired_monthly_annuity <= 0` (so the UI section simply doesn't render).

### 3. Workflow wiring — `Financial_Planning/Workflow/workflow.py`
- Import `calculate_retirement_annuity` alongside `wealth_at_retirement`.
- `graph.add_node('calculate_retirement_annuity', calculate_retirement_annuity)`.
- Replace the terminal edge `graph.add_edge('wealth_at_retirement', END)` with:
  `graph.add_edge('wealth_at_retirement', 'calculate_retirement_annuity')` then
  `graph.add_edge('calculate_retirement_annuity', END)`.

### 4. Summary contract — `backend/financial_plan_runner.py`
In `summarize_plan_state`, mirror the `wealth_at_retirement_preview` block (~L597-635): read
`state.get('retirement_annuity')`, and if it has `sources`, build `annuity_preview` with the same
shape the node returns (it's already UI-ready — pass `sources` straight through as `rows`-equivalent
plus the scalar fields). Add `"annuity_preview": annuity_preview` to the returned `summary` dict
(near the `wealth_at_retirement_preview` return, ~L693).

### 5. Override inputs (backend) — `backend-airtable/main.py`
- `PlanOverrides` (L107-112): add `desired_monthly_annuity: float | None = None` and
  `retirement_age: int | None = None`.
- `apply_plan_overrides` (L619-650), after `deepcopy`: these are **not rates** — do not pass through
  `_normalize_rate`.
  - `if overrides.retirement_age is not None: payload["client_data"]["retirement_age"] = int(overrides.retirement_age)`
  - `if overrides.desired_monthly_annuity is not None: payload["client_data"]["desired_monthly_annuity"] = float(overrides.desired_monthly_annuity)`
  (Run endpoint already calls `apply_plan_overrides` before invoke, ~L771 — no change there.)

### 6. UI — `components/FinancialPlanPanel.tsx`
- **Types:** add to `PlanOverrides` (L107-117): `desired_monthly_annuity?: number;`,
  `retirement_age?: number;`. Add to `PlanSummary` (L45-88): `annuity_preview?: { ... } | null;`
  matching the node output (achievable, desired_monthly_annuity, achievable_monthly_annuity,
  max_monthly_annuity, shortfall_monthly, surplus_income_monthly, retirement_year, retirement_age,
  life_expectancy, sources[]).
- **New section:** after the wealth-at-retirement block (insert after L1112, before the "Goal
  allocations" comment at L1114). Render only when `s.annuity_preview`. Use `ReviewSectionTitle`
  with a new lucide icon (e.g. `Banknote` or `Coins`; add to imports). Show:
  - Header line: desired vs achievable monthly annuity + a status pill — green "Achievable" when
    `achievable`, amber "Shortfall ₹X/mo" otherwise (`fmtInr(shortfall_monthly)`).
  - A table of `sources` (label `@ rate` | monthly income via `fmtInr`), de-emphasize rows where
    `required === false` (e.g. muted text + "not required" tag); FD/MF/RSU show `corpus_fv` as a
    secondary "from ₹Xcr corpus" caption.
  - A `PieChart` of source `monthly_income` contributions (reuse the wealth section's pattern).
  - Footnote: "Funded by asset income — principal is preserved (assets are not sold)."
  Reuse `fmtInr` (L176-179) for all currency.
- **Input fields:** add two number inputs near the existing rate-override controls — "Desired monthly
  annuity (₹)" and "Retirement age" — bound to new props/state passed up to `ClientsDashboard`
  (these are plain numbers, not percentages, so do not route them through `parseRateToDecimal`).

### 7. UI run wiring — `components/ClientsDashboard.tsx`
- Hold the two new inputs as state (next to the rate-input state).
- In `buildPlanOverridesForRun` (L230-269) — or a sibling call at run time — set
  `overrides.desired_monthly_annuity` / `overrides.retirement_age` directly from the raw number
  inputs when provided (no rate parsing). Keep them out of `planTabLabel`'s rate-diff logic (they can
  still trigger a fresh run, but don't need to drive the rate tab label).

### 8. Docs — `PROJECT_OVERVIEW.md` + `AGENTS.md`
- PROJECT_OVERVIEW §5.3 DAG: end is now `wealth_at_retirement → calculate_retirement_annuity → END`;
  §5.5 add the node row; §11 add `annuity_preview` to the `summary` shape and the two new
  `PlanOverrides` fields; §7 note the override injection points.
- AGENTS.md "Known doc drift" #3: update terminal node to `calculate_retirement_annuity`.

## Contract / interface changes
- **Workflow:** +1 node `calculate_retirement_annuity`; end edges rerouted through it. +1 state key
  `retirement_annuity`.
- **API `POST /financial-plan/run` `overrides`:** + `desired_monthly_annuity?: number`,
  `retirement_age?: number`.
- **`summary`:** + `annuity_preview` object.
- **React state:** + two inputs in the Make-plan panel; `PlanSummary` / `PlanOverrides` types extended.

## Env / ports touched
None new. Make-plan path only: Next :3000 → FastAPI :8001 → workflow. No Azure/LLM changes (this is a
deterministic node). `AZURE_API_*` still required by the unrelated LLM nodes for a full run.

## Acceptance criteria & how to verify
1. `curl http://localhost:8001/health` → ok; backend boots without import errors after the new node.
2. **Example case** (retirement_age + ₹50k annuity via overrides/inputs; client with ₹50k/month
   `other_income`): plan returns `annuity_preview.achievable === true`, `sources[rental].required`
   true, FD/MF/RSU `required === false`; UI shows green "Achievable", rental row highlighted, asset
   rows muted as "not required". Confirms "income covers it → don't touch assets."
3. **Shortfall case** (set annuity to e.g. ₹3L/month): `achievable === false`,
   `shortfall_monthly > 0`, FD then MF marked `required`, max annuity = sum of all source incomes /12.
4. Section appears **immediately after** "Wealth at retirement"; Network shows
   `POST /api/financial-plan/run` 200 with `summary.annuity_preview` populated.
5. Changing the override `retirement_age` shifts `years_to_retirement` and the FVs/incomes accordingly.

## Tests
- Add a Python unit test (`Financial_Planning/tests/test_retirement_annuity.py`) for
  `calculate_retirement_annuity` covering: (a) income covers annuity → achievable, no asset required;
  (b) shortfall → FD/MF tapped in order, correct `max_monthly_annuity`; (c) zero desired annuity →
  returns empty (section hidden). Use a minimal hand-built `state` dict (no Airtable/LLM needed).
- Frontend: manual verification (no existing test covers `FinancialPlanPanel` rendering).

## Risks & rollback
- **Wrong nesting for override injection.** Verified: `retirement_age` at `payload['client_data']`
  (main.py:197); `other_income` at `payload['investment_details']['financial_summary'][0]`
  (main.py:576). Keep reads defensive (`.get(...)`, defaults) so a missing field hides the section
  rather than 500s.
- **RSU income path** is best-effort; if the RSU helper isn't cleanly reusable, ship FD+MF+ESOP and
  leave RSU at 0 with a TODO — does not affect the example.
- **Rollback:** revert the touched files; the node is additive and the end-edge change is a 2-line revert.

## Out of scope
- No BAF vs large-cap fund split (single MF bucket by decision); no per-property rental mapping
  (use the `other_income` aggregate); no inflation-adjusted annuity; no corpus drawdown fallback;
  no plan persistence. Do not touch the LLM nodes, chat agent, or Airtable write-back.

## Docs to update
PROJECT_OVERVIEW.md §5.3, §5.5, §7, §11; AGENTS.md "Known doc drift" #3 (terminal node).
