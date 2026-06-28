"""
Checks whether each LLM-generated explanation is faithful to (entailed
by) the retrieved rule text it was supposed to be grounded in, using a
pretrained NLI CrossEncoder model.

The premise is the rule's rationale + examples (the grounding context).
The hypothesis is the LLM's generated explanation. A high entailment
score means the explanation's claims are supported by the premise; a
low score suggests possible hallucination beyond the retrieved context.
"""

import logging
from dataclasses import dataclass
from typing import List

from sentence_transformers import CrossEncoder

from app.config import FAITHFULNESS_ENTAILMENT_THRESHOLD, NLI_MODEL_NAME
from app.generation.explainer import FlagExplanation
from app.generation.prompt_templates import build_faithfulness_premise

logger = logging.getLogger(__name__)

_nli_model: CrossEncoder | None = None

# Standard label order for cross-encoder/nli-deberta-v3-base and most
# DeBERTa-MNLI-style checkpoints: [contradiction, entailment, neutral].
_LABEL_ORDER = ["contradiction", "entailment", "neutral"]


@dataclass
class FaithfulnessResult:
    flag_id: str
    entailment_score: float
    contradiction_score: float
    neutral_score: float
    label: str  # "faithful" | "unfaithful" | "uncertain"


def _get_model() -> CrossEncoder:
    global _nli_model
    if _nli_model is None:
        logger.info("Loading NLI model '%s' for faithfulness checking.", NLI_MODEL_NAME)
        _nli_model = CrossEncoder(NLI_MODEL_NAME)
    return _nli_model


def _softmax(scores: List[float]) -> List[float]:
    import math

    max_score = max(scores)
    exps = [math.exp(s - max_score) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def _label_from_scores(entailment: float, contradiction: float) -> str:
    if entailment >= FAITHFULNESS_ENTAILMENT_THRESHOLD:
        return "faithful"
    if contradiction >= FAITHFULNESS_ENTAILMENT_THRESHOLD:
        return "unfaithful"
    return "uncertain"


def check_faithfulness(explanation: FlagExplanation) -> FaithfulnessResult:
    """
    Scores a single FlagExplanation's faithfulness against its primary
    cited rule. If no rule was cited (no knowledge base match), the
    explanation cannot be checked and is marked "uncertain" with zero
    scores.
    """
    if not explanation.cited_rules:
        return FaithfulnessResult(
            flag_id=explanation.flag_id,
            entailment_score=0.0,
            contradiction_score=0.0,
            neutral_score=0.0,
            label="uncertain",
        )

    primary_rule = explanation.cited_rules[0]
    premise = build_faithfulness_premise(primary_rule)
    hypothesis = explanation.explanation_text

    model = _get_model()
    raw_scores = model.predict([(premise, hypothesis)])[0]
    probabilities = _softmax(list(raw_scores))

    scores_by_label = dict(zip(_LABEL_ORDER, probabilities))
    entailment = round(float(scores_by_label["entailment"]), 4)
    contradiction = round(float(scores_by_label["contradiction"]), 4)
    neutral = round(float(scores_by_label["neutral"]), 4)

    return FaithfulnessResult(
        flag_id=explanation.flag_id,
        entailment_score=entailment,
        contradiction_score=contradiction,
        neutral_score=neutral,
        label=_label_from_scores(entailment, contradiction),
    )


def check_all_faithfulness(
    explanations: List[FlagExplanation],
) -> List[FaithfulnessResult]:
    """Runs faithfulness checking for every explanation, in order."""
    return [check_faithfulness(exp) for exp in explanations]
