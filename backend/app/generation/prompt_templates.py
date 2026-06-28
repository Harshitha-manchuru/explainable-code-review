"""
Prompt construction for the explanation generator.

The template explicitly instructs the model to ground its explanation
ONLY in the retrieved rule text, and to avoid introducing claims not
supported by the rationale or examples. This grounding instruction is
what the faithfulness checker subsequently verifies.
"""

from app.retrieval.retriever import RetrievedRule


def build_explanation_prompt(
    code_line: str, flag_message: str, rule: RetrievedRule
) -> str:
    """
    Builds a prompt asking the LLM to explain why the flagged code line
    violates the given rule, using only the rule's own rationale and
    examples as grounding material.
    """
    return f"""You are a Python programming tutor helping a student understand a code review comment.

You must base your explanation STRICTLY on the rule information provided below. Do not invent additional rules, do not reference style guidelines that are not mentioned here, and do not make claims that are not directly supported by the Rationale text.

Flagged Code Line:
{code_line}

Linter Message:
{flag_message}

Rule Source: {rule.source}
Rule Title:
{rule.title}

Rationale:
{rule.rationale}

Bad Example:
{rule.bad_example}

Good Example:
{rule.good_example}

Write a concise, beginner-friendly explanation (3-5 sentences) of why the flagged line violates this rule and how the student should fix it. Reference the rationale directly. Do not introduce any rule, fact, or stylistic claim that is not present in the Rationale, Bad Example, or Good Example above.
"""


def build_faithfulness_premise(rule: RetrievedRule) -> str:
    """
    Builds the 'premise' text used by the NLI faithfulness checker: the
    full grounding context the explanation is supposed to be entailed by.
    """
    return (
        f"{rule.title}. {rule.rationale} "
        f"Bad example: {rule.bad_example} "
        f"Good example: {rule.good_example}"
    )
