"""
loan_prepayment_consolidated.py
================================
Consolidates:
  - plan_prepayments  (goal-aware waterfall, freed SIP/EMI cascading)
  - build_prepayment_analysis  (marginal-gain knee detection)

Key design:
  1. build_prepayment_analysis  →  pure math engine, no state awareness
  2. _knee_capped_lump          →  caps snowball allocation at knee point
  3. plan_prepayments           →  orchestrates everything:
       guard → budget → snowball+knee → avalanche waterfall → freed cascade
"""

import copy
import math
import numpy as np
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from pprint import pprint
from typing import Any


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — PURE MATH HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def calculate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Standard EMI formula. annual_rate_pct is in % (e.g. 9.0 for 9%)."""
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return principal / tenure_months
    return principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)


def remaining_tenure(P: float, monthly_rate: float, emi: float) -> float:
    """
    Back-calculate remaining months from outstanding balance.
    monthly_rate is already divided (e.g. 0.09/12).
    Returns float('inf') if loan is non-amortizing.
    """
    if emi <= 0 or P <= 0:
        return 0.0
    if monthly_rate == 0:
        return math.ceil(P / emi)
    if emi <= P * monthly_rate:
        return float('inf')
    n = -math.log(1 - monthly_rate * P / emi) / math.log(1 + monthly_rate)
    return math.ceil(n)


def total_interest_remaining(P: float, emi: float, monthly_rate: float) -> float:
    """Total interest paid over remaining life of loan with no prepayment."""
    n = remaining_tenure(P, monthly_rate, emi)
    if n == float('inf'):
        return float('inf')
    return max(0.0, emi * n - P)


def _add_months(dt: date, months: int) -> date:
    return dt + relativedelta(months=months)


def _freed_by_year(close_date: date, emi: float) -> dict:
    return {close_date.year: emi}


def _safe(v: Any) -> Any:
    if v is None or v == float('inf'):
        return None
    return v


def max_extra_payment(P: float, r: float, emi: float) -> float:
    """Cap extra payment so we never overshoot the remaining balance."""
    if r == 0:
        return max(0.0, P - emi)
    return max(0.0, P - (emi - P * r))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — MARGINAL GAIN ENGINE  (from build_prepayment_analysis)
# ══════════════════════════════════════════════════════════════════════════════

def build_prepayment_analysis(
    principal: float,
    annual_rate_pct: float,
    tenure_months: int,
    step_size: float = 50_000,
    max_prepayment: float = None,
    knee_threshold_pct: float = 0.70,
) -> tuple[pd.DataFrame, dict]:
    """
    Sweep lump-sum prepayment amounts from 0 → max_prepayment and identify
    the knee of the marginal-gain curve.

    Parameters
    ----------
    principal          : outstanding loan balance (₹)
    annual_rate_pct    : annual interest rate in % (e.g. 9.0)
    tenure_months      : remaining tenure in months
    step_size          : ₹ increment between scenarios
    max_prepayment     : upper bound for sweep (default: principal − step_size)
    knee_threshold_pct : knee = first step where MG < threshold × peak_MG
                         0.70 means "MG drops to 70% of peak" (more conservative
                         than 0.50; keeps more money available for goals)

    Returns
    -------
    df        : DataFrame with one row per scenario
    knee_info : dict with peak MG, knee prepayment, interest saved, months saved
    """
    if max_prepayment is None:
        max_prepayment = max(0.0, principal - step_size)

    original_emi = calculate_emi(principal, annual_rate_pct, tenure_months)

    def _sim(new_P: float) -> tuple[float, int]:
        """Return (total_interest, months) for a given post-prepayment balance."""
        if new_P <= 0:
            return 0.0, 0
        r = annual_rate_pct / 12 / 100
        balance = new_P
        total_int = 0.0
        months = 0
        while balance > 1 and months < 2_000:
            interest = balance * r
            principal_component = original_emi - interest
            if principal_component <= 0:
                raise ValueError(
                    f"EMI Rs.{original_emi:,.0f} is too low to amortize "
                    f"new balance Rs.{new_P:,.0f} at {annual_rate_pct}%."
                )
            if principal_component > balance:
                total_int += interest
                months += 1
                break
            balance -= principal_component
            total_int += interest
            months += 1
        return total_int, months

    original_total_int, original_months = _sim(principal)

    prepayments = np.arange(0, min(max_prepayment, principal) + step_size, step_size)
    rows = []
    for p in prepayments:
        new_P = principal - p
        if new_P <= 0:
            continue
        new_int, new_months = _sim(new_P)
        rows.append({
            "Prepayment_Amount":               round(p, 2),
            "Outstanding_After_Prepayment":    round(new_P, 2),
            "Original_EMI":                    round(original_emi, 2),
            "Original_Total_Interest":         round(original_total_int, 2),
            "New_Total_Interest":              round(new_int, 2),
            "Interest_Saved_S(P)":             round(original_total_int - new_int, 2),
            "Original_Remaining_Months":       original_months,
            "New_Remaining_Months":            new_months,
            "Months_Saved":                    original_months - new_months,
        })

    df = pd.DataFrame(rows)
    df["Marginal_Gain"] = df["Interest_Saved_S(P)"].diff()
    df.loc[df.index[0], "Marginal_Gain"] = float("nan")

    mg_peak     = df["Marginal_Gain"].max()
    knee_cutoff = knee_threshold_pct * mg_peak
    knee_row    = df[df["Marginal_Gain"] < knee_cutoff].head(1)

    if not knee_row.empty:
        knee_prepayment    = knee_row["Prepayment_Amount"].iloc[0]
        knee_interest_saved = knee_row["Interest_Saved_S(P)"].iloc[0]
        knee_mg            = knee_row["Marginal_Gain"].iloc[0]
        knee_months_saved  = knee_row["Months_Saved"].iloc[0]
    else:
        knee_prepayment = knee_interest_saved = knee_mg = knee_months_saved = None

    knee_info = {
        "Peak_Marginal_Gain":   round(mg_peak, 2) if not np.isnan(mg_peak) else None,
        "Knee_Cutoff":          round(knee_cutoff, 2) if not np.isnan(knee_cutoff) else None,
        "Knee_Prepayment":      knee_prepayment,
        "Knee_Interest_Saved":  knee_interest_saved,
        "Knee_Marginal_Gain":   knee_mg,
        "Months_Saved":         knee_months_saved,
        "Threshold_Used":       knee_threshold_pct,
    }

    return df, knee_info


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — LOAN SCORING  (from plan_prepayments)
# ══════════════════════════════════════════════════════════════════════════════

def _score_loan(L: dict, client_data: dict, today: date) -> float:
    """
    Armstrong Capital loan priority score.

    Loan Score     = (Rate Weight × 0.4) + (EMI Burden × 0.3) + (Tenure Risk × 0.3)
    Priority Score = (Loan Score  × 0.6) + (1/√remaining_years × 0.4)

    Rate Weight : >12% → 7 | 9–12% → 5 | <9% → 3
    EMI Burden  : >50% net income → 3 | 30–50% → 5 | <30% → 7
    Tenure Risk : loan extends past retirement → 10
                  else (remaining_years / years_to_retirement) × 100, capped 10
    """
    client_info     = client_data.get("client_data", {})
    inv             = client_data.get("investment_details", {})
    summary         = (inv.get("financial_summary") or [{}])[0]
    net_monthly_in  = (
        float(summary.get("monthly_salary", 0))
        + float(summary.get("other_income(rental/interest/other)", 0))
    )

    retirement_age  = int(client_info.get("retirement_age", 60))
    client_age      = int(client_info.get("client_age", 35))
    years_to_retire = max(1, retirement_age - client_age)

    rate_pct        = float(L.get("interest_rate", 0)) * 100
    emi             = float(L.get("emi_amount", 0))
    P               = float(L.get("outstanding_balance", 0))
    r               = float(L.get("interest_rate", 0)) / 12

    ten_months      = remaining_tenure(P, r, emi)
    remaining_years = (ten_months / 12) if ten_months != float("inf") else 50.0

    # Rate weight
    rate_w = 7 if rate_pct > 12 else (5 if rate_pct >= 9 else 3)

    # EMI burden
    emi_burden_pct = (emi / net_monthly_in * 100) if net_monthly_in else 0
    emi_score = 3 if emi_burden_pct > 50 else (5 if emi_burden_pct >= 30 else 7)

    # Tenure risk
    if remaining_years >= years_to_retire:
        tenure_risk = 10.0
    else:
        tenure_risk = min(10.0, (remaining_years / years_to_retire) * 100)

    loan_score     = (rate_w * 0.4) + (emi_score * 0.3) + (tenure_risk * 0.3)
    priority_score = (loan_score * 0.6) + ((1 / math.sqrt(max(0.01, remaining_years))) * 0.4)

    return round(priority_score, 4)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — KNEE-CAPPED LUMP SUM HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _knee_capped_lump(
    L: dict,
    available_lump: float,
    step_size: float = 50_000,
    knee_threshold_pct: float = 0.70,
) -> tuple[float, dict]:
    """
    Run build_prepayment_analysis for a single loan and return:
      - the knee-capped optimal lump sum (≤ available_lump)
      - the full knee_info dict (for reporting)

    If the loan is too small for a meaningful sweep, fall back to min(available, balance).
    """
    P          = float(L["outstanding_balance"])
    rate_pct   = float(L["interest_rate"]) * 100          # stored as decimal, convert to %
    emi        = float(L["emi_amount"])
    r_monthly  = float(L["interest_rate"]) / 12
    tenure_m   = remaining_tenure(P, r_monthly, emi)

    if tenure_m == float("inf") or P <= 0:
        return 0.0, {"note": "Non-amortizing or zero balance — no lump sum assigned."}

    tenure_m = int(tenure_m)

    # Cap sweep at available lump
    max_sweep  = min(available_lump, P - step_size)

    if max_sweep <= 0:
        # Available is smaller than one step — still use it if positive
        actual = min(available_lump, P)
        return round(actual, 2), {"note": "Lump sum < step_size; full available amount used.", "Knee_Prepayment": actual}

    try:
        _, knee_info = build_prepayment_analysis(
            principal          = P,
            annual_rate_pct    = rate_pct,
            tenure_months      = tenure_m,
            step_size          = step_size,
            max_prepayment     = max_sweep,
            knee_threshold_pct = knee_threshold_pct,
        )
    except ValueError as e:
        return 0.0, {"note": f"Simulation error: {e}"}

    knee_lump = knee_info.get("Knee_Prepayment")

    # Fallback: if no knee found, use full available amount
    if knee_lump is None:
        knee_lump = min(available_lump, P)
    else:
        knee_lump = min(float(knee_lump), available_lump, P)

    return round(knee_lump, 2), knee_info


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — WATERFALL SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def simulate_prepayment_waterfall(
    P_start: float,
    r: float,
    emi: float,
    lump: float,
    remaining_stepup: dict,
    start_date: date,
    current_extra: float,
    loan_type: str = "Unknown",
) -> tuple:
    """
    Month-by-month loan simulation with:
      - One-time lump-sum prepayment at start
      - Shared monthly extra budget (from surplus after goals)
      - Step-up injections from freed SIP / freed EMI schedule

    Returns
    -------
    (total_months, total_interest_paid, avg_monthly_extra,
     close_date, freed_by_year, actually_used_stepup,
     activated_stepup_years, leftover_stepup)
    """
    print(f"\n  [WATERFALL] {loan_type}")
    print(f"    P_start={P_start:,.0f}  lump={lump:,.0f}  extra={current_extra:,.0f}  "
          f"start={start_date}  stepups={remaining_stepup}")

    P = max(0.0, P_start - lump)

    # Loan fully closed by lump sum
    if P <= 0:
        close_date = start_date
        freed      = _freed_by_year(close_date, emi)
        print(f"    → Closed immediately by lump sum.")
        return 0, 0.0, 0.0, close_date, freed, 0.0, set(), remaining_stepup

    sorted_stepups           = sorted(remaining_stepup.items())
    month                    = 0
    total_interest_paid      = 0.0
    total_extra_paid         = 0.0
    current_date             = start_date
    activated_stepup_years   = set()
    active_extra_budget      = current_extra

    while P > 0 and month < 600:
        current_year = current_date.year

        # Absorb any step-ups that have become available this year
        new_sorted = []
        for yr, amt in sorted_stepups:
            if yr <= current_year:
                active_extra_budget += amt
                activated_stepup_years.add(yr)
            else:
                new_sorted.append((yr, amt))
        sorted_stepups = new_sorted

        cap = max_extra_payment(P, r, emi)
        E   = min(active_extra_budget, cap)

        interest_this_month = P * r
        principal_payment   = (emi + E) - interest_this_month

        if principal_payment <= 0:
            break

        total_interest_paid += interest_this_month
        total_extra_paid    += E
        P                    = max(0.0, P - principal_payment)
        month               += 1
        current_date         = _add_months(current_date, 1)

    close_date        = current_date
    avg_monthly_extra = total_extra_paid / month if month > 0 else 0.0
    freed             = _freed_by_year(close_date, emi)

    actually_used_stepup = sum(
        amt for yr, amt in remaining_stepup.items()
        if yr in activated_stepup_years
    )
    leftover_stepup = dict(new_sorted)  # stepups not yet consumed

    print(f"    → Close={close_date}  months={month}  "
          f"int_paid={total_interest_paid:,.0f}  stepup_used={actually_used_stepup:,.0f}")

    return (
        month,
        total_interest_paid,
        avg_monthly_extra,
        close_date,
        freed,
        actually_used_stepup,
        activated_stepup_years,
        leftover_stepup,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def plan_prepayments(
    state: dict,
    step_size: float = 50_000,
    knee_threshold_pct: float = 0.70,
) -> dict:
    """
    Goal-aware loan prepayment planner.

    Pipeline
    --------
    1. Guard       — skip entirely if any post-retirement goal is unfunded
    2. Budget      — pull surplus + liquid pool from goal_funding state
    3. Knee sweep  — run marginal-gain analysis per loan, cap lump at knee
    4. Snowball    — assign knee-capped lump sums smallest-balance first
    5. Avalanche   — monthly extra + step-ups routed highest-score first
    6. Waterfall   — sequential simulation; each closed loan's freed EMI
                     cascades into the next loan's monthly budget
    7. Output      — per-loan results + freed timeline + cascade schedule

    Parameters
    ----------
    state               : LangGraph ClientState dict
    step_size           : ₹ granularity for marginal-gain sweep
    knee_threshold_pct  : 0.70 = knee at 70% of peak MG (conservative;
                          more money preserved for goals)
    """
    print("\n" + "=" * 120)
    print("NODE: plan_prepayments (consolidated)")
    print("=" * 120)

    client_data = copy.deepcopy(state["client_data"])
    liabilities = copy.deepcopy(client_data.get("liabilities", []))

    # ── Early exit: no liabilities ───────────────────────────────────────────
    if not liabilities:
        print("\n[DEBUG] No liabilities. Skipping.")
        return _empty_output(state)

    today       = date.today()
    client_info = client_data.get("client_data", {})
    ret_age     = int(client_info.get("retirement_age", 60))
    cli_age     = int(client_info.get("client_age", 35))
    ret_year    = today.year + (ret_age - cli_age)

    print(f"\n[DEBUG] Today={today} | Age={cli_age} | Ret year={ret_year}")

    # ── GUARD: skip if any post-retirement goal is unfunded ──────────────────
    last_goal_funding = state["goal_funding"][-1]
    unfunded_post_ret = [
        g for g in last_goal_funding.get("goals", [])
        if g.get("target_year", 0) > ret_year
        and g.get("goal_type", "") != "loan_closure"
        and float(g.get("corpus_gap", 0) or g.get("corpus_needed", 0)) > 0
    ]

    if unfunded_post_ret:
        print(f"\n[GUARD] {len(unfunded_post_ret)} post-retirement goal(s) unfunded — skipping prepayment.")
        for g in unfunded_post_ret:
            print(f"  - {g['goal_name']} | gap={g.get('corpus_gap')}")
        return _guard_exit_output(state)

    # ── Budget: pulled from goal_funding (already net of goal SIPs) ─────────
    monthly_surplus = float(last_goal_funding.get("ending_monthly_surplus", 0))
    liquid_pool     = float(last_goal_funding.get("ending_liquid_pool", 0))

    freed_sip_schedule = {
        int(yr): float(v)
        for yr, v in last_goal_funding.get("ending_freed_sip_schedule", {}).items()
    }
    freed_emi_schedule = {
        int(yr): float(v)
        for yr, v in (state["freed_timeline"][0] if state.get("freed_timeline") else {}).items()
    }

    print(f"\n[BUDGET] surplus={monthly_surplus:,.0f}  liquid={liquid_pool:,.0f}")
    print(f"[BUDGET] freed_sip={freed_sip_schedule}  freed_emi={freed_emi_schedule}")

    # ── Step-up source selection ─────────────────────────────────────────────
    eligible_loans   = [L for L in liabilities if not L.get("is_under_penalty_period", False)]
    ineligible_loans = [L for L in liabilities if L.get("is_under_penalty_period", False)]

    # Reference: top-scored loan close year (to decide which stepup to use)
    _loan_close_year = _top_loan_close_year(eligible_loans, client_data, today)

    if freed_sip_schedule:
        stepup_schedule = {yr: v for yr, v in freed_sip_schedule.items() if yr < _loan_close_year}
        cascade_source  = "freed_sip_within_loan_tenure"
    elif freed_emi_schedule:
        stepup_schedule = {yr: v for yr, v in freed_emi_schedule.items() if yr < _loan_close_year}
        cascade_source  = "freed_emi"
    else:
        stepup_schedule = {}
        cascade_source  = "none"

    print(f"\n[STEPUP] source={cascade_source}  schedule={stepup_schedule}")

    # ── Score every eligible loan ────────────────────────────────────────────
    for L in eligible_loans:
        L["_score"] = _score_loan(L, client_data, today)

    # ── SNOWBALL + KNEE: assign lump sums, smallest balance first ────────────
    # But cap each loan's lump sum at the knee of its own marginal-gain curve.
    loans_snowball = sorted(eligible_loans, key=lambda x: float(x["outstanding_balance"]))
    remaining_lump = liquid_pool

    print(f"\n[LUMP] Snowball + knee-capped allocation  (pool={liquid_pool:,.0f})")

    for L in loans_snowball:
        if remaining_lump <= 0:
            L["_lump_assigned"] = 0.0
            L["_knee_info"]     = {}
            continue

        knee_lump, knee_info = _knee_capped_lump(
            L,
            available_lump     = remaining_lump,
            step_size          = step_size,
            knee_threshold_pct = knee_threshold_pct,
        )

        L["_lump_assigned"] = knee_lump
        L["_knee_info"]     = knee_info
        remaining_lump     -= knee_lump

        print(f"  {L['type']:30s}  balance={float(L['outstanding_balance']):>12,.0f}  "
              f"knee_lump={knee_lump:>10,.0f}  "
              f"int_saved@knee={knee_info.get('Knee_Interest_Saved') or 0:>10,.0f}  "
              f"months_saved={knee_info.get('Months_Saved') or 0:>4}  "
              f"lump_pool_left={remaining_lump:>10,.0f}")

    # Fill in 0 for any loan not reached
    for L in eligible_loans:
        L.setdefault("_lump_assigned", 0.0)
        L.setdefault("_knee_info",     {})

    # ── AVALANCHE: monthly extra routed to highest-score loans first ─────────
    loans_avalanche = sorted(eligible_loans, key=lambda x: x["_score"], reverse=True)

    # Fully closable by lump sum come first (close them cheaply and fast)
    fully_closable = [
        L for L in loans_snowball
        if L.get("_lump_assigned", 0.0) >= float(L["outstanding_balance"])
    ]
    remaining_eligible = [L for L in loans_avalanche if L not in fully_closable]
    execution_order    = fully_closable + remaining_eligible + ineligible_loans

    print("\n[EXECUTION ORDER]")
    for i, L in enumerate(execution_order, 1):
        print(f"  {i}. {L['type']:30s}  score={L.get('_score')}  "
              f"lump={L.get('_lump_assigned', 0):,.0f}  "
              f"penalty={L.get('is_under_penalty_period', False)}")

    # ── WATERFALL SIMULATION ─────────────────────────────────────────────────
    per_loan_results         = []
    freed_aggregate          = {}
    total_allocated_lump     = 0.0
    freed_sip_utilized_total = 0.0
    all_activated_stepup_yrs = set()

    shared_stepup = dict(stepup_schedule)
    waterfall_budget = max(0.0, monthly_surplus)
    waterfall_date   = today

    for L in execution_order:
        P          = float(L["outstanding_balance"])
        i_annual   = float(L["interest_rate"])          # decimal (e.g. 0.09)
        emi        = float(L["emi_amount"])
        r          = i_annual / 12.0
        is_eligible = not L.get("is_under_penalty_period", False)
        pen_months  = L.get("time_left_to_come_out_of_penalty_period(months)")

        base_months = remaining_tenure(P, r, emi)
        if base_months == float("inf"):
            per_loan_results.append(_non_amortizing_result(L, is_eligible, pen_months))
            continue

        base_close_dt  = _add_months(today, int(base_months))
        base_interest  = total_interest_remaining(P, emi, r)

        if is_eligible:
            LUMP = L.get("_lump_assigned", 0.0)
            (
                acc_months, acc_interest, avg_extra,
                acc_close_dt, freed, used_stepup,
                activated_yrs, shared_stepup,
            ) = simulate_prepayment_waterfall(
                P, r, emi, LUMP,
                shared_stepup, waterfall_date, waterfall_budget,
                loan_type=L["type"],
            )

            saved_interest = base_interest - acc_interest

            # No real acceleration? Revert to baseline
            if acc_months >= int(base_months):
                saved_interest = 0.0
                avg_extra      = 0.0
                acc_months     = int(base_months)
                acc_close_dt   = base_close_dt
                freed          = _freed_by_year(base_close_dt, emi)
                used_stepup    = 0.0
                activated_yrs  = set()

            # Cascade: freed EMI flows into next loan's budget
            waterfall_budget += emi
            waterfall_date    = acc_close_dt

            all_activated_stepup_yrs.update(activated_yrs)
            freed_sip_utilized_total += used_stepup
            total_allocated_lump     += LUMP
            knee_info_out             = L.get("_knee_info", {})

        else:
            # Penalty period — baseline only, no prepayment
            LUMP           = 0.0
            acc_months     = int(base_months)
            acc_interest   = base_interest
            saved_interest = 0.0
            avg_extra      = 0.0
            used_stepup    = 0.0
            acc_close_dt   = base_close_dt
            freed          = _freed_by_year(base_close_dt, emi)
            knee_info_out  = {}

        for yr, amt in freed.items():
            freed_aggregate[yr] = freed_aggregate.get(yr, 0.0) + amt

        per_loan_results.append({
            "type":                       L["type"],
            "loan_score":                 L.get("_score") if is_eligible else None,
            "baseline_months":            _safe(base_months),
            "baseline_close_date":        base_close_dt.isoformat(),
            "accelerated_months":         _safe(acc_months),
            "accelerated_close_date":     acc_close_dt.isoformat(),
            "interest_saved":             round(float(saved_interest), 2),
            "avg_monthly_extra_applied":  round(float(avg_extra), 2),
            "lump_sum_applied":           round(float(LUMP), 2),
            "freed_by_year":              {k: round(float(v), 2) for k, v in freed.items()},
            "freed_sip_utilized":         round(float(used_stepup), 2),
            "allocation_method_monthly":  "avalanche_stepup" if is_eligible else "skipped_penalty",
            "allocation_method_lump":     "snowball_knee_capped" if is_eligible else "skipped_penalty",
            "penalty_expires_in_months":  pen_months,
            # Marginal gain analysis for this loan
            "knee_analysis": {
                "knee_prepayment":    knee_info_out.get("Knee_Prepayment"),
                "knee_interest_saved": knee_info_out.get("Knee_Interest_Saved"),
                "knee_months_saved":  knee_info_out.get("Months_Saved"),
                "peak_marginal_gain": knee_info_out.get("Peak_Marginal_Gain"),
                "threshold_used":     knee_info_out.get("Threshold_Used"),
                "note":               knee_info_out.get("note"),
            } if is_eligible else None,
        })

    # ── Assemble final result ─────────────────────────────────────────────────
    result = {
        "per_loan":                  per_loan_results,
        "freed_timeline":            {k: round(float(v), 2) for k, v in sorted(freed_aggregate.items())},
        "allocated_monthly_surplus": round(float(monthly_surplus), 2),
        "allocated_lump_sum":        round(float(total_allocated_lump), 2),
        "lump_pool_remaining":       round(float(remaining_lump), 2),
        "freed_sip_utilized_total":  round(float(freed_sip_utilized_total), 2),
        "cascade_schedule": {
            str(yr): stepup_schedule[yr]
            for yr in sorted(all_activated_stepup_yrs)
            if yr in stepup_schedule
        },
        "assumptions": {
            "today":                    today.isoformat(),
            "monthly_budget_today":     round(float(monthly_surplus), 2),
            "liquid_pool_available":    round(float(liquid_pool), 2),
            "lump_strategy":            "snowball_by_balance_knee_capped",
            "monthly_strategy":         "avalanche_by_loan_score",
            "stepup_source":            cascade_source,
            "stepup_schedule":          {str(k): v for k, v in sorted(stepup_schedule.items())},
            "knee_threshold_pct":       knee_threshold_pct,
            "step_size":                step_size,
            "simulation":               "sequential_waterfall_realistic",
        },
        "unused_monthly_surplus": 0.0,
    }

    _print_summary(result)

    return {
        "liability_allocation":   [result],
        "freed_timeline":         [result["freed_timeline"]],
        "used_monthly_surplus":   [float(monthly_surplus)],
        "used_liquid_surplus":    [float(total_allocated_lump)],
        "EMI_allocated":          True,
        "loan_prepayed_times":    state.get("loan_prepayed_times", 0) + 1,
        "unused_monthly_surplus": [result["unused_monthly_surplus"]],
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — PRIVATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _top_loan_close_year(eligible_loans: list, client_data: dict, today: date) -> int:
    if not eligible_loans:
        return today.year + 50
    scored = sorted(eligible_loans, key=lambda L: _score_loan(L, client_data, today), reverse=True)
    top    = scored[0]
    P      = float(top["outstanding_balance"])
    r      = float(top["interest_rate"]) / 12.0
    emi    = float(top["emi_amount"])
    n      = remaining_tenure(P, r, emi)
    if n == float("inf"):
        return today.year + 50
    return _add_months(today, int(n)).year


def _non_amortizing_result(L: dict, is_eligible: bool, pen_months) -> dict:
    return {
        "type":                      L["type"],
        "loan_score":                L.get("_score") if is_eligible else None,
        "baseline_months":           None,
        "baseline_close_date":       None,
        "accelerated_months":        None,
        "accelerated_close_date":    None,
        "interest_saved":            None,
        "avg_monthly_extra_applied": 0.0,
        "lump_sum_applied":          0.0,
        "freed_by_year":             {},
        "freed_sip_utilized":        0.0,
        "allocation_method_monthly": "avalanche_stepup" if is_eligible else "skipped_penalty",
        "allocation_method_lump":    "snowball_knee_capped" if is_eligible else "skipped_penalty",
        "penalty_expires_in_months": pen_months,
        "knee_analysis":             None,
        "note":                      "EMI <= monthly interest; loan is not amortizing.",
    }


def _empty_output(state: dict) -> dict:
    surplus = state.get("monthly_surplus", 0.0)
    return {
        "liability_allocation":   [{"per_loan": [], "freed_timeline": {},
                                    "allocated_monthly_surplus": 0.0,
                                    "allocated_lump_sum": 0.0, "assumptions": {},
                                    "unused_monthly_surplus": surplus}],
        "freed_timeline":         [{}],
        "used_monthly_surplus":   [0.0],
        "used_liquid_surplus":    [0.0],
        "EMI_allocated":          False,
        "loan_prepayed_times":    state.get("loan_prepayed_times", 0),
        "unused_monthly_surplus": [surplus],
    }


def _guard_exit_output(state: dict) -> dict:
    baseline = (state.get("liability_allocation") or [{}])[0]
    return {
        "liability_allocation":   [baseline],
        "freed_timeline":         [baseline.get("freed_timeline", {})],
        "used_monthly_surplus":   [0.0],
        "used_liquid_surplus":    [0.0],
        "EMI_allocated":          False,
        "loan_prepayed_times":    state.get("loan_prepayed_times", 0),
        "unused_monthly_surplus": [state.get("monthly_surplus", 0.0)],
    }


def _print_summary(result: dict) -> None:
    print("\n" + "=" * 120)
    print("FINAL SUMMARY")
    print("=" * 120)
    print(f"  Allocated Monthly Surplus : {result['allocated_monthly_surplus']:,.2f}")
    print(f"  Allocated Lump Sum        : {result['allocated_lump_sum']:,.2f}")
    print(f"  Lump Pool Remaining       : {result['lump_pool_remaining']:,.2f}  ← redirected to goals/investments")
    print(f"  Freed SIP Utilized Total  : {result['freed_sip_utilized_total']:,.2f}")
    print(f"  Freed Timeline            : {result['freed_timeline']}")
    print(f"  Cascade Schedule          : {result['cascade_schedule']}")
    print(f"\n  Per-Loan Summary:")
    for loan in result["per_loan"]:
        ka = loan.get("knee_analysis") or {}
        print(f"    {loan['type']:30s}  "
              f"base={loan['baseline_months']}m → acc={loan['accelerated_months']}m  |  "
              f"int_saved={loan['interest_saved'] or 0:>10,.0f}  |  "
              f"lump={loan['lump_sum_applied']:>10,.0f}  |  "
              f"knee={ka.get('knee_prepayment') or 0:>10,.0f}  |  "
              f"knee_int_saved={ka.get('knee_interest_saved') or 0:>10,.0f}")
    print("=" * 120)
