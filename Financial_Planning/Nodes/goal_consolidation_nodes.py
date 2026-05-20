"""
Goal Consolidation - Future Value & Merging

What this file does:
This script consolidates and enriches financial goals by calculating future values,
determining funding gaps, and merging goals from different sources into a unified list.

What this file contains and processes:
- goals_future_value: Calculates future value of savings and required capital for each financial goal, determines funding gap, and reallocates surplus from earlier goals to later ones
- add_goals: Consolidates all goals from financial_goals, education_goals, and retirement_goals into a single unified list
"""

# goal consolidation nodes: goals_future_value, add_goals
from Financial_Planning.Models.client_data_state import ClientState
from datetime import datetime, date
from Financial_Planning.Utilities.utility_functions import (calculate_future_value, remaining_tenure, _add_months)

def goals_future_value(state: ClientState):  # calculate the actual goal gap and allocating surplus for all the financial goals mentioned 
    """
    Calculates the future value of savings and required capital for each financial goal, 
    determines the funding gap, and reallocates any surplus from earlier goals 
    to later ones.

    Args:
        state (ClientState): A state object containing a "client_data" dictionary 
            with the following structure:
                - financial_goals (list[dict]): Each goal dictionary includes:
                    - target_year (int): Year when the goal must be achieved
                    - amount_saved_for_goal (float): Amount already saved toward the goal
                    - capital_required_today (float): Present-day value of capital needed 
                      to achieve the goal
                    - funded_from (list, optional): Records sources used to fund gaps 
                      (e.g., surplus from previous goals)

    Returns:
        dict: Updated "client_data" with enriched "financial_goals", where each goal includes:
                - future_value_of_saved_amount (float): Projected value of current savings 
                  at the target year (assumed 10% annual growth)
                - capital_required_at_target_year (float): Future value of required capital 
                  at the target year (assumed 6% annual inflation)
                - goal_gap (float): Remaining shortfall to fund the goal after considering 
                  savings and surplus reallocation
                - funded_from (list): Updated with surplus allocations from previous goals, 
                  if applicable

    Purpose:
        This function performs financial goal gap analysis by:
        1. Projecting savings and capital requirements into the future.
        2. Identifying shortfalls (goal gaps).
        3. Reallocating surplus from earlier goals to reduce gaps in later goals.
    """ 
    print("--------------------------"*6)
    print("\n")
    print("Node: goals_future_value \n")
    print("Other financial goals: calculating the future value of investmenst made for goals and defining goal based on the corpus gap... \n")
    client_data=state['client_data']
    goals=client_data.get('financial_goals', []) 
    surplus=0.0
    financial_goals=[]

    if goals==[]:
        return {'client_data': client_data, 'surplus_from_goals': surplus, 'financial_goals': financial_goals}            
    current_date=date.today()
    for goal in goals:
        if goal['target_year']-current_date.year >= 0:            # target year should not be less than current year
            future_value_of_saved=calculate_future_value(goal.get('amount_saved_for_goal',0), 0.09, goal['target_year']-current_date.year )
            capital_required_at_target_year=calculate_future_value(goal['capital_required_today'], 0.06, goal['target_year']-current_date.year)
            goal['future_value_of_saved_amount']=future_value_of_saved
            if future_value_of_saved>0:
                goal['funded_from']=[{'future_value_of_allocated_funds': future_value_of_saved}]
            goal['capital_required_at_target_year']=capital_required_at_target_year
    
    goals.sort(key=lambda x:x['target_year'])

    for goal in goals:
        
        goal_gap=goal['capital_required_at_target_year']-goal['future_value_of_saved_amount']
        if goal_gap>0:
            if surplus>0: 
                #print(f"considering the surplus collected from previous goals: {surplus}, the new gap is: {goal_gap}")
                goal_gap=goal_gap-surplus 
                goal['goal_gap']=goal_gap 
                goal['funded_from'].append({'surplus_from_previous_goal': surplus})
                # sip_required=calculate_required_sip(goal_gap,0.09, goal['target_year']-current_date.year)
                # goal['sip_required']=sip_required
                # goal['sip_month']=int((goal['target_year']-current_date.year)*12)
            else: 
                goal['goal_gap']=goal_gap
                # sip_required=calculate_required_sip(goal_gap,0.09, goal['target_year']-current_date.year)
                # goal['sip_required']=sip_required
                # goal['sip_month']=int((goal['target_year']-current_date.year)*12)
        elif goal_gap==0: 
            goal['goal_gap']=0
            # goal['sip_required']=0
            # goal['sip_month']=int((goal['target_year']-current_date.year)*12)
        elif goal_gap<0: 
            goal['goal_gap']=0 
            # goal['sip_required']=0  
            # goal['sip_month']=int((goal['target_year']-current_date.year)*12)
            surplus+= -1*goal_gap  
 
    for goal in client_data['financial_goals']: 
        financial_goals.append({'goal_name': goal['goal_name'] ,'target_corpus': goal['capital_required_at_target_year'], 'corpus_needed': goal['goal_gap'], 'corpus_gap': goal['goal_gap'], 'funded_from': goal.get('funded_from',[]),'target_year': goal['target_year'] })
    
    print(f"financial_goals: {financial_goals}\n")
    print("--------------------------"*6)
    return {'client_data': client_data, 'surplus_from_goals': surplus, 'financial_goals': financial_goals} 

def _score_loan_for_goal(loan: dict, client_data: dict) -> float:
    """
    Compute a dynamic loan score used as the 'weight' when a post-retirement
    loan is injected as a goal into goal_prioritization.

    Loan Score = (Interest Rate Weight × 0.4) + (EMI Burden × 0.3) + (Tenure Risk × 0.3)
    """
    today = date.today()
    client_info = client_data.get('client_data', {})
    retirement_age = float(client_info.get('retirement_age', 60))
    client_age = float(client_info.get('client_age', 35))
    monthly_salary = float(client_data.get('financial_summary', {}).get('monthly_salary', 0) or
                           client_info.get('monthly_salary', 0))
    other_income = float(client_data.get('financial_summary', {}).get('other_income(rental/interest/other)', 0) or
                         client_info.get('other_income(rental/interest/other)', 0))
    gross_monthly_income = monthly_salary + other_income

    P = float(loan.get('outstanding_balance', 0))
    rate = float(loan.get('interest_rate', 0))
    EMI = float(loan.get('emi_amount', 0))
    r = rate / 12.0

    if rate > 0.12:
        interest_weight = 8
    elif rate >= 0.09:
        interest_weight = 5
    else:
        interest_weight = 2

    emi_ratio = (EMI / gross_monthly_income) if gross_monthly_income > 0 else 0.0
    if emi_ratio > 0.50:
        emi_burden_score = 5
    elif emi_ratio >= 0.30:
        emi_burden_score = 7
    else:
        emi_burden_score = 3

    months_to_retirement = max((retirement_age - client_age) * 12, 1)
    loan_months = remaining_tenure(P, r, EMI)
    if loan_months == float('inf') or loan_months == 'inf':
        tenure_risk_score = 10
    elif float(loan_months) > months_to_retirement:
        tenure_risk_score = 10
    else:
        tenure_risk_score = round((float(loan_months) / months_to_retirement) * 10, 1)

    return round((interest_weight * 0.4) + (emi_burden_score * 0.3) + (tenure_risk_score * 0.3), 2)


def add_goals(state: ClientState):
    print("--------------------------"*6)
    print("\n")
    print("Node: add_goals \n")
    print("Combining all the goals... \n")
    financial_goals = state['financial_goals']
    education_goals = state['children_education_planning']
    retirement_goals = state['retirement_goal']
    goals = financial_goals + education_goals + retirement_goals

    # Inject post-retirement loans as loan_closure goals
    client_data = state['client_data']
    client_info = client_data.get('client_data', {})
    retirement_age = int(client_info.get('retirement_age', 60))
    client_age = int(client_info.get('client_age', 35))
    today = date.today()
    retirement_year = today.year + (retirement_age - client_age)
    liabilities = client_data.get('liabilities', [])

    loan_closure_goals = []
    for loan in liabilities:
        P = float(loan.get('outstanding_balance', 0))
        rate = float(loan.get('interest_rate', 0))
        EMI = float(loan.get('emi_amount', 0))
        r = rate / 12.0
        if P <= 0 or EMI <= 0:
            continue
        loan_months = remaining_tenure(P, r, EMI)
        if loan_months == float('inf') or loan_months == 'inf':
            continue
        close_date = _add_months(today, int(loan_months))
        if close_date.year > retirement_year:
            loan_score = _score_loan_for_goal(loan, client_data)
            loan_closure_goals.append({
                'goal_name': f"Loan Closure: {loan.get('type', 'Loan')}",
                'target_year': retirement_year,
                'corpus_needed': P,
                'corpus_gap': P,
                'target_corpus': P,
                'capital_required_at_target_year': P,
                'future_value_of_saved_amount': 0.0,
                'goal_type': 'loan_closure',
                'loan_ref': loan,
                'weight': loan_score,
                'funded': False,
                'funded_from': []
            })

    if loan_closure_goals:
        print(f"Injecting {len(loan_closure_goals)} post-retirement loan closure goal(s): "
              f"{[g['goal_name'] for g in loan_closure_goals]}\n")

    goals = goals + loan_closure_goals

    print(f"goals: {goals}\n")
    print("--------------------------"*6)
    return {'goals': goals}
