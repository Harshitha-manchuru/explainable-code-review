import logging

from fastapi import APIRouter, HTTPException

from app.analysis.flag_normalizer import normalize_flags
from app.analysis.static_analyzer import analyze_code
from app.api.schemas import (
    CodeSubmissionRequest,
    CodeSubmissionResponse,
    FaithfulnessScoreSchema,
    FaithfulnessSummarySchema,
    FlagFeedbackSchema,
    RuleCitationSchema,
)
from app.config import MAX_CODE_LENGTH_CHARS
from app.generation.explainer import explain_all_flags

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["submission"])


@router.post("/submit", response_model=CodeSubmissionResponse)
def submit_code(payload: CodeSubmissionRequest) -> CodeSubmissionResponse:

    source_code = payload.code

    if len(source_code) > MAX_CODE_LENGTH_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Submitted code exceeds {MAX_CODE_LENGTH_CHARS} characters."
        )

    analysis_result = analyze_code(source_code)

    if analysis_result.syntax_error:
        return CodeSubmissionResponse(
            syntax_error=analysis_result.syntax_error,
            total_flags=0,
            feedback=[],
            faithfulness_summary=FaithfulnessSummarySchema(
                overall_score=0.0,
                faithful_count=0,
                unfaithful_count=0,
                uncertain_count=0,
                total_checked=0,
                label="disabled",
            ),
        )

    normalized_flags = normalize_flags(analysis_result)

    if not normalized_flags:
        return CodeSubmissionResponse(
            syntax_error=None,
            total_flags=0,
            feedback=[],
            faithfulness_summary=FaithfulnessSummarySchema(
                overall_score=0.0,
                faithful_count=0,
                unfaithful_count=0,
                uncertain_count=0,
                total_checked=0,
                label="disabled",
            ),
        )

    try:
        explanations = explain_all_flags(
            normalized_flags,
            source_code,
        )
    except Exception as exc:
        logger.error("Explanation generation failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate explanations."
        ) from exc

    feedback_items = []

    for explanation in explanations:

        cited_rules_schema = [
            RuleCitationSchema(
                rule_id=rule.rule_id,
                source=rule.source,
                title=rule.title,
                rationale=rule.rationale,
                good_example=rule.good_example,
                bad_example=rule.bad_example,
                relevance_score=rule.relevance_score,
            )
            for rule in explanation.cited_rules
        ]

        feedback_items.append(
            FlagFeedbackSchema(
                flag_id=explanation.flag_id,
                line=explanation.line,
                severity=explanation.severity,
                raw_code=explanation.raw_code,
                linter_message=explanation.linter_message,
                explanation_text=explanation.explanation_text,
                cited_rules=cited_rules_schema,
                faithfulness=None,
            )
        )

    return CodeSubmissionResponse(
        syntax_error=None,
        total_flags=len(feedback_items),
        feedback=feedback_items,
        faithfulness_summary=FaithfulnessSummarySchema(
            overall_score=0.0,
            faithful_count=0,
            unfaithful_count=0,
            uncertain_count=0,
            total_checked=0,
            label="disabled",
        ),
    )

