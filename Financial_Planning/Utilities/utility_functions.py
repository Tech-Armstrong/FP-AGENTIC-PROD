"""
Financial Calculation Utilities - Core Math Functions

What this file does:
This script provides core financial calculation utilities for the planning workflow.
It includes future value, present value, SIP calculations, loan math, and allocation helpers.

What this file contains:
- calculate_future_value: Computes FV with compound growth
- calculate_present_value_annuity: Calculates PV of annuity payment series
- ulip_future_value / epf_future_value / ppf_future_value / nps_future_value: Scheme-specific FV calculations
- calculate_sip_future_value / calculate_required_sip: Monthly SIP calculations
- lumpsum_required / future_value_lumpsum / sip_required: Investment requirement calculations
- apply_lumpsum_to_goal / apply_freed_sip_to_goal / apply_surplus_sip_to_goal: Goal funding allocation helpers
- remaining_tenure / max_extra_payment / total_interest: Loan amortization calculations
- months_to_close / close_date_from_months: Loan closure timeline functions
- present_loans_no_allocation: Baseline loan analysis without prepayment
- fv_monthly / fv_sip: Future value calculation utilities
- reduce_from_schedule / add_to_schedule: Schedule manipulation helpers
- _add_months / _freed_by_year / _safe: Utility helper functions
"""

from datetime import datetime
from typing import Any, List, Tuple, Dict
from math import log, ceil, isfinite
from datetime import datetime, date
import math
from math import isclose
import locale
locale.setlocale(locale.LC_ALL, 'C')
import json
from babel.numbers import format_decimal

def calculate_future_value(present_value, annual_rate, years):
        """Calculate future value with compound growth"""
        if years <= 0:
            return present_value
        return present_value * ((1 + annual_rate) ** years)

def calculate_present_value_annuity(annual_payment, discount_rate, years):
        """Calculate present value of annuity (series of payments)"""
        if years <= 0 or discount_rate == 0:
            return annual_payment * years
        return annual_payment * (1 - (1 + discount_rate) ** -years) / discount_rate

#def ulip_future_value(pmt, start, end, r_annual):
#    start, end = [datetime.strptime(d, "%d-%m-%Y") for d in (start, end)]
#    n = (end.year - start.year) * 12 + (end.month - start.month)
#    if n <= 0:                                  # safety
#        return 0.0
#    r_m = r_annual / 12
#    fv = pmt * (((1 + r_m) ** n - 1) / r_m) * (1 + r_m)
#    return round(fv, 2)

def epf_future_value(cur_val, m_contrib, r, years_left):
    if years_left <= 0:
        return cur_val
    fv_cur = cur_val * (1 + r) ** years_left
    
    annual_c = m_contrib * 12
    fv_c   = sum(annual_c * (1 + r) ** (years_left - i - 1)           # end-of-year flow
                 for i in range(years_left))
    return round(fv_cur + fv_c, 2)

def ppf_future_value(cur_val, annual_c, r, n):
    if n <= 0:
        return cur_val
    fv_c   = annual_c * (((1 + r) ** n - 1) / r) * (1 + r)            # start-of-year flow
    fv_cur = cur_val * (1 + r) ** n
    return round(fv_cur + fv_c, 2)

def nps_future_value(cur_val, m_contrib, r_annual, months_left):
    if months_left <= 0:
        return cur_val
    r_m = r_annual / 12
    fv_c   = m_contrib * (((1 + r_m) ** months_left - 1) / r_m) * (1 + r_m)
    fv_cur = cur_val * (1 + r_m) ** months_left
    return round(fv_cur + fv_c, 2)

def calculate_sip_future_value(monthly_sip, annual_rate, years):
        """Calculates the future value of a Systematic Investment Plan (SIP)."""
        if years <= 0:
            return 0.0
        monthly_rate = annual_rate / 12
        months = int(years * 12)
        if monthly_rate == 0:
            return monthly_sip * months
        return monthly_sip * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)

def calculate_required_sip(target_value, annual_rate, years):
        """Calculates the monthly SIP required to reach a target future value."""
        if years <= 0 or target_value <= 0:
            return 0.0   
        monthly_rate = annual_rate / 12
        months = int(years * 12)
        if monthly_rate == 0:
            return target_value / months
        return (target_value * monthly_rate) / (((1 + monthly_rate) ** months - 1))

def lumpsum_required(corpus_needed: float, r_annual: float, years: int) -> float:
    """Present value needed today to reach corpus_needed in `years` years at rate r_annual."""
    if years <= 0:
        return corpus_needed
    return corpus_needed / ((1 + r_annual) ** years)

def future_value_lumpsum(principal: float, r_annual: float, years: float, compounding_frequency: int = 1) -> float:
    """Future value of a lumpsum with compounding."""
    if years <= 0 or principal <= 0:
        return principal
    n = max(1, compounding_frequency)
    rate_per = r_annual / n
    total_n = n * years
    return principal * ((1 + rate_per) ** total_n)

def sip_required(corpus_needed: float, r_annual: float, n_months: int) -> float:
    """Monthly SIP needed to reach corpus_needed with monthly compounding at r_annual."""
    if n_months <= 0:
        return float('inf')
    if r_annual < 0:
        # Fallback: linear divide when negative rate passed accidentally.
        return corpus_needed / n_months
    r = r_annual / 12.0
    if r == 0:
        return corpus_needed / n_months
    denom = (((1 + r) ** n_months - 1) / r) * (1 + r)
    if denom == 0:
        return float('inf')
    return round(corpus_needed / denom)

def reduce_from_schedule(schedule: Dict[int, float], year: int, amount: float) -> float:
    """Reduce up to `amount` from schedule[year]; returns actually reduced."""
    if amount <= 0:
        return 0.0
    avail = schedule.get(year, 0.0)
    used = min(avail, amount)
    if used > 0:
        new_val = avail - used
        if new_val <= 1e-9:
            schedule.pop(year, None)
        else:
            schedule[year] = new_val
    return used 

def add_to_schedule(schedule: Dict[int, float], year: int, amount: float) -> None:
    if amount <= 0:
        return
    schedule[year] = schedule.get(year, 0.0) + amount

def fv_sip(P: float, r_annual: float, n_months: int) -> float:
    """Future value at month-end contributions P over n_months."""
    if n_months <= 0 or P <= 0:
        return 0.0
    r = r_annual / 12.0
    if r == 0:
        return P * n_months
    return P * (((1 + r) ** n_months - 1) / r) * (1 + r)

def apply_lumpsum_to_goal(goal_gap: float, liquid_pool: float, start_year: int, end_year: int, 
    funded_from: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Try to close remaining gap with lumpsum today. If insufficient, use all liquid to reduce gap.
    Records principal used and its FV contribution.
    """
    if goal_gap <= 0 or liquid_pool <= 1e-9:
        return goal_gap, liquid_pool

    years = max(0, end_year - start_year)
    if years > 3:
        r_annual=0.12
    else: 
        r_annual=0.09 
    # PV needed today to exactly close the goal_gap
    pv_needed = lumpsum_required(goal_gap, r_annual, years)

    if pv_needed <= liquid_pool:
        # Fully close
        fv_contrib = future_value_lumpsum(pv_needed, r_annual, years)
        funded_from.append({
            "type": "lumpsum_from_liquid",
            "principal_used_today": pv_needed,
            "from_year": start_year,
            "to_year": end_year,
            "years": years,
            "rate": f'{round(r_annual*100)}'+'%',
            "fv_contribution": fv_contrib
        }) 
        liquid_pool -= pv_needed
        goal_gap -= fv_contrib
        return round(goal_gap), round(liquid_pool)
    else: 
        # Use everything; reduce the gap by its FV 
        principal_used = liquid_pool
        fv_contrib = future_value_lumpsum(principal_used, r_annual, years)
        funded_from.append({
            "type": "lumpsum_from_liquid_partial",
            "principal_used_today": principal_used,
            "from_year": start_year,
            "to_year": end_year,
            "years": years,
            "rate": f'{round(r_annual*100)}'+'%',
            "fv_contribution": fv_contrib
        })
        liquid_pool = 0.0
        goal_gap -= fv_contrib 
        return round(goal_gap), round(liquid_pool) 

def apply_freed_sip_to_goal(
    goal_gap: float,
    freed_sip: Dict[int, float],
    #r_annual: float,
    start_year: int,
    end_year: int,
    funded_from: List[Dict[str, Any]]
) -> Tuple[float, Dict[int, float]]:
    """
    Use freed SIPs that start before end_year to reduce goal_gap.
    Each freed monthly amount starting at Y contributes until end_year.
    We may use part/all of a freed monthly. We then move what we used to free at end_year.
    """
    if goal_gap <= 0:
        return round(goal_gap), freed_sip
    
    years_sorted = sorted([y for y in freed_sip.keys() if y < end_year])
    # Work on a copy; we'll mutate safely and only return final dict.
    sched = dict(freed_sip)

    for y in years_sorted:
        if goal_gap <= 0:
            break 
        months = max(0, (end_year - y) * 12)
        if max(0, (end_year - y))>3:
            r_annual=0.12
        else :
            r_annual=0.09
        if months == 0:
            continue

        monthly_available = sched.get(y, 0.0)
        if monthly_available <= 1e-9:
            continue

        # Monthly SIP needed if we only started at year y for the remaining gap:
        monthly_needed = sip_required(goal_gap, r_annual, months)

        if monthly_available >= monthly_needed:
            # Use only the part needed
            used = monthly_needed
            # Reduce at y; add to end_year
            reduce_from_schedule(sched, y, used)
            add_to_schedule(sched, end_year, used)

            # Record and close the gap
            fv_contrib = fv_sip(used, r_annual, months)
            funded_from.append({
                "type": "freed_sip",
                "monthly": used,
                "from_year": y,
                "to_year": end_year,
                "months": months,
                "rate": f'{round(r_annual*100)}'+'%',
                "fv_contribution": fv_contrib
            }) 
            goal_gap -= fv_contrib
            break  # fully funded

        else:
            # Use the entire freed monthly_available
            used = monthly_available
            reduce_from_schedule(sched, y, used)
            add_to_schedule(sched, end_year, used)

            fv_contrib = fv_sip(used, r_annual, months)
            funded_from.append({
                "type": "freed_sip",
                "monthly": used,
                "from_year": y,
                "to_year": end_year,
                "months": months,
                "rate": f'{round(r_annual*100)}'+'%',
                "fv_contribution": fv_contrib
            })
            goal_gap -= fv_contrib
            # continue; still gap left

    return round(goal_gap), sched

def apply_surplus_sip_to_goal(
    goal_gap: float,
    monthly_surplus: float,
    # r_annual: float,
    start_year: int,
    end_year: int,
    funded_from: List[Dict[str, Any]],
    freed_sip: Dict[int, float]
) -> Tuple[float, float, Dict[int, float]]:
    """
    Use monthly_surplus toward the goal until end_year. Whatever is used becomes freed again at end_year.
    """
    if goal_gap <= 0 or monthly_surplus <= 1e-9:
        return goal_gap, monthly_surplus, freed_sip

    months = max(0, (end_year - start_year) * 12)
    years=max(0, (end_year - start_year))
    if years>3:
        r_annual=0.12
    else: 
        r_annual=0.09
    if months == 0:
        return round(goal_gap), round(monthly_surplus), freed_sip

    monthly_needed = sip_required(goal_gap, r_annual, months)

    if monthly_surplus >= monthly_needed:
        used = monthly_needed
        fv_contrib = fv_sip(used, r_annual, months)
        funded_from.append({
            "type": "sip_from_surplus",
            "monthly": used,
            "from_year": start_year,
            "to_year": end_year,
            "months": months,
            "rate": f'{round(r_annual*100)}'+'%',
            "fv_contribution": fv_contrib
        })
        # Commit this monthly until end_year → becomes free then
        add_to_schedule(freed_sip, end_year, used)
        monthly_surplus -= used
        goal_gap -= fv_contrib
    else: 
        # Use all available surplus
        used = monthly_surplus
        fv_contrib = fv_sip(used, r_annual, months)
        funded_from.append({
            "type": "sip_from_partial_surplus",
            "monthly": used,
            "from_year": start_year,
            "to_year": end_year,
            "months": months,
            "rate": f'{round(r_annual*100)}'+'%',
            "fv_contribution": fv_contrib
        })
        add_to_schedule(freed_sip, end_year, used)
        monthly_surplus = 0.0
        goal_gap -= fv_contrib

    return round(goal_gap), round(monthly_surplus), freed_sip

def remaining_tenure(P, r, EMI):
    """
    Calculate remaining number of months for a loan
    P = outstanding principal
    r = monthly interest rate
    EMI = monthly payment
    """
    if EMI <= P * r:
        return float('inf')  # Loan never pays off with this EMI
    n = -math.log(1 - (P * r) / EMI) / math.log(1 + r)
    return n

def _add_months(start: date, months: int) -> date:
    """Add a positive number of months to a date (month-end alignment not required)."""
    y, m = start.year, start.month
    m_total = m + months
    y += (m_total - 1) // 12
    m = (m_total - 1) % 12 + 1
    # keep the same day; if day overflow matters for you, clamp to month-end
    return date(y, m, min(start.day, 28))  # safe clamp to 28

def max_extra_payment(P, r, EMI):
    """
    Calculate the maximum extra payment (x) such that loan tenure does not become less than 1 month
    
    Parameters:
    P = outstanding principal
    r = monthly interest rate
    EMI = current monthly payment
    
    Returns:
    Maximum extra payment amount
    """
    min_tenure = 5  # minimum tenure in months
    
    # Derived from: n_new = -log(1 - (P*r)/(EMI+x)) / log(1+r)
    # Setting n_new = 1 and solving for x:
    denominator = 1 - (1 + r)**(-min_tenure)
    max_emi = (P * r) / denominator
    max_extra = max_emi - EMI
    
    if max_extra < 0:
        return 0  # No extra payment possible
    
    return max_extra

def _freed_by_year(close_dt: date, monthly_freed: float) -> dict[int, float]:
    """Record freed monthly amount in the year when the loan closes."""
    return {close_dt.year: float(monthly_freed)}

def total_interest(P, EMI, n):
    """Calculate total interest paid over loan tenure"""
    return (EMI * n) - P

def _safe(n):
    return None if (n is None or not isfinite(n)) else int(n)

def fv_monthly(contribution_monthly: float, annual_rate: float, months: int) -> float:
        if months <= 0:
            return 0.0
        monthly_i = annual_rate / 12.0
        if isclose(monthly_i, 0.0):
            return contribution_monthly * months
        # FV of ordinary annuity (payments at end of period)
        return contribution_monthly * ((1 + monthly_i)**months - 1) / monthly_i

def months_to_close(principal: float, annual_rate: float, payment: float) -> int | None:
    """Return number of months to close an amortizing loan with fixed payment.
    If payment <= interest-only payment, returns None."""
    if principal <= 0:
        return 0
    r_month = annual_rate / 12.0
    if payment <= principal * r_month:
        return None
    # n = -log(1 - r_month*principal/payment) / log(1 + r_month)
    # rearranged safe formula:
    try:
        n = - (log(1 - r_month * principal / payment) / log(1 + r_month))
    except ValueError:
        return None
    if not isfinite(n):
        return None
    return ceil(n)

def close_date_from_months(start_date: date, months: int) -> str:
    y = start_date.year
    m = start_date.month + months
    y += (m - 1) // 12
    m = ((m - 1) % 12) + 1
    
    # Handle day overflow safely
    # Find the last valid day in the target month
    from calendar import monthrange
    last_day = monthrange(y, m)[1]
    d = min(start_date.day, last_day)
    
    return date(y, m, d).isoformat()

def present_loans_no_allocation(loans: list, today: date, monthly_surplus: float = 0.0):
    per_loan = []
    freed_timeline = {}
    today=datetime.today()
    for ln in loans:
        principal = float(ln.get('outstanding_balance', 0))
        rate = float(ln.get('interest_rate', 0))
        emi = float(ln.get('emi_amount', 0))
        loan_type = ln.get('type', 'Unknown')
        
        baseline_months = months_to_close(principal, rate, emi)
        baseline_close_date = None
        freed_by_year = {}

        if baseline_months is not None:
            baseline_close_date = close_date_from_months(today, baseline_months)
            
            # Calculate the year when this loan will be freed
            close_date = date.fromisoformat(baseline_close_date)
            close_year = close_date.year
            
            # Add the EMI amount to freed_by_year for this loan
            freed_by_year[close_year] = emi
            
            # Add to overall freed_timeline
            if close_year in freed_timeline:
                freed_timeline[close_year] += emi
            else:
                freed_timeline[close_year] = emi
        
        # Build loan dict with allocation fields zero/null per user's request
        loan_entry = {
            'type': loan_type,
            'baseline_months': baseline_months,
            'baseline_close_date': baseline_close_date,
            'accelerated_months': 0,
            'accelerated_close_date': None,
            'interest_saved': 0.0,
            'monthly_extra_assigned': 0.0,
            'monthly_extra_applied': 0.0,
            'lump_sum_assigned': 0.0,
            'lump_sum_applied': 0.0,
            'freed_by_year': freed_by_year  # Now contains the EMI amount freed when loan closes
        }
        per_loan.append(loan_entry)
    
    result = {
        'per_loan': per_loan,
        'freed_timeline': freed_timeline,  # Overall timeline of all freed amounts by year
        'allocated_monthly_surplus': 0.0,
        'allocated_lump_sum': 0.0,
        'assumptions': {
            'today': today.isoformat(),
            'sorted_by': 'interest_rate desc',
            'monthly_surplus': monthly_surplus,
            'considered_only_not_under_penalty_for_prepayment': True,
            'monthly_extra_split_among_eligible': 0.0,
            'liquid_pool_total': None,
            'use_liquid_pool': False,
            'liquid_pool_percent_used': 0.0,
            'per_loan_lump_sum_if_used': 0.0,
            'no_snowball_reallocation': True
        },
        'unused_monthly_surplus': monthly_surplus
    }
    return result

# def convert_currency(value):
#     # return '{:,}'.format(value)
#     # return '₹{:,}'.format(value)
#     # return '₹ {:,}'.format(value)
#     value=round(value)
#     if value>10000:
#         value=round(value, -3)
#     else: 
#         value=round(value, -1)
#     return '{:,}'.format(value)

def convert_currency(value):
    value = round(value)
    if value > 1000000:
        value = round(value, -3)
    elif value > 100000:
        value = round(value, -2)
    else:
        value = round(value, -1)
    
    # Format number with Indian comma placement (no currency symbol)
    return format_decimal(value, locale='en_IN')

# con_val=convert_currency(15657876543)

def analyze_asset_portfolio(retirement_assets, liquid_assets, fixed_assets):
    """
    Analyzes asset portfolio and calculates total value and percentage distribution.
    
    Args:
        retirement_assets: List of retirement asset dictionaries
        liquid_assets: List of liquid asset dictionaries
        fixed_assets: List of fixed asset dictionaries
    
    Returns:
        JSON string containing asset breakdown, percentages, and total value
    """
    
    asset_details = []
    total_value = 0
    
    # Process retirement assets
    for asset in retirement_assets:
        for asset_type, details in asset.items():
            if asset_type == 'epf':
                current_value = details['current_value']
                asset_name = 'EPF'
            elif asset_type == 'ppf':
                current_value = details['current_value']
                asset_name = 'PPF'
            elif asset_type == 'nps':
                current_value = details['current_value']
                asset_name = 'NPS'
            else:
                continue
            
            asset_details.append({
                'asset_category': 'Retirement Assets',
                'asset_name': asset_name,
                'current_value': current_value,
                'asset_id': details['asset_id']
            })
            total_value += current_value
    
    # Process liquid assets
    for asset in liquid_assets:
        for asset_type, details in asset.items():
            if asset_type == 'mutual_funds':
                current_value = details['current_value']
                asset_name = f"Mutual Funds (ID: {details['asset_id']})"
            elif asset_type == 'direct_equity':
                current_value = details['portfolio_value']
                asset_name = 'Direct Equity'
            elif asset_type == 'reits':
                current_value = details['current_value']
                asset_name = 'REITs'
            elif asset_type == 'fixed_deposits':
                current_value = details['principal_amount']
                asset_name = f"Fixed Deposit - {details['name_of_bank'].replace('_', ' ').title()}"
            
            asset_details.append({
                'asset_category': 'Liquid Assets',
                'asset_name': asset_name,
                'current_value': current_value,
                'asset_id': details['asset_id']
            })
            total_value += current_value
    
    # Process fixed assets
    for asset in fixed_assets:
        for asset_type, details in asset.items():
            if asset_type == 'real_estate_investment':
                current_value = details['current_market_value']
                asset_name = 'Real Estate Investment'
            elif asset_type == 'bonds':
                current_value = details['investment_amount']
                asset_name = f"Bonds - {details['name_of_bond'].replace('_', ' ').title()}"
            elif asset_type == 'pms_aif':
                current_value = details['current_value']
                asset_name = 'PMS/AIF'
            elif asset_type == 'esops':
                current_value = details['vested_esops_value']
                asset_name = 'ESOPs (Vested)'
            
            asset_details.append({
                'asset_category': 'Fixed Assets',
                'asset_name': asset_name,
                'current_value': current_value,
                'asset_id': details['asset_id']
            })
            total_value += current_value
    
    # Calculate percentages
    for asset in asset_details:
        asset['percentage_of_total'] = round((asset['current_value'] / total_value * 100), 2)
    
    # Prepare final output
    result = {
        'portfolio_summary': {
            'total_asset_value': total_value,
            'number_of_assets': len(asset_details)
        },
        'assets_breakdown': asset_details,
        'percentage_distribution': [
            {
                'asset_name': asset['asset_name'],
                'percentage': asset['percentage_of_total']
            }
            for asset in asset_details
        ]
    }
    
    return result

def calculate_investment_details(scheme):
    """
    Calculates the total invested amount and future value for an investment scheme.
    
    Args:
        scheme (dict): Dictionary with keys -
                       'start_date', 'end_date', 'monthly_investment', 'interest_rate'
    
    Returns:
        dict: {
            'scheme_name': str,
            'linked_to': str,
            'total_invested': float,
            'future_value': float,
            'duration_months': int
        }
    """
    # Parse dates
    start_date = datetime.strptime(scheme['start_date'], "%Y-%m-%d")
    end_date = datetime.strptime(scheme['end_date'], "%Y-%m-%d")
    
    # Calculate total months of investment
    duration_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    # Extract values
    P = scheme['monthly_investment']
    annual_rate = scheme['interest_rate']
    r = annual_rate / 12  # monthly rate
    
    # Total invested amount
    total_invested = P * duration_months
    
    # Future Value of SIP formula
    future_value = P * (((1 + r) ** duration_months - 1) / r) * (1 + r)
    
    # return {
    #     'scheme_name': scheme['scheme_name'],
    #     'linked_to': scheme['linked_to'],
    #     'duration_months': duration_months,
    #     'total_invested': round(total_invested, 2),
    #     'future_value': round(future_value, 2)
    # }

    return round(total_invested, 2), round(future_value, 2)

def calculate_current_value(scheme):
    """
    Calculates the current value of an ongoing investment scheme as of today's date.
    
    Args:
        scheme (dict): Investment details containing start_date, end_date, monthly_investment, and interest_rate.
    
    Returns:
        dict: {
            'scheme_name': str,
            'linked_to': str,
            'duration_months_total': int,
            'months_invested_so_far': int,
            'total_invested_so_far': float,
            'current_value': float
        }
    """

    if scheme=={}:
        return 0
    # Parse input dates
    start_date = datetime.strptime(scheme['start_date'], "%Y-%m-%d")
    end_date = datetime.strptime(scheme['end_date'], "%Y-%m-%d")
    today = datetime.today()
    
    # Calculate total and current months
    total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if today < start_date:
        invested_months = 0
    elif today > end_date:
        invested_months = total_months
    else:
        invested_months = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    
    # Extract data
    P = scheme['monthly_investment']
    annual_rate = scheme['interest_rate']
    r = annual_rate / 12  # monthly rate
    
    # Total invested so far
    total_invested = P * invested_months
    
    # SIP value formula
    if invested_months > 0:
        current_value = P * (((1 + r) ** invested_months - 1) / r) * (1 + r)
    else:
        current_value = 0
    
    # return {
    #     'scheme_name': scheme['scheme_name'],
    #     'linked_to': scheme['linked_to'],
    #     'duration_months_total': total_months,
    #     'months_invested_so_far': invested_months,
    #     'total_invested_so_far': round(total_invested, 2),
    #     'current_value': round(current_value, 2)
    # }

    return round(current_value, 2)


def stepup_sip_required(corpus_needed: float, r_annual: float, n_months: int, 
                        stepup_rate: float, stepup_frequency: int = 12) -> float:
    """
    Monthly Step-up SIP needed to reach corpus_needed with periodic increases.
    
    Args:
        corpus_needed: Target corpus amount
        r_annual: Annual rate of return (as decimal, e.g., 0.12 for 12%)
        n_months: Total investment period in months
        stepup_rate: Rate of increase in SIP (as decimal, e.g., 0.10 for 10%)
        stepup_frequency: Months between step-ups (default 12 for annual)
    
    Returns:
        Initial monthly SIP amount needed
    """
    if n_months <= 0:
        return 0  # Changed from float('inf') to 0 for better handling
    if corpus_needed <= 0:
        return 0  # No SIP needed if corpus is already met
    if r_annual < 0:
        # Fallback: linear divide when negative rate passed accidentally
        return corpus_needed / n_months
    
    r = r_annual / 12.0  # Monthly return rate
    
    # Handle edge cases
    if stepup_frequency <= 0:
        stepup_frequency = n_months + 1  # No step-up
    if stepup_rate < 0:
        stepup_rate = 0  # No step-up for negative rates
    
    # Special case: no return
    if r == 0:
        # Calculate sum of stepped-up payments
        total_payments = 0
        current_sip = 1  # Unit SIP
        for month in range(n_months):
            if month > 0 and month % stepup_frequency == 0:
                current_sip *= (1 + stepup_rate)
            total_payments += current_sip
        if total_payments == 0:
            return float('inf')
        return round(corpus_needed / total_payments)
    
    # Calculate future value of stepped-up SIPs
    fv_total = 0
    current_sip = 1  # Start with unit SIP
    
    for month in range(n_months):
        # Apply step-up at appropriate intervals
        if month > 0 and month % stepup_frequency == 0:
            current_sip *= (1 + stepup_rate)
        
        # Calculate future value of this month's SIP
        months_remaining = n_months - month
        fv_total += current_sip * ((1 + r) ** months_remaining)
    
    if fv_total == 0:
        return float('inf')
    
    # Calculate initial SIP needed
    initial_sip = corpus_needed / fv_total
    return round(initial_sip)


def calculate_ssy_future_value(
    current_value: float,
    annual_contribution: float,
    account_opening_date: date,
    girl_child_dob: date,
    goal_target_year: int,
    goal_type: str,  # 'UG', 'PG', 'marriage', 'other'
    ssy_interest_rate: float = 0.082  # Current SSY rate ~8.2%
) -> dict:
    """
    Calculate SSY future value with withdrawal constraints.
    
    SSY Rules:
    - Partial withdrawal (up to 50%): Girl must be 18+ OR passed 10th grade
    - Full maturity: 21 years from account opening
    - Premature closure: For marriage (after 18) or compassionate grounds
    
    Returns:
        dict with:
        - available_amount: Amount available for the goal
        - withdrawal_type: 'partial', 'full', 'not_eligible'
        - maturity_date: When SSY matures
        - remaining_balance: Balance left in SSY after withdrawal
    """
    from datetime import datetime
    
    current_date = datetime.today().date()
    current_year = current_date.year
    
    # Calculate key dates
    maturity_date = date(
        account_opening_date.year + 21,
        account_opening_date.month,
        account_opening_date.day
    )
    girl_turns_18 = date(
        girl_child_dob.year + 18,
        girl_child_dob.month,
        girl_child_dob.day
    )
    
    # Calculate years until goal and years of contribution remaining
    # SSY allows contributions for 15 years only
    contribution_end_date = date(
        account_opening_date.year + 15,
        account_opening_date.month,
        account_opening_date.day
    )
    
    # Calculate FV at goal target year
    years_to_goal = goal_target_year - current_year
    years_from_opening_to_goal = goal_target_year - account_opening_date.year
    
    # Calculate contributions remaining
    if current_date < contribution_end_date:
        years_of_contributions_left = min(
            (contribution_end_date.year - current_year),
            years_to_goal
        )
    else:
        years_of_contributions_left = 0
    
    # Calculate FV of current value
    fv_current = current_value * ((1 + ssy_interest_rate) ** years_to_goal)
    
    # Calculate FV of future contributions (ordinary annuity)
    if years_of_contributions_left > 0:
        fv_contributions = annual_contribution * (
            ((1 + ssy_interest_rate) ** years_of_contributions_left - 1) / ssy_interest_rate
        ) * (1 + ssy_interest_rate)  # FV at end of contribution period
        
        # Grow this to goal year if contributions end before goal
        remaining_growth_years = years_to_goal - years_of_contributions_left
        if remaining_growth_years > 0:
            fv_contributions *= ((1 + ssy_interest_rate) ** remaining_growth_years)
    else:
        fv_contributions = 0
    
    total_fv_at_goal = fv_current + fv_contributions
    
    # Determine withdrawal eligibility
    goal_date = date(goal_target_year, 6, 1)  # Assume mid-year for goal
    
    # Check if girl will be 18+ at goal date
    is_18_plus_at_goal = goal_date >= girl_turns_18
    
    # Check if SSY has matured at goal date
    is_matured = goal_date >= maturity_date
    
    # Determine available amount based on rules
    if is_matured:
        # Full maturity - 100% available
        available_amount = total_fv_at_goal
        withdrawal_type = 'full_maturity'
        remaining_balance = 0
    elif is_18_plus_at_goal and goal_type in ['UG','PG']:
        # Partial withdrawal eligible (50% for higher education)
        available_amount = total_fv_at_goal * 0.50
        withdrawal_type = 'partial_50'
        remaining_balance = total_fv_at_goal * 0.50
    elif is_18_plus_at_goal and goal_type in ['Marriage']:
        available_amount = total_fv_at_goal
        withdrawal_type = 'premature_closure_marriage'   
        remaining_balance = 0
    else:
        # Not eligible for withdrawal
        available_amount = 0
        withdrawal_type = 'not_eligible'
        remaining_balance = total_fv_at_goal
    
    return {
        'available_amount': round(available_amount),
        'total_fv_at_goal': round(total_fv_at_goal),
        'withdrawal_type': withdrawal_type,
        'maturity_date': maturity_date.isoformat(),
        'remaining_balance': round(remaining_balance),
        'is_girl_18_plus': is_18_plus_at_goal,
        'goal_target_year': goal_target_year,
        'girl_child_name': None,  # To be filled by caller
        'ssy_interest_rate': ssy_interest_rate
    }
