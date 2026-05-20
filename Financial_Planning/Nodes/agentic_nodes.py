"""
AI-Powered Analysis - Risk & Prioritization

What this file does:
This script leverages LLM agents with custom tools to perform intelligent financial analysis.
It assesses risk tolerance and prioritizes goals using structured reasoning and tool execution.

What this file contains and processes:
- risk_appetite_assessment: LLM agent analyzes equity exposure and years to retirement to classify risk appetite (Low/Medium/Medium to High/Medium to Low) with reasoning
- goal_prioritization: LLM agent with tools calculates priority scores for each goal based on weights and urgency, then sorts goals by descending priority
"""

# agentic nodes: risk_appetite_assessment, goal_prioritization 
from Financial_Planning.Models.client_data_state import ClientState
from langchain.tools import tool
from Financial_Planning.Agent.agent import (Agent)
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from Financial_Planning.Toools.custom_tools import (risk_analysis, calculate_priority_score, sort_goals_by_priority)
from Financial_Planning.Utilities.prompts import (risk_appetite_prompt, goal_prioritization_system_prompt)
from Financial_Planning.Models.llm_schemas import (RiskSchema, PrioritizedGoals)
from Financial_Planning.Utilities.utility_functions import (sip_required)
import os
import copy
from datetime import date

load_dotenv()

AZURE_API_KEY=os.getenv('AZURE_API_KEY')
AZURE_API_BASE=os.getenv('AZURE_API_BASE')
AZURE_API_VERSION=os.getenv('AZURE_API_VERSION')
AZURE_DEPLOYMENT_NAME=os.getenv('AZURE_DEPLOYMENT_NAME')

llm_azure = AzureChatOpenAI(
    api_key=AZURE_API_KEY,  # AZURE_API_KEY
    azure_endpoint=AZURE_API_BASE,  # AZURE_API_BASE
    api_version=AZURE_API_VERSION,  # AZURE_API_VERSION
    deployment_name=AZURE_DEPLOYMENT_NAME,  # AZURE_DEPLOYMENT_NAME
    temperature=0  # Optional
)

def risk_appetite_assessment(state: ClientState): 
    """
    Assess the client’s risk appetite based on equity exposure and years to retirement.
    Purpose:
        Provides a structured risk appetite classification that downstream LLMs or planning
        modules can use in financial recommendations.
    """
    print("--------------------------"*6)
    print("\n")
    print("Node: risk_appetite_assessment \n")
    print("Assessing the risk appetite based on exposure to equity and years left to retirment... \n")
    client_assets=state['client_data']["investment_details"]
    year_to_retire={state['client_data']['client_data']['retirement_age']-state['client_data']['client_data']['client_age']}
    client_name=state['client_data']['client_data']['name']

    agent=Agent(model=llm_azure, tools=[risk_analysis], system=risk_appetite_prompt)
    risk_llm=llm_azure.with_structured_output(RiskSchema)
    
    response=agent.graph.invoke({'messages': [HumanMessage(content=f"The customer's name is {client_name}, current assets include {client_assets} and will be retired in {year_to_retire} years.")]})
    response=risk_llm.invoke(response['messages'][-1].content)
    risk_appetite_analysis={'risk_appetite': response.risk_assessment, 'reason': response.reason_of_risk_assessment}

    print(f"risk_appetite_analysis: {risk_appetite_analysis}\n")
    print("--------------------------"*6)
    return {'risk_appetite': risk_appetite_analysis} 

def goal_prioritization(state: ClientState):
    """
    Prioritize financial goals using LLM + tool-assisted scoring and sorting.
    Purpose: 
        Ensures client’s goals are ranked systematically for allocation planning,
        considering both subjective importance (weights) and timing (target year).
    """ 
    print("--------------------------"*6)
    print("\n")
    print("Node: goal_prioritization")
    print("Prioritizing goals based on the priority score... \n")   
    goalS=state['goals']
    # print(f"goals: {goalS} \n")
    client_agE=state['client_data']['client_data']['client_age']         #client age is compulsory data
    financial_infO=state['financial_overview']                                           

    agent=Agent(model=llm_azure, tools=[calculate_priority_score, sort_goals_by_priority], system=goal_prioritization_system_prompt)
    structured_goal_llm=llm_azure.with_structured_output(PrioritizedGoals)

    result=agent.graph.invoke({'messages': [HumanMessage(content=f'Prioritize the goals, goals: {goalS}, Financial Info: {financial_infO}, client age: {client_agE}')]})
    # print(result['messages'][-1].content)
    response=structured_goal_llm.invoke(f'Format the goals such that they align with the schema expected. The sorted goal are: {result['messages'][-1].content}').goals
    sorted_goals=[g.dict() for g in response]
    goals=copy.deepcopy(sorted_goals)
    sip_goals=[] 
    current_date=date.today() 
    for goal in goals:   
        if goal['corpus_needed']>0.1*goal['target_corpus']:
            amt=sip_required( goal['corpus_needed'], 0.09, (goal['target_year']-current_date.year)*12 )
            sip_goals.append({'goal_name': goal['goal_name'], 'target_year': goal['target_year'], 'corpus_gap': goal['corpus_needed'], 'sip_needed': round(amt), 'interest_rate': 0.09})      
    # print(f"sorted_goals: {sorted_goals}")
    print(f"Sorted Goals: {sorted_goals}\n")
    print("--------------------------"*6)
    return {'sorted_goals': sorted_goals, 'sip_for_goal': sip_goals}
