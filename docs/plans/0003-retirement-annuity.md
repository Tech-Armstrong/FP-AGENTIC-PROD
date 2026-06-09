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

**Decided model (confirmed with user over two rounds of Q&A):**
- **Income-preservation for EVERY source — principal is never spent.** The annuity is funded only by
  the *income/yield* each source throws off (interest, fund yield, ESOP/RSU growth). Per source:
  `annual_income = value_at_retirement × yield_rate`. We do **not** use
  `calculate_present_value_annuity` and we do **not** draw down/consume any pool — including ESOP/RSU.
- **Priority order: ESOP → RSU → rental/other income → FD → mutual funds.** ESOP and RSU yield is
  tapped first, then recurring rental/other income, then FD interest, then mutual-fund yield. Mutual
  funds are a single bucket (no BAF/large-cap tag exists in the data), so "FD > BAF > large-cap"
  collapses to FD → MF. Priority only decides which sources are "required" to reach the desired
  annuity (for the breakdown); since principal is preserved and incomes just sum, nothing is consumed.
- **ESOP/RSU use the remaining-after-education pool, within the existing 60% usable cap.** The annuity
  node runs after goal allocation, so education goals may already have used some ESOP/RSU:
  - **RSU:** sum of `rsu_remaining` across `optimal_goal_allocation.rsu_portfolio` entries
    (the RSU tracker value = `total_rsu_value × 60% − consumed`). The annuity taps the **yield** of
    this remaining pool — it does **not** reduce `rsu_remaining` further (income-only).
  - **ESOP:** `vested_esops_value × 60% − (ESOP already consumed by education)`, where consumed =
    Σ `pv_allocated_today` over goal `funded_from` entries of type `esop_funds`.
- **Recurring rental/other income** comes from `financial_summary[0]['other_income(rental/interest/other)']`
  (the populated aggregate; per-property rent isn't mapped today).
- If total available income < desired → report **max achievable annuity** and the monthly shortfall.
- **Inputs `desired_monthly_annuity` and `retirement_age` are user-given** (for testing): delivered
  via the existing `overrides` payload **and** new UI input fields, mirroring the rate-override pattern.

Relevant architecture: PROJECT_OVERVIEW §5.3 (node DAG — currently ends `wealth_at_retirement → END`),
§5.5 (per-node table), §7 (RSU/ESOP utilization + tracker `rsu_remaining`), §11 (`summary` shape +
`PlanOverrides`).

### Assumptions (tunable; call out in code comments)
- Desired annuity is a **retirement-year nominal** monthly figure (not inflation-adjusted in v1).
- Recurring `other_income` is used at face value (not grown to retirement); it conflates
  rental/interest/other, which is acceptable per the decision.
- Yield rates: **ESOP** = 12% (matches `allocations_nodes.py` `ESOP_GROWTH_RATE`); **RSU** =
  `get_rsu_growth_rate(...)` (default 10%); **FD** = its `interest_rate` (default 6.5%); **MF** =
  `expected_annual_return` (default 12%, also settable via the existing `mf_expected_return`
  override) — flag MF as optimistic.
- Each source's **value at retirement** is grown to the retirement year with `calculate_future_value`
  before applying its yield (FD already grown by `wealth_at_retirement`; ESOP/RSU remaining and MF
  grown the same way). The RSU-remaining time basis is approximate (the tracker value mixes vest-year
  projections) — acceptable for v1; note it.
- `life_expectancy = 85` (existing constant) is informational only — in an income-preservation model
  income is perpetual, so 85 does not bound the math (kept for display).
- The annuity is **income-only**, so it does **not** mutate `rsu_remaining` / the RSU tracker; it
  merely reads the remaining pool and reports the yield it contributes.

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
`calculate_future_value` (`Utilities/utility_functions.py`) and `get_rsu_growth_rate`
(`RSU/constants.py`). Read inputs (the whole payload is `state['client_data']`):

- `personal = state['client_data']['client_data']` → `retirement_age`, `desired_monthly_annuity`
  (new field injected by override; if `<= 0` or missing, return `{}` so the UI section hides).
- `invest = state['client_data']['investment_details']`.
- `surplus_income_monthly = invest['financial_summary'][0]['other_income(rental/interest/other)']` (default 0).
- `years_to_ret = state['required_retirement_corpus']['client_info']['years_to_retirement']`.
- `retirement_year = state['wealth_at_retirement']['retirement_year']` (fallback `date.today().year + years_to_ret`).
- `goals = state['optimal_goal_allocation'].get('goals', [])`;
  `rsu_portfolio = state['optimal_goal_allocation'].get('rsu_portfolio', [])`.

Compute each source's **value at retirement** then **annual income = value × yield** (principal
preserved — nothing consumed). Build the `sources` list in this exact priority order:

1. **ESOP** (`key="esop"`, rate `"12.0%"`):
   - `vested = Σ e['vested_esops_value']` over `invest.get('esops', [])`; `esop_usable = vested * 0.60`.
   - `esop_consumed = Σ f['pv_allocated_today']` over `g['funded_from']` (all goals) where
     `f['type'] == 'esop_funds'`.
   - `esop_remaining = max(0, esop_usable - esop_consumed)`;
     `esop_fv = calculate_future_value(esop_remaining, 0.12, years_to_ret)`;
     `esop_income = esop_fv * 0.12`. Carry `corpus_fv = esop_fv`, `remaining_base = esop_remaining`.
2. **RSU** (`key="rsu"`, rate from `get_rsu_growth_rate(invest)`):
   - `rsu_remaining = Σ p.get('rsu_remaining', 0)` over `rsu_portfolio` (the tracker leftovers).
   - `rsu_rate = get_rsu_growth_rate(invest)`;
     `rsu_fv = calculate_future_value(rsu_remaining, rsu_rate, years_to_ret)`;
     `rsu_income = rsu_fv * rsu_rate`. Carry `corpus_fv = rsu_fv`, `remaining_base = rsu_remaining`.
3. **Rental / other income** (`key="rental_other_income"`, rate `"-"`):
   `annual_income = surplus_income_monthly * 12` (face value; `corpus_fv = None`).
4. **FD** (`key="fixed_deposits"`): reuse
   `state['wealth_at_retirement']['breakdown']['fixed_deposits']` → `fd_fv = future_value`,
   `fd_rate` parsed from its `rate` string (fallback 0.065); `fd_income = fd_fv * fd_rate`.
5. **Mutual funds** (`key="mutual_funds"`, single bucket): over `invest.get('mutual_funds', [])`
   with `cv = current_value`, `r = expected_annual_return` (default 0.12):
   `mf_fv = Σ calculate_future_value(cv, r, years_to_ret)`, `mf_income = Σ fv * r`; representative
   `mf_rate` = first fund's `r`.

Algorithm (annualize: `desired_annual = desired_monthly_annuity * 12`):
```
ordered = [esop, rsu, rental_other, fixed_deposits, mutual_funds]   # priority order
cumulative = 0
for src in ordered:
    src.required = cumulative < desired_annual    # was this source needed to reach the target?
    cumulative += src.annual_income
total_available_annual = sum(src.annual_income for src in ordered)
achievable = total_available_annual >= desired_annual
max_monthly = total_available_annual / 12
shortfall_monthly = max(0.0, desired_monthly_annuity - max_monthly)
achievable_monthly = desired_monthly_annuity if achievable else max_monthly
```
Return:
```python
return {'retirement_annuity': {
  "model": "income_preservation",            # principal not consumed for any source
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
  "sources": [   # ordered ESOP, RSU, rental, FD, MF
    {"key":"esop","label":"ESOP yield","rate":"12.0%",
     "monthly_income":..,"annual_income":..,"corpus_fv":esop_fv,"remaining_base":esop_remaining,"required":bool},
    {"key":"rsu","label":"RSU yield","rate":rsu_rate_str,
     "monthly_income":..,"annual_income":..,"corpus_fv":rsu_fv,"remaining_base":rsu_remaining,"required":bool},
    {"key":"rental_other_income","label":"Rental / other income","rate":"-",
     "monthly_income":..,"annual_income":..,"corpus_fv":None,"remaining_base":None,"required":bool},
    {"key":"fixed_deposits","label":"FD interest","rate":fd_rate_str,
     "monthly_income":..,"annual_income":..,"corpus_fv":fd_fv,"remaining_base":None,"required":bool},
    {"key":"mutual_funds","label":"Mutual fund yield","rate":mf_rate_str,
     "monthly_income":..,"annual_income":..,"corpus_fv":mf_fv,"remaining_base":None,"required":bool},
  ],
}}
```
Drop zero-income sources from `sources` (e.g. no ESOP/RSU) so the table stays clean. Match the
existing node's `print(...)` debug style. Read everything defensively (`.get(...)`, defaults) so a
missing field hides the section rather than 500-ing.

### 3. Workflow wiring — `Financial_Planning/Workflow/workflow.py`
- Import `calculate_retirement_annuity` alongside `wealth_at_retirement`.
- `graph.add_node('calculate_retirement_annuity', calculate_retirement_annuity)`.
- Replace the terminal edge `graph.add_edge('wealth_at_retirement', END)` with:
  `graph.add_edge('wealth_at_retirement', 'calculate_retirement_annuity')` then
  `graph.add_edge('calculate_retirement_annuity', END)`.

### 4. Summary contract — `backend/financial_plan_runner.py`
In `summarize_plan_state`, mirror the `wealth_at_retirement_preview` block (~L597-635): read
`state.get('retirement_annuity')`, and if it has `sources`, set `annuity_preview = <that dict>`
(it's already UI-ready). Add `"annuity_preview": annuity_preview` to the returned `summary` dict
(near `wealth_at_retirement_preview` / `rsu_portfolio_preview`, ~L698-700).

### 5. Override inputs (backend) — `backend-airtable/main.py`
- `PlanOverrides` (L107-112): add `desired_monthly_annuity: float | None = None` and
  `retirement_age: int | None = None`.
- `apply_plan_overrides` (L619-650), after `deepcopy` — these are **not rates**, do not pass through
  `_normalize_rate`:
  - `if overrides.retirement_age is not None: payload["client_data"]["retirement_age"] = int(overrides.retirement_age)`
  - `if overrides.desired_monthly_annuity is not None: payload["client_data"]["desired_monthly_annuity"] = float(overrides.desired_monthly_annuity)`
  (Run endpoint already calls `apply_plan_overrides` before invoke, ~L771 — no change there.)

### 6. UI — `components/FinancialPlanPanel.tsx`
- **Types:** `PlanOverrides` (L134-142) already extended with `desired_monthly_annuity?` /
  `retirement_age?` — keep. Add to `PlanSummary` (L45-111): `annuity_preview?: { ... } | null;`
  matching the node output (scalars + `sources[]` with `key,label,rate,monthly_income,annual_income,
  corpus_fv,remaining_base,required`).
- **New section:** after the wealth-at-retirement block (insert after L1112, before the "Goal
  allocations" comment). Render only when `s.annuity_preview`. Use `ReviewSectionTitle` with a new
  lucide icon (`Banknote` or `Coins`; add to imports). Show:
  - Header: desired vs achievable monthly annuity + status pill — green "Achievable" when
    `achievable`, amber "Shortfall ₹X/mo" (`fmtInr(shortfall_monthly)`) otherwise.
  - Table of `sources` in order (label `@ rate` | monthly income via `fmtInr`); muted style +
    "not required" tag where `required === false`. For ESOP/RSU rows show a secondary caption tying
    to the tracker, e.g. "from remaining ESOP/RSU ₹{fmtInr(remaining_base)} (yield only — principal
    kept)". For FD/MF show "from ₹{fmtInr(corpus_fv)} corpus".
  - `PieChart` of source `monthly_income` contributions (reuse the wealth section's pattern).
  - Footnote: "Funded by income/yield only — ESOP, RSU, FD and funds keep their principal; the RSU
    tracker's remaining balance is unchanged."
  Reuse `fmtInr` (L176-179).
- **Input fields:** add two number inputs near the existing rate-override controls — "Desired monthly
  annuity (₹)" and "Retirement age" — plain numbers (do **not** route through `parseRateToDecimal`).

### 7. UI run wiring — `components/ClientsDashboard.tsx`
- Hold the two inputs as state (next to the rate-input state).
- At run time set `overrides.desired_monthly_annuity` / `overrides.retirement_age` directly from the
  raw numbers when provided (no rate parsing). They can trigger a fresh run but need not feed
  `planTabLabel`'s rate-diff logic.

### 8. Docs — `PROJECT_OVERVIEW.md` + `AGENTS.md`
- PROJECT_OVERVIEW §5.3 DAG end → `wealth_at_retirement → calculate_retirement_annuity → END`;
  §5.5 add the node row; §11 add `annuity_preview` to `summary` and the two new `PlanOverrides`
  fields. AGENTS.md "Known doc drift" #3 → terminal node is `calculate_retirement_annuity`.

## Contract / interface changes
- **Workflow:** +1 node `calculate_retirement_annuity`; end edges rerouted through it. +1 state key
  `retirement_annuity`.
- **API `POST /financial-plan/run` `overrides`:** + `desired_monthly_annuity?: number`,
  `retirement_age?: number`.
- **`summary`:** + `annuity_preview` object.
- **React state:** + two inputs in the Make-plan panel; `PlanSummary` type extended (`PlanOverrides`
  already done).

## Env / ports touched
None new. Make-plan path only: Next :3000 → FastAPI :8001 → workflow. Deterministic node, no
Azure/LLM changes. `AZURE_API_*` still required by the unrelated LLM nodes for a full run.

## Acceptance criteria & how to verify
1. `curl http://localhost:8001/health` → ok; backend boots without import errors after the new node.
2. **Example case** (retirement_age + ₹50k annuity via overrides; client with ₹50k/month
   `other_income`, no ESOP/RSU): `annuity_preview.achievable === true`; the rental row is `required`,
   ESOP/RSU rows absent (zero), FD/MF `required === false`. UI shows green "Achievable" with rental
   highlighted and FD/MF muted. Confirms "income covers it → core assets untouched."
3. **ESOP/RSU-first case** (client with vested ESOP and RSU `rsu_remaining > 0`): ESOP and RSU rows
   appear first and are marked `required` before rental/FD/MF; their income = remaining-pool FV ×
   yield; `rsu_remaining` in `rsu_portfolio_preview` is **unchanged** by the annuity.
4. **Shortfall case** (e.g. ₹3L/month): `achievable === false`, `shortfall_monthly > 0`,
   `max_monthly_annuity` = Σ all source incomes / 12, sources flagged `required` in priority order.
5. Section renders **immediately after** "Wealth at retirement"; Network shows
   `POST /api/financial-plan/run` 200 with `summary.annuity_preview` populated. Changing override
   `retirement_age` shifts `years_to_retirement` and all FVs/incomes.

## Tests
- Add `Financial_Planning/tests/test_retirement_annuity.py` for `calculate_retirement_annuity` with a
  minimal hand-built `state` (no Airtable/LLM): (a) rental covers annuity → achievable, ESOP/RSU/FD/MF
  not required; (b) ESOP+RSU remaining present → those rows come first and are `required`, income =
  FV×yield, and `rsu_remaining` is not mutated; (c) shortfall → correct `max_monthly_annuity` and
  priority `required` flags; (d) `desired_monthly_annuity <= 0` → returns `{}` (section hidden).
- Frontend: manual verification (no existing test covers `FinancialPlanPanel` rendering).

## Risks & rollback
- **Field nesting.** Verified: `retirement_age` at `payload['client_data']` (main.py:197);
  `other_income` at `payload['investment_details']['financial_summary'][0]` (main.py:576);
  `rsu_remaining` per entry in `optimal_goal_allocation.rsu_portfolio`
  (allocations_nodes.py:951); ESOP consumption via `funded_from` `esop_funds.pv_allocated_today`
  (allocations_nodes.py:749). Keep all reads defensive.
- **RSU-remaining time basis** is approximate (mixes vest-year projections) — acceptable for v1;
  flagged in code. If RSU market data is absent, `rsu_portfolio` is empty → RSU income 0 (non-blocking).
- **Rollback:** revert the touched files; the node is additive and the end-edge change is a 2-line revert.

## Out of scope
- No BAF vs large-cap fund split (single MF bucket); no per-property rental mapping (use the
  `other_income` aggregate); no inflation-adjusted annuity; **no consumption/drawdown of any pool**
  (income-only — the RSU tracker remaining is not changed by the annuity); no plan persistence. Do not
  touch the LLM nodes, chat agent, or Airtable write-back.

## Docs to update
PROJECT_OVERVIEW.md §5.3, §5.5, §7, §11; AGENTS.md "Known doc drift" #3 (terminal node).
