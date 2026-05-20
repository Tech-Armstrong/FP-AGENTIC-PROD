"""
LLM Output Schemas - Structured Response Models

What this file does:
This script defines Pydantic schemas for structured LLM outputs using .with_structured_output().
It ensures LLM responses conform to expected formats for downstream processing.

What this file contains:
- RiskSchema: Schema for risk appetite assessment with classification and reasoning
- Goal: Individual goal schema with priority scoring
- PrioritizedGoals: List of goals sorted by priority
- slide7_llm: Financial overview text for PPT slide 7
- slide8_llm: Retirement planning explanation for PPT slide 8
- retirement_commentary: Short retirement analysis commentary
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any

class RiskSchema(BaseModel):
    risk_assessment: Literal['Low', 'Medium', 'Medium to High', 'Medium to Low'] = Field(
        description='Marks risk appetite of the user')
    reason_of_risk_assessment: str = Field(
        description='Reason for the risk assessment chosen based on the conditions provided')

from typing import List, Dict
from pydantic import BaseModel, Field

class FundingSource(BaseModel):
    source: str = Field(..., description="Name of the funding source")
    amount: float = Field(..., description="Amount from this source")

class Goal(BaseModel):
    goal_name: str = Field(..., description="Name of the financial goal")
    target_corpus: float = Field(..., description="Target corpus of the goal")
    target_year: int = Field(..., description="The year the goal should be achieved")
    corpus_needed: float = Field(..., description="Total corpus required for the goal")
    corpus_gap: float = Field(..., description="Gap between required and available corpus")
    funded_from: List[FundingSource] = Field(default_factory=list, description="Funding sources for this goal")
    # surplus: float = Field(default=0.0, description="Any surplus funds allocated to the goal")
    priority_score: float = Field(..., description="The calculated priority score for the goal")

class PrioritizedGoals(BaseModel):
    goals: List[Goal] = Field(..., description="Prioritized list of goals")


class RiskSchema(BaseModel):
    risk_assessment: Literal['Low', 'Medium', 'Medium to High', 'Medium to Low'] = Field(
        description='Marks risk appetite of the user')
    reason_of_risk_assessment: str = Field(
        description='Reason for the risk assessment chosen based on the conditions provided')

class slide7_llm(BaseModel):
    financial_overview: str=Field(description="Overview of the financial parameters provided.")

class slide8_llm(BaseModel):
    retirement_plan : str=Field(description="Retirement planning explanation. ")

class retirement_commentary(BaseModel):
    commentary: str= Field(description="Short analysis of retirement fields")

class fees_list(BaseModel): 
    fee_list : List[float] = Field(description="List of college fees")

class GraduationFee(BaseModel):
    """Schema for graduation fee data scraped from web."""
    graduation_destination: Literal['International', 'Domestic'] = Field(
        description="Destination of graduation study: International (UK) or Domestic (India)")
    graduation_stream: Literal['Engineering', 'Medical', 'Commerce', 'General'] = Field(
        description="Stream of graduation study")
    current_fees_of_graduation: float = Field(
        gt=0,
        lt=100000000,
        description="Total course fees for graduation in INR (must be > 0 and < 10 crore)")

class PostGraduationFee(BaseModel):
    """Schema for post-graduation fee data scraped from web."""
    post_graduation_destination: Literal['International', 'Domestic'] = Field(
        description="Destination of post-graduation study: International (UK) or Domestic (India)")
    post_graduation_stream: Literal['MBA', 'M.Tech', 'MD', 'M.Com', 'General'] = Field(
        description="Stream of post-graduation study")
    current_fees_of_post_graduation: float = Field(
        gt=0,
        lt=100000000,
        description="Total course fees for post-graduation in INR (must be > 0 and < 10 crore)")

class Finalblock(BaseModel):
    final_block_summary: str = Field(
        description=(
            "A concise, well-structured financial summary written in bullet points. "
            "Each point should provide clear insights, goal statuses, or recommendations "
            "based on the provided financial data — for example, highlighting funded goals, "
            "liquidity position, or key action steps for the client."
        )
    )


class Edu_commentator(BaseModel):
    edu_comm: str = Field(
        description=(
            "A concise, presentation-ready paragraph explaining the child’s education goal outlook. "
            "The text should summarize what the goal is (UG/PG, stream, destination, and target year), "
            "the current and projected cost of education, and the goal’s funding status (funded, partially funded, or unfunded). "
            "If funded or partially funded, include a closing sentence indicating that the recommended investment strategy "
            "and allocation details are provided below. "
            "Use a professional and client-facing tone, addressing the customer as 'you/your' and the organization as 'we/us'. "
            "Keep the response crisp (3–5 sentences), clear, and suitable for a financial presentation slide."
        )
    )
