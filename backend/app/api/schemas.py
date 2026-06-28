"""
Pydantic schemas for the /api/submit endpoint.

These models mirror the dataclasses already defined in the analysis,
retrieval, generation, and faithfulness layers field-for-field, so the
route handler can convert dataclass -> Pydantic with simple attribute
access and FastAPI can serialize the final response correctly.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------
class CodeSubmissionRequest(BaseModel):
    code: str = Field(
        ..., min_length=1, description="The Python source code to review."
    )


# ---------------------------------------------------------------------
# Shared sub-objects
# ---------------------------------------------------------------------
class RuleCitationSchema(BaseModel):
    rule_id: str
    source: str
    title: str
    rationale: str
    good_example: str
    bad_example: str
    relevance_score: float


class FaithfulnessScoreSchema(BaseModel):
    flag_id: str
    entailment_score: float
    contradiction_score: float
    neutral_score: float
    label: str  # "faithful" | "unfaithful" | "uncertain"


class FlagFeedbackSchema(BaseModel):
    flag_id: str
    line: int
    severity: str  # "info" | "warning" | "high"
    raw_code: str
    linter_message: str
    explanation_text: str
    cited_rules: List[RuleCitationSchema]
    faithfulness: Optional[FaithfulnessScoreSchema] = None


class FaithfulnessSummarySchema(BaseModel):
    overall_score: float
    faithful_count: int
    unfaithful_count: int
    uncertain_count: int
    total_checked: int
    label: str  # "high" | "medium" | "low"


# ---------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------
class CodeSubmissionResponse(BaseModel):
    syntax_error: Optional[str] = None
    total_flags: int
    feedback: List[FlagFeedbackSchema]
    faithfulness_summary: FaithfulnessSummarySchema


class HealthResponse(BaseModel):
    status: str
    llm_mode: str  # "live" | "stub"
