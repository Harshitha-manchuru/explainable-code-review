"""
Orchestrates explanation generation: for each normalized flag, retrieves
the best matching knowledge base rule and produces a grounded
explanation containing an issue summary, why it matters, the cited
rule's title and rationale, and a suggested fix.

If a Gemini API key is configured, llm_client.generate_text is used to
generate the explanation text. If not (stub mode), a deterministic
local explanation is built directly from the retrieved rule's own
fields, so the pipeline remains fully runnable offline.
"""

from dataclasses import dataclass, field
from typing import List

from app.config import USE_LLM_STUB
from app.generation.llm_client import generate_text
from app.generation.prompt_templates import build_explanation_prompt
from app.retrieval.retriever import RetrievedRule, retrieve_rules_for_flag


@dataclass
class FlagExplanation:
    flag_id: str
    line: int
    severity: str
    raw_code: str
    linter_message: str
    explanation_text: str
    cited_rules: List[RetrievedRule] = field(default_factory=list)


def _extract_code_line(source_code: str, line_number: int) -> str:
    lines = source_code.splitlines()
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


def _build_local_explanation(flag_message: str, rule: RetrievedRule) -> str:
    """
    Deterministically composes an explanation from the retrieved rule's
    own fields, with no LLM call. Used when no Gemini API key is set.
    """
    return (
        f"Issue: {flag_message} "
        f"Why it matters: this violates the rule '{rule.title}' "
        f"({rule.source}). {rule.rationale} "
        f"Suggested fix: refactor the flagged line to match the "
        f"recommended pattern, for example: {rule.good_example}"
    )


def _generate_explanation_text(
    code_line: str, flag_message: str, rule: RetrievedRule
) -> str:
    if USE_LLM_STUB:
        return _build_local_explanation(flag_message, rule)

    prompt = build_explanation_prompt(code_line, flag_message, rule)
    return generate_text(prompt)


def explain_flag(flag, source_code: str) -> FlagExplanation:
    """
    Produces a single grounded explanation for one normalized flag by
    retrieving the best matching rule and generating explanation text
    either via the LLM client or, in stub mode, deterministically from
    the rule's own fields.
    """
    retrieved_rules = retrieve_rules_for_flag(flag)
    code_line = _extract_code_line(source_code, flag.line)

    if not retrieved_rules:
        return FlagExplanation(
            flag_id=flag.flag_id,
            line=flag.line,
            severity=flag.severity,
            raw_code=flag.raw_code,
            linter_message=flag.message,
            explanation_text=(
                f"Issue: {flag.message} No matching style rule was found "
                "in the knowledge base for this issue."
            ),
            cited_rules=[],
        )

    best_rule = retrieved_rules[0]
    explanation_text = _generate_explanation_text(
        code_line, flag.message, best_rule
    )

    return FlagExplanation(
        flag_id=flag.flag_id,
        line=flag.line,
        severity=flag.severity,
        raw_code=flag.raw_code,
        linter_message=flag.message,
        explanation_text=explanation_text,
        cited_rules=retrieved_rules,
    )


def explain_all_flags(normalized_flags, source_code: str) -> List[FlagExplanation]:
    """Generates an explanation for every normalized flag, in order."""
    return [explain_flag(flag, source_code) for flag in normalized_flags]