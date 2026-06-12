# Plan 0004 — Annuity shows only used sources; wealth-at-retirement shows leftover ESOP/RSU

- **Status:** ready-for-execution
- **Branch / PR:** `feat/annuity-used-only-and-leftover-esop-rsu`
- **Owner:** Claude Code (planner)

## Goal
Two coupled display changes to the retirement output:
1. **Retirement annuity** — show only the sources actually drawn on, each **capped to the amount
   used** to reach the desired annuity; omit sources that aren't needed (no more greyed-out
   "NOT REQUIRED" rows). "Total available" becomes "Total used".
2. **Wealth at retirement** — when ESOP/RSU pools are **left over**, show them as corpus rows,
   the same way the annuity currently surfaces ESOP/RSU.

## Context & rationale
The annuity node (`calculate_retirement_annuity`) builds a `sources` list in fixed priority order
and tags each row `required: true/false` based on whether it was reached before the desired annual
income was met ([retirement_nodes.py:627-668](../../Financial_Planning/Nodes/retirement_nodes.py#L627-L668)).
The UI greys out `required: false` rows and labels them "not required"
([FinancialPlanPanel.tsx:1232-1284](../../components/FinancialPlanPanel.tsx#L1232-L1284)). The user
wants those un-used rows **gone**, and the used rows to show only the **portion actually used**
(decision: "cap to amount used"), so the rows sum to the desired annuity.

The "Wealth at retirement" node (`wealth_at_retirement`) builds a corpus `breakdown`
(EPF/PPF/NPS/FD/real estate/SIP/freed-SIP/lumpsum) at
[retirement_nodes.py:500-509](../../Financial_Planning/Nodes/retirement_nodes.py#L500-L509) but
omits ESOP/RSU. The user wants leftover ESOP/RSU shown there.

**Priority order is unchanged** (decision: keep **ESOP → RSU → rental → FD → MF**). With ESOP/RSU
first, the annuity is typically funded by ESOP yield (capped to the target), and the other sources
drop off the table. Because the annuity is **yield-only (principal kept)**, the ESOP/RSU *corpus*
still exists at retirement, so it legitimately appears as wealth — exactly the way FD already shows
in **both** views (FD corpus in wealth-at-retirement, FD interest in the annuity). This is
intentional double-representation of corpus vs. income, not double-counting, and is why no
reordering is needed.

## Affected files
- `Financial_Planning/Nodes/retirement_nodes.py` — **edit** (nodes `calculate_retirement_annuity`
  and `wealth_at_retirement`).
- `backend/financial_plan_runner.py` — **edit** (`_war_labels` map only).
- `components/FinancialPlanPanel.tsx` — **edit** (one label: "Total available" → "Total used").
- `Financial_Planning/tests/test_retirement_annuity.py` — **edit** (annuity capping/hiding) and a
  new `test_wealth_at_retirement_esop_rsu.py` — **create**.
- `PROJECT_OVERVIEW.md` — **edit** (annuity table semantics + wealth breakdown sources).

## Implementation steps

### Part A — Annuity: show only used sources, capped to amount used

In `calculate_retirement_annuity`, replace the source-building loop and totals
([retirement_nodes.py:627-668](../../Financial_Planning/Nodes/retirement_nodes.py#L627-L668)).
`ordered_candidates` (lines 630-636) stays **exactly as-is** (priority unchanged).

Replace lines **627-668** (`desired_annual = ...` through the end of the `result` dict) with:

```python
    desired_annual = desired_monthly_annuity * 12

    # Achievability is judged on the FULL (uncapped) yield capacity of every source.
    full_total_annual = sum(
        annual_income for (_k, _l, _r, annual_income, _c, _b) in ordered_candidates
        if annual_income > 0
    )
    achievable = full_total_annual >= desired_annual

    # Display only the sources actually drawn on, in priority order, each capped to
    # the remaining need. Once the desired annuity is met, the remaining (cheaper-
    # ranked) sources are unused and omitted entirely.
    sources: list[dict] = []
    cumulative = 0.0
    for key, label, rate_str, annual_income, corpus_fv, remaining_base in ordered_candidates:
        if annual_income <= 0:
            continue
        remaining_need = desired_annual - cumulative
        if remaining_need <= 0:
            break  # desired met — everything below is unused, so don't show it
        used = min(annual_income, remaining_need)
        cumulative += used
        sources.append(
            _source_row(key, label, rate_str, used, corpus_fv, remaining_base, True)
        )

    used_total_annual = cumulative  # == desired_annual when achievable, else < desired
    max_monthly = full_total_annual / 12 if full_total_annual > 0 else 0.0
    used_monthly = used_total_annual / 12
    shortfall_monthly = max(0.0, desired_monthly_annuity - max_monthly)
    achievable_monthly = desired_monthly_annuity if achievable else used_monthly

    result = {
        "model": "income_preservation",
        "retirement_year": retirement_year,
        "retirement_age": retirement_age,
        "life_expectancy": 85,
        "desired_monthly_annuity": round(desired_monthly_annuity, 2),
        "achievable": achievable,
        "achievable_monthly_annuity": round(achievable_monthly, 2),
        "max_monthly_annuity": round(max_monthly, 2),      # true uncapped capacity
        "shortfall_monthly": round(shortfall_monthly, 2),
        "surplus_income_monthly": round(surplus_income_monthly, 2),
        "total_available_monthly": round(used_monthly, 2),  # drives the "Total used" row
        "sources": sources,
    }
```

Notes:
- Every emitted row now has `required=True`, so the UI's greyed/"not required" styling never
  triggers (left in place, harmless).
- A row's `monthly_income` is the **capped used** amount; `corpus_fv` / `remaining_base` still
  reflect the underlying asset (truthful: ESOP keeps principal, only part of its yield is used).
- When **not achievable**, `remaining_need` never reaches 0, so every positive source shows at full
  income and `used_total_annual` = `full_total_annual` (< desired) — the shortfall path is intact.

### Part B — Annuity UI label
In [FinancialPlanPanel.tsx:1287](../../components/FinancialPlanPanel.tsx#L1287), change the total
row label `Total available` → `Total used`. (Value binding at line 1290 is unchanged — it already
reads `total_available_monthly`, which now carries the used total.)

### Part C — Wealth at retirement: add leftover ESOP/RSU corpus

In `wealth_at_retirement`, insert after the "Real Estate" block (after line 477, before the
"SIP / Lumpsum" block at line 479). `calculate_future_value` and `get_rsu_growth_rate` are already
imported (lines 18-20); `invest_detail` is bound at line 442.

```python
    # ── 3b. Leftover ESOP / RSU (remaining pools after goal allocation) ──
    oga_state = state.get('optimal_goal_allocation', {}) or {}
    goals_state = oga_state.get('goals', []) or []
    rsu_portfolio = oga_state.get('rsu_portfolio', []) or []

    # ESOP: 60% usable cap on vested value, less what goals already consumed.
    esop_rate = 0.12
    esop_usable_cap = 0.60
    vested_total = sum(
        float(e.get('vested_esops_value', 0) or 0)
        for e in (invest_detail.get('esops') or [])
    )
    esop_usable = vested_total * esop_usable_cap
    esop_consumed = 0.0
    for goal in goals_state:
        for fund in goal.get('funded_from') or []:
            if fund.get('type') == 'esop_funds':
                esop_consumed += float(fund.get('pv_allocated_today', 0) or 0)
    esop_remaining = max(0.0, esop_usable - esop_consumed)
    esop_fv = calculate_future_value(esop_remaining, esop_rate, years_to_ret) if esop_remaining > 0 else 0.0

    # RSU: remaining tracker value across portfolio, grown at the RSU growth rate.
    rsu_rate = get_rsu_growth_rate(invest_detail)
    rsu_remaining = sum(float(p.get('rsu_remaining', 0) or 0) for p in rsu_portfolio)
    rsu_fv = calculate_future_value(rsu_remaining, rsu_rate, years_to_ret) if rsu_remaining > 0 else 0.0
```

This mirrors the annuity node's ESOP/RSU math
([retirement_nodes.py:560-580](../../Financial_Planning/Nodes/retirement_nodes.py#L560-L580)) so the
two views agree on the leftover figures.

Then in step **5. Aggregate totals** (lines 496-498) add the two FVs:

```python
    total_corpus = (fd_fv + epf_fv + ppf_fv + nps_fv + real_estate_fv
                    + sip_fv_retirement + freed_sip_fv_retirement + lumpsum_fv_retirement
                    + esop_fv + rsu_fv)
```

And in `wealth_breakdown` (lines 500-509) add two entries after `real_estate`:

```python
        "esop":        {"future_value": round(esop_fv, 2),               "rate": f"{esop_rate * 100:.1f}%"},
        "rsu":         {"future_value": round(rsu_fv, 2),                "rate": f"{rsu_rate * 100:.1f}%"},
```

Both runner and UI already drop rows whose `future_value <= 0`, so a client with no leftover
ESOP/RSU shows no new rows (parity with today).

### Part D — Runner labels
In `backend/financial_plan_runner.py`, `_war_labels`
([financial_plan_runner.py:602-611](../../backend/financial_plan_runner.py#L602-L611)) add:

```python
            "esop": "ESOP (leftover)",
            "rsu": "RSU (leftover)",
```

(Without these, the `.title()` fallback would render "Esop"/"Rsu".) No other runner change — the
existing loop maps any breakdown key into a row and skips `fv <= 0`.

### Part E — Tests
- **Annuity (edit `test_retirement_annuity.py`):**
  - Desired annuity fully met by the first source: assert only that one source is returned,
    its `monthly_income` equals the desired monthly annuity (capped), and
    `total_available_monthly == desired_monthly_annuity`.
  - Desired met across several sources: assert the last source is capped so the rows sum to
    desired, and no un-needed source appears.
  - Shortfall case: assert every positive source appears at full income, `achievable is False`,
    and `total_available_monthly` < desired.
- **Wealth (new `test_wealth_at_retirement_esop_rsu.py`):** build a `state` with
  `investment_details.esops`, an `optimal_goal_allocation` with an `esop_funds` consumption and a
  `rsu_portfolio` carrying `rsu_remaining`; assert `breakdown["esop"]/["rsu"]` future values match
  `calculate_future_value(...)`, `total_corpus` includes both, and that zero-leftover yields FV `0`.

### Part F — Docs
`PROJECT_OVERVIEW.md`: update the annuity section to state the table shows only used sources capped
to the amount used ("Total used"), and add ESOP/RSU leftover to the wealth-at-retirement corpus
source list. Reconcile with the "Known doc drift" note in `AGENTS.md` first.

## Contract / interface changes
- `retirement_annuity.sources` now contains **only used** rows, each `monthly_income` capped to the
  portion used; all rows have `required: true`. `total_available_monthly` now = the used total
  (≤ desired). `max_monthly_annuity` remains the true uncapped capacity. No field added/removed.
- `wealth_at_retirement.breakdown` (and `wealth_at_retirement_preview.rows`) gains two optional
  keys: `esop`, `rsu`. Additive.
- UI: one static label string change. No API route, env var, or React state-shape change. No
  workflow node added/removed.

## Env / ports touched
None.

## Acceptance criteria & how to verify
- Annuity table lists only the sources actually used; the "NOT REQUIRED" row is gone; the rows sum
  to the desired annuity; the total row reads "Total used" with the desired figure (or the lower
  achievable figure on a shortfall).
- For a client with leftover vested ESOP and/or RSU remaining, "Wealth at retirement" shows
  "ESOP (leftover)" / "RSU (leftover)" rows and the donut/total include them; a client with none
  shows no new rows.
- `POST /api/financial-plan/run` → 200; `annuity_preview.sources` has no `required:false` rows;
  `wealth_at_retirement_preview.rows` carries the new keys when applicable.
- `pytest Financial_Planning/tests/ -k "annuity or wealth or esop or rsu"` passes.

## Tests
Per Part E, plus one manual end-to-end run through the panel to confirm both sections render.

## Risks & rollback
- **Risk:** an asset's yield used in the annuity AND its corpus shown in wealth reads as
  double-counting. Mitigated: identical to existing FD behavior; sections are never summed; labels
  say "(leftover)". Flag for user review.
- **Risk:** capping changes `total_available_monthly` semantics; verified only two UI bindings use
  annuity fields ([FinancialPlanPanel.tsx:1198,1290](../../components/FinancialPlanPanel.tsx#L1198))
  and both stay correct.
- **Rollback:** revert the annuity loop, the wealth ESOP/RSU block + two breakdown keys + the
  `total_corpus` addends, the two `_war_labels` entries, and the one UI label. Additive/local; no
  migration.

## Out of scope
- **Priority order is NOT changed** — ESOP/RSU stay first (per user decision).
- RSU/ESOP allocation/consumption logic in `allocations_nodes.py` and `optimal_goal_allocation`.
- The donut/table render structure — only the one annuity label string changes.

## Docs to update
`PROJECT_OVERVIEW.md` — annuity table semantics + wealth-at-retirement corpus sources (Part F).
