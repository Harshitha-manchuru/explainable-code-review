"""
Converts the raw, tool-specific flags produced by static_analyzer.py
into a single normalized, deduplicated list of NormalizedFlag objects
that the retrieval layer can consume directly.

The mapping from raw linter/AST codes to knowledge base rule_ids is
the single source of truth connecting "what the linter found" to
"which curated rule explains it".
"""

from dataclasses import dataclass
from typing import List

from app.analysis.static_analyzer import AnalysisResult, RawFlag

# Maps a raw linter/AST code to the rule_id of the relevant knowledge
# base entry (see backend/knowledge_base/*.json). Codes not present
# here are still surfaced but without a guaranteed retrieval match;
# the retriever will fall back to semantic search using the message text.
CODE_TO_RULE_ID = {
    # PEP8 whitespace / formatting
    "E211": "PEP8-E211",
    "E225": "PEP8-E225",
    "E226": "PEP8-E225",
    "E227": "PEP8-E225",
    "E228": "PEP8-E225",
    "E231": "PEP8-E231",
    "E301": "PEP8-E301",
    "E302": "PEP8-E301",
    "E303": "PEP8-E301",
    "E501": "PEP8-E501",
    "E711": "PEP8-E711",
    "E712": "PEP8-E711",
    "N802": "PEP8-N802",
    "N803": "PEP8-N802",
    "N801": "PEP8-N801",
    "E101": "PEP8-E101",
    "W191": "PEP8-E101",
    # Google style guide
    "D100": "GOOGLE-DOCSTRING",
    "D103": "GOOGLE-DOCSTRING",
    "MISSING_DOCSTRING": "GOOGLE-DOCSTRING",
    "MUTABLE_DEFAULT": "GOOGLE-MUTABLE-DEFAULT",
    "B006": "GOOGLE-MUTABLE-DEFAULT",
    "F403": "GOOGLE-IMPORT-STAR",
    "F401": "GOOGLE-IMPORT-STAR",
    "ANN001": "GOOGLE-TYPE-ANNOTATION",
    "ANN201": "GOOGLE-TYPE-ANNOTATION",
    "E722": "GOOGLE-EXCEPTION-NAMING",
    "BARE_EXCEPT": "GOOGLE-EXCEPTION-NAMING",
    "GLOBAL_STATE": "GOOGLE-GLOBAL-VARS",
    # Anti-patterns
    "EVAL_USAGE": "ANTI-EVAL-USE",
    "S307": "ANTI-EVAL-USE",
    "W0703": "ANTI-BROAD-EXCEPT",
    "BROAD_EXCEPT": "ANTI-BROAD-EXCEPT",
    "STRING_CONCAT_LOOP": "ANTI-STRING-CONCAT-LOOP",
    "TYPE_EQUALITY": "ANTI-TYPE-COMPARE",
    "F841": "ANTI-UNUSED-VARIABLE",
    "W0612": "ANTI-UNUSED-VARIABLE",
    "R1702": "ANTI-NESTED-LOOPS-DEEP",
    "TOO_MANY_NESTED_BLOCKS": "ANTI-NESTED-LOOPS-DEEP",
    "MAGIC_NUMBER": "ANTI-MAGIC-NUMBERS",
    "R1710": "ANTI-RETURN-INCONSISTENT",
    "INCONSISTENT_RETURN": "ANTI-RETURN-INCONSISTENT",
}

SEVERITY_MAP = {
    "ast": "warning",
    "flake8": "warning",
    "pylint": "warning",
}
HIGH_SEVERITY_CODES = {"EVAL_USAGE", "S307", "BARE_EXCEPT", "BROAD_EXCEPT", "W0703"}


@dataclass
class NormalizedFlag:
    flag_id: str
    line: int
    col: int
    severity: str  # "info" | "warning" | "high"
    source_tool: str
    raw_code: str
    message: str
    candidate_rule_id: str | None


def _severity_for(code: str, tool: str) -> str:
    if code in HIGH_SEVERITY_CODES:
        return "high"
    return SEVERITY_MAP.get(tool, "warning")


def _dedupe_key(flag: RawFlag) -> tuple:
    rule_id = CODE_TO_RULE_ID.get(flag.code)
    return (flag.line, rule_id or flag.code)


def normalize_flags(analysis_result: AnalysisResult) -> List[NormalizedFlag]:
    """
    Converts an AnalysisResult's raw flags into deduplicated, normalized
    flags. When multiple tools report the same underlying rule on the
    same line, only one normalized flag is kept (first occurrence wins,
    with pylint/flake8 preferred over the AST pass for richer messages).
    """
    if analysis_result.syntax_error:
        return []

    seen: dict[tuple, NormalizedFlag] = {}

    # Process flake8/pylint before ast so their messages win on collision.
    ordered = sorted(
        analysis_result.flags, key=lambda f: 0 if f.tool != "ast" else 1
    )

    for idx, raw in enumerate(ordered):
        key = _dedupe_key(raw)
        if key in seen:
            continue
        rule_id = CODE_TO_RULE_ID.get(raw.code)
        seen[key] = NormalizedFlag(
            flag_id=f"flag-{idx}-{raw.line}-{raw.code}",
            line=raw.line,
            col=raw.col,
            severity=_severity_for(raw.code, raw.tool),
            source_tool=raw.tool,
            raw_code=raw.code,
            message=raw.message,
            candidate_rule_id=rule_id,
        )

    # Stable order: by line number, then by severity (high first).
    severity_rank = {"high": 0, "warning": 1, "info": 2}
    return sorted(
        seen.values(), key=lambda f: (f.line, severity_rank.get(f.severity, 1))
    )
