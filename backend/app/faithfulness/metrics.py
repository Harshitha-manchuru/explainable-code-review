"""
Aggregates per-flag FaithfulnessResult objects into submission-level
summary metrics, used by the API response and (optionally) for
research evaluation logging.
"""

from dataclasses import dataclass
from typing import List

from app.faithfulness.faithfulness_checker import FaithfulnessResult


@dataclass
class FaithfulnessSummary:
    overall_score: float  # mean entailment score across all checked flags
    faithful_count: int
    unfaithful_count: int
    uncertain_count: int
    total_checked: int
    label: str  # "high" | "medium" | "low"


def _overall_label(overall_score: float, total_checked: int) -> str:
    if total_checked == 0:
        return "low"
    if overall_score >= 0.7:
        return "high"
    if overall_score >= 0.4:
        return "medium"
    return "low"


def summarize_faithfulness(
    results: List[FaithfulnessResult],
) -> FaithfulnessSummary:
    """
    Computes submission-level faithfulness metrics from a list of
    per-flag FaithfulnessResult objects. Returns a zero-value summary
    if the list is empty (e.g. no flags were raised on clean code).
    """
    if not results:
        return FaithfulnessSummary(
            overall_score=0.0,
            faithful_count=0,
            unfaithful_count=0,
            uncertain_count=0,
            total_checked=0,
            label="low",
        )

    faithful_count = sum(1 for r in results if r.label == "faithful")
    unfaithful_count = sum(1 for r in results if r.label == "unfaithful")
    uncertain_count = sum(1 for r in results if r.label == "uncertain")

    mean_entailment = round(
        sum(r.entailment_score for r in results) / len(results), 4
    )

    return FaithfulnessSummary(
        overall_score=mean_entailment,
        faithful_count=faithful_count,
        unfaithful_count=unfaithful_count,
        uncertain_count=uncertain_count,
        total_checked=len(results),
        label=_overall_label(mean_entailment, len(results)),
    )
