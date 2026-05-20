"""
Retirement Planning Nodes - Corpus & Goal Analysis

What this file does:
This script handles all retirement-related calculations including corpus requirements,
investment projections, and goal gap analysis for retirement planning.

What this file contains and processes:
- calculate_retirement_corpus: Calculates required retirement corpus using both standard (flat expenses) and segmented (phased lifestyle) methods
- calculate_all_retirement_investments: Computes future values of EPF, PPF, NPS, ULIP schemes with category totals and grand total
- retirement_goal: Evaluates retirement corpus gap by comparing required vs estimated corpus and creates standardized retirement goal
"""

# retirement nodes:  calculate_retirement_corpus, calculate_all_retirement_investments, retirement_goal
from Financial_Planning.Models.client_data_state import ClientState
from datetime import datetime, date
from collections import defaultdict
from Financial_Planning.Utilities.utility_functions import (calculate_future_value, calculate_present_value_annuity, epf_future_value, 
                                                            ppf_future_value, nps_future_value, calculate_investment_details)

def calculate_retirement_corpus(state: ClientState):
    """
    Calculates the required retirement corpus using two methods:
    1. Standard Method: Flat expenses throughout retirement
    2. Segmented Cash Flow Method: Lifestyle-based phases with varying expenses
    
    Args:
        client_data (dict): Client's financial and personal data
        retirement_age (int): Age at which client plans to retire (default: 60)
        life_expectancy (int): Expected life expectancy (default: 85)
        inflation_rate (float): Annual inflation rate (default: 6%)
    
    Returns:
        dict: Detailed retirement corpus calculation with both methods
    """
    print("--------------------------"*6)
    print("\n")
    print("Node: calculate_retirement_corpus \n")
    print("Calculating retirement corpus... \n")
    client_data=state['client_data']
    life_expectancy=85                    # pre-defined
    inflation_rate=0.06                   # pre-defined 
    real_return_rate = 0.04                # pre-defined

    # Extract client information
    client_dob = datetime.strptime(client_data['client_data']['date_of_birth'], '%Y-%m-%d').date() 
    current_age = date.today().year - client_dob.year
    monthly_expenses = client_data['investment_details']['financial_summary'][0]['monthly_expenses_excl_emis']
    annual_expenses = monthly_expenses*12 #+ (client_data['investment_details']['financial_summary'][0]["miscellaneous_kids_education_expenses_monthly"])*12 + client_data['investment_details']['financial_summary'][0]["annual_vacation_expenses"]
    retirement_age=client_data['client_data']['retirement_age']
    # Calculate years to retirement and retirement duration
    years_to_retirement = retirement_age - current_age
    retirement_duration = life_expectancy - retirement_age
    
    # Future annual expenses at retirement (adjusted for inflation)
    future_annual_expenses = calculate_future_value(annual_expenses, inflation_rate, years_to_retirement)
    
    retirement_plan = {
        "client_info": {
            "current_age": current_age,
            "retirement_age": retirement_age,
            "life_expectancy": life_expectancy,
            "years_to_retirement": years_to_retirement,
            "retirement_duration": retirement_duration,
            "current_monthly_expenses": monthly_expenses,
            "current_annual_expenses": annual_expenses,
            "future_annual_expenses_at_retirement": round(future_annual_expenses, 2)
        }
    }
    
    standard_corpus = calculate_present_value_annuity(
        future_annual_expenses, 
        real_return_rate, 
        retirement_duration
    )
    
    retirement_plan["standard_method"] = {
        "annual_expenses_throughout_retirement": round(future_annual_expenses, 2),
        "real_return_rate_assumed": real_return_rate,
        "required_corpus": round(standard_corpus, 2)
    }
    
    phases = [
        {
            "name": "Early Retirement",
            "age_range": "55-65",
            "start_age": retirement_age,
            "end_age": 65,
            "expense_multiplier": 1.1,  # 10% higher
            "description": "Active lifestyle, travel"
        },
        {
            "name": "Middle Retirement", 
            "age_range": "65-75",
            "start_age": 65,
            "end_age": 75,
            "expense_multiplier": 1.0,  # Normal expenses
            "description": "Baseline expenses"
        },
        {
            "name": "Late Retirement",
            "age_range": "75-85", 
            "start_age": 75,
            "end_age": life_expectancy,
            "expense_multiplier": 1.2,  # 20% higher
            "description": "Healthcare, support needs"
        }
    ]
    
    segmented_phases = [] 
    total_segmented_corpus = 0 
    
    for phase in phases:

        phase_start = max(phase['start_age'], retirement_age)
        phase_end = phase["end_age"]
        phase_duration = phase_end - phase_start
        
        if phase_duration <= 0:
            continue
            
        # Calculate expenses for this phase
        phase_annual_expenses = future_annual_expenses * phase["expense_multiplier"]
        
        # Calculate years from retirement to start of this phase
        years_to_phase_start = phase_start - retirement_age
        
        # Discount the required corpus back to retirement age
        if years_to_phase_start > 0:
            # Phase starts later, so discount the annuity back
            phase_corpus_at_phase_start = calculate_present_value_annuity(
                phase_annual_expenses, real_return_rate, phase_duration
            )
            phase_corpus_at_retirement = phase_corpus_at_phase_start / ((1 + real_return_rate) ** years_to_phase_start)
        else:
            # Phase starts immediately at retirement
            phase_corpus_at_retirement = calculate_present_value_annuity(
                phase_annual_expenses, real_return_rate, phase_duration
            )
        
        phase_info = {
            "phase_name": phase["name"],
            "age_range": f"{phase_start}-{phase_end}",
            "duration_years": phase_duration,
            "expense_multiplier": phase["expense_multiplier"],
            "annual_expenses": round(phase_annual_expenses, 2),
            "corpus_required": round(phase_corpus_at_retirement, 2),
            "description": phase["description"]
        }
        
        segmented_phases.append(phase_info)
        total_segmented_corpus += phase_corpus_at_retirement
    
    retirement_plan["segmented_method"] = {
        "phases": segmented_phases,
        "total_required_corpus": round(total_segmented_corpus, 2)
    }
    
    difference = total_segmented_corpus - standard_corpus
    percentage_diff = (difference / standard_corpus) * 100
    
    retirement_plan["comparison"] = {
        "standard_corpus": round(standard_corpus, 2),
        "segmented_corpus": round(total_segmented_corpus, 2),
        "difference": round(difference, 2),
        "percentage_difference": round(percentage_diff, 1)
    }
    
    # Recommended corpus (higher of the two)
    recommended_corpus = max(standard_corpus, total_segmented_corpus)
    retirement_plan["recommendation"] = {
        "recommended_corpus": round(recommended_corpus, 2),
        "method_used": "Segmented Method" if total_segmented_corpus > standard_corpus else "Standard Method",
        "rationale": "Taking the higher estimate to ensure adequate retirement funding"
    }
    
    print(f"retirement plan: {retirement_plan}\n")
    print("--------------------------"*6)
    return {'required_retirement_corpus': retirement_plan}


def calculate_all_retirement_investments(state: ClientState):
    """
    Computes future values of all retirement investment schemes, returning 
    per-scheme details, per-category totals, and an overall grand total.

    Args:
        state (ClientState): Contains client data with:
            - client_data.client_age (int)
            - investment_details.retirement_investments (dict) where keys are 
              categories ("ulip", "epf", "ppf", "nps") and values are lists of schemes.
              Each scheme includes fields like start date, contribution amounts, 
              rates, term/maturity, etc. (varies by category).

    Returns:
        dict: {
            "retirement_schemes_fv": {
                "schemes": {category: [ {scheme_no, future_value, total_invested}, ... ]},
                "category_totals": {category: float},
                "grand_total": float
            }
        }

    Purpose:
        Projects the corpus for each scheme until maturity/retirement, aggregates 
        by category, and produces a consolidated total.
    """
    print("--------------------------"*6)
    print("\n")
    print("Node: calculate_all_retirement_investments")
    print("Calculating future value of retirement funds... \n")
    retirement_investments=state['client_data']['investment_details']['retirement_investments']
    current_age = state['client_data']['client_data']['client_age'] 
    retirement_age=state['client_data']['client_data']['retirement_age']
    today=datetime.today() 
    
    results          = defaultdict(list)   # per-scheme data
    category_totals  = {}                  # per-category sum
    grand_total      = 0.0
    
    for category, scheme_list in retirement_investments.items():
        cat_total = 0.0 

        for i, sc in enumerate(scheme_list, start=1):
            # ---------- ULIP (UPDATED field names) ----------
            if category.lower() == "ulip":
                pass
            #    # Create end date from final year of premium + term
            #    start_date = sc["commencement_date_of_ulip_policy_1"]
            #    ppt = sc['ppt']
            #    term = sc["term"]
            #    maturity_amount = sc["maturity_value"]
                
                

            # ---------- EPF (field names remain same) ----------
            elif category.lower() == "epf" and sc["current_value"]!=0 and sc["employee_employer_contribution_monthly"]!=0:
                # EPF doesn't have maturity_year in new structure, use retirement age
                years_left = retirement_age - current_age 
                fv = epf_future_value(
                        sc["current_value"],
                        sc["employee_employer_contribution_monthly"],
                        sc["interest_rate"],
                        years_left)   
                invested = sc["current_value"] + \
                           sc["employee_employer_contribution_monthly"] * 12 * max(years_left, 0)

            # ---------- PPF (field names remain same) ----------
            elif category.lower() == "ppf" and sc["current_value"]!=0 and sc["annual_contribution"]!=0:
                # PPF doesn't have lock_in_end_year, assume 15-year lock-in from current year 
                years_left = retirement_age - current_age  # Standard PPF lock-in period is 15 years but here we consider the left years are upto the retirement age.
                fv = ppf_future_value(
                        sc["current_value"],
                        sc["annual_contribution"],
                        sc["interest_rate"],
                        years_left) 
                invested = sc["current_value"]+sc["annual_contribution"]*years_left

            # ---------- NPS (UPDATED field names) ----------
            elif category.lower() == "nps" and sc["current_value"]!=0 and sc["monthly_contribution"]!=0: 
                # Calculate months left until maturity year 
                months_left = max((sc["maturity_year"] - today.year) * 12, 0)
                fv = nps_future_value( 
                        sc["current_value"],
                        sc["monthly_contribution"],
                        sc["expected_corpus_growth_rate"],
                        months_left) 
                invested = sc["current_value"] + sc["monthly_contribution"] * months_left

            elif category.lower()=='other' and sc['monthly_investment']>0:
                category=sc['scheme_name'] 
                invested, fv=calculate_investment_details(sc)

            else: 
                # Skip unknown categories gracefully
                continue

            results[category].append({
                "scheme_no"     : i,
                "future_value"  : fv,
                "total_invested": round(invested, 2)
            })
            cat_total += fv 

        if cat_total:
            category_totals[category] = round(cat_total, 2)
            grand_total += cat_total

    retirement_schemes_fv={
        "schemes"         : dict(results),
        "category_totals" : category_totals,
        "grand_total"     : round(grand_total, 2)
    }
    
    print(f"retirement schemes: {retirement_schemes_fv}\n")
    print("--------------------------"*6)
    return {"retirement_schemes_fv": retirement_schemes_fv}

def retirement_goal(state: ClientState):
    """
    Evaluates the retirement goal against the estimated corpus and consolidates it 
    with other education and financial goals.

    Args:
        state (ClientState): Contains client data and prior calculations with:
            - client_data.client_data.client_age (int)
            - client_data.client_data.retirement_age (int)
            - required_retirement_corpus.recommendation.recommended_corpus (float)
            - retirement_schemes_fv.grand_total (float)
            - education_planning_summary (list[dict]): Goals with name, type, target_year, final_gap
            - financial_goals (list[dict]): Goals with goal_name, target_year, goal_gap

    Returns:
        dict: {
            "goals": [
                {
                    "goal_name": str,
                    "corpus_needed": float,
                    "corpus_gap": float,
                    "target_year": int,
                    "funded_from": list,
                    "surplus": float (only for retirement goal)
                },
                ...
            ]
        }

    Purpose:
        - Compares required vs. estimated retirement corpus to compute gaps or surplus.
        - Builds a unified list of all goals (retirement, education, financial).
        - Standardizes each goal with common fields for downstream planning.
    """
    print("--------------------------"*6)
    print("\n")
    print("Node: retirement_goal \n")
    print("Define a retirement goal...")
    client_data3=state['client_data']
    required_retirement_corpus= state['required_retirement_corpus']['recommendation']['recommended_corpus']
    estimated_retirement_corpus = state['retirement_schemes_fv']['grand_total']
    retirement_age = state['client_data']['client_data']['retirement_age']
    current_date=date.today()
    current_year=current_date.year

    if required_retirement_corpus>estimated_retirement_corpus:
        years_to_retire= retirement_age - client_data3['client_data']['client_age']
        result={} 
        result['goal_name']="retirement"
        result['target_corpus']=required_retirement_corpus 
        result['corpus_needed']=required_retirement_corpus-estimated_retirement_corpus
        result['corpus_gap']=required_retirement_corpus-estimated_retirement_corpus
        result['target_year']= current_year + years_to_retire
        if estimated_retirement_corpus>0:
            result['funded_from']=[{'future_values_retirement_investments':estimated_retirement_corpus}]
        else:      
            result['funded_from']=[]
        #result['sip_amount']=sip_amount
        #result['sip_years']=client_data['client_data']['retirement_age']-(current_date.year-int(client_data['client_data']['date_of_birth'].split('-')[0]))
        result['surplus']=0
    
    elif required_retirement_corpus==estimated_retirement_corpus:

        result={}
        result['goal_name']="retirement" 
        result['target_corpus']=required_retirement_corpus
        result['corpus_needed']=0 
        result['corpus_gap']=0 
        result['target_year']= current_year + years_to_retire
        if estimated_retirement_corpus>0:
            result['funded_from']=[{'future_values_retirement_investments':estimated_retirement_corpus}]
        else: 
            result['funded_from']=[]
        #result['sip_amount']=0
        #result['sip_years']=0
        result['surplus']=0
    
    elif required_retirement_corpus<estimated_retirement_corpus: 
#         print(f""" 
#              required retirement corpus: {required_retirement_corpus} \n estimated retirement corpus: {estimated_retirement_corpus} \n
#              retirement_gap = 0, \n surplus_corpus: {estimated_retirement_corpus-required_retirement_corpus}
# """)
        result={}
        result['goal_name']="retirement"
        result['target_corpus']=required_retirement_corpus
        result['corpus_needed']=0
        result['corpus_gap']=0
        result['target_year']= current_year + years_to_retire
        if estimated_retirement_corpus>0:
            result['funded_from']=[{'future_values_retirement_investments':estimated_retirement_corpus}]
        else: 
            result['funded_from']=[]
        #result['sip_amount']=0
        #result['sip_years']=0
        #result['surplus']=estimated_retirement_corpus-required_retirement_corpus
    
    retirement_goal=[result]

    print(f"retirement_goal: {retirement_goal}\n")
    print("--------------------------"*6)
    return {'retirement_goal': retirement_goal}
