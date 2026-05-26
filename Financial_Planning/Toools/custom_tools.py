"""
Custom LangChain Tools - Financial Calculations & Scoring

What this file does:
This script defines custom LangChain tools that agents can use for specialized calculations.
It provides goal prioritization, education cost analysis, and risk assessment functionality.

What this file contains:
- calculate_priority_score: Calculates goal priority score using weight (60%) and time urgency (40%) formula
- sort_goals_by_priority: Sorts goal list by descending priority_score
- clarify_with_user: Interactive tool for agent to ask user questions
- calculate_overall_fees: Multiplies annual fees by duration to get total program cost
- currency_conversion: Converts foreign currency to INR using conversion ratio
- avg_fees: Computes arithmetic mean of college fees list
- get_current_date: Returns today's date for age, retirement, and time-to-goal calculations
- risk_analysis: Analyzes risk appetite based on equity exposure and years to retirement (Low/Medium/Medium to High/Medium to Low)
"""

from langchain.tools import tool
from datetime import date, datetime
from typing import List, Dict
import json
import logging

log = logging.getLogger(__name__)

########################## current date ################################################

@tool
def get_current_date() -> str:
    """
    Returns today's calendar date for age, years-to-retirement, years-to-goal,
    and other date-based calculations. Call this instead of guessing the year.
    """
    today = date.today()
    payload = {
        "date": today.isoformat(),
        "year": today.year,
        "month": today.month,
        "day": today.day,
    }
    log.info("get_current_date tool called — returning %s", payload)
    print(f"[get_current_date] tool called - returning date: {today.isoformat()}")
    return json.dumps(payload)

########################## goal prioritization ################################################

@tool
def calculate_priority_score(weight: float, target_year: int) -> float:
    """Calculates the priority score for a financial goal."""
    time_left = target_year - date.today().year
    if time_left <= 0: time_left = 0.1
    return round((weight * 0.6) + ((1 / time_left) * 0.4),1)

@tool
def sort_goals_by_priority(goals: List[Dict]) -> List[Dict]:
    """Sorts a list of goals based on their 'priority_score'."""
    #goals=goals['goals']
    if not all("priority_score" in g for g in goals):
        raise ValueError("Each goal must include a 'priority_score' before sorting.")
    return sorted(goals, key=lambda x: x["priority_score"], reverse=True)

#################################### goal prioritization ######################################

#################### education web scrapper tool #######################################
@tool
def clarify_with_user(question: str)->str:
    "This function is used to interact with the user and ask any question "
    answer=input(question)
    return str(answer)

@tool
def calculate_overall_fees(annual_fees: float, duration: int) -> float:
    """
    Calculate total program fees as annual_fees * duration.
    Returns the total in the same currency as the annual_fees.
    """
    return round(float(annual_fees) * int(duration))

@tool
def currency_conversion(amount_to_convert: float, conversion_ratio: float) -> float:
    """
    Convert a given amount to INR using the provided conversion ratio.
    Example: if 1 USD = 83.25 INR, pass conversion_ratio=83.25.
    """
    return round(float(amount_to_convert) * float(conversion_ratio))

@tool
def avg_fees(colleges: List[float]) -> float:
    """
    Compute the arithmetic mean of overall fees for the given colleges.
    Expects all values in the SAME currency (e.g., INR).
    """
    # defensive numeric cast + basic validation
    vals = [float(x) for x in colleges]
    return round(sum(vals) / len(vals))
#################### education web scrapper tool #######################################

@tool
def risk_analysis(equity_exposure: bool, years_to_retire: int):
    """
    Analyze the risk appetite based on equity exposure and years left to retire.

    Args:
        equity_exposure (bool): Indicates whether the individual has exposure to equities (stocks).
        years_to_retire (int): Number of years remaining until retirement.

    Returns:
        str: A descriptive statement of the risk appetite category based on the inputs.
             - "Medium" if years to retire is less than 5 and there is equity exposure.
             - "Low" if years to retire is less than 5 and there is no equity exposure.
             - "Medium to High" if years to retire is 5 or more and there is equity exposure.
             - "Medium to Low" if years to retire is 5 or more and there is no equity exposure.
    """
    
    if years_to_retire < 5 and equity_exposure==True: 
        return "Risk Appetite is 'Medium' as years to retire is less than 5 and there is equity exposure is there."
    elif years_to_retire < 5 and equity_exposure==False: 
        return "Risk Appetite is 'Low' as years to retire is less than 5 and there is no equity exposure."
    elif years_to_retire >=5 and equity_exposure==True:   
        return "Risk Appetite is 'Medium to High' as years to retire is greater than or equal to 5 and there is equity exposure as well."
    else:
        return "Risk Appetite is 'Medium to Low' as years to retire is greater than or equal to 5 and there is no equity exposure."


