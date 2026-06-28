"""
Retrieval layer: given a normalized flag, fetches the most relevant
knowledge base rule(s) directly from the in-memory RuleStore.

No chromadb, sentence_transformers, torch, or embeddings are used.
Retrieval is purely deterministic: exact rule_id lookup when available,
falling back to keyword overlap scoring between the flag's message and
each rule's title + rationale.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from app.retrieval.embed_rules import build_or_get_collection

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_]+")

_STOPWORDS = {
    "the", "a", "an", "is", "are", "be", "to", "of", "in", "on", "for",
    "and", "or", "should", "must", "this", "that", "with", "as", "it",
    "its", "use", "used", "using", "not", "no", "do", "does", "did",
}


@dataclass
class RetrievedRule:
    rule_id: str
    source: str
    title: str
    rationale: str
    good_example: str
    bad_example: str
    relevance_score: float


def _tokenize(text: str) -> set:
    words = _WORD_RE.findall(text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _to_retrieved_rule(rule: dict, relevance_score: float) -> RetrievedRule:
    return RetrievedRule(
        rule_id=rule["rule_id"],
        source=rule["source"],
        title=rule["title"],
        rationale=rule["rationale"],
        good_example=rule["good_example"],
        bad_example=rule["bad_example"],
        relevance_score=round(relevance_score, 4),
    )


def _exact_lookup(rule_id: str) -> Optional[RetrievedRule]:
    store = build_or_get_collection()
    rule = store.get_by_id(rule_id)
    if rule is None:
        return None
    return _to_retrieved_rule(rule, relevance_score=1.0)


def _keyword_match(query_text: str, top_k: int) -> List[RetrievedRule]:
    """
    Scores every rule by overlap between the query's significant words
    and the rule's title + rationale words. Deterministic: same input
    always produces the same ranked output (ties broken by rule_id).
    """
    store = build_or_get_collection()
    query_tokens = _tokenize(query_text)

    if not query_tokens:
        return []

    scored: List[tuple] = []
    for rule in store.all_rules():
        rule_tokens = _tokenize(f"{rule['title']} {rule['rationale']}")
        if not rule_tokens:
            continue

        overlap = query_tokens & rule_tokens
        if not overlap:
            continue

        score = len(overlap) / min(len(query_tokens), len(rule_tokens))
        scored.append((score, rule["rule_id"], rule))

    scored.sort(key=lambda triple: (-triple[0], triple[1]))
    return [_to_retrieved_rule(rule, score) for score, _, rule in scored[:top_k]]


def retrieve_rules_for_flag(flag, top_k: int = 3) -> List[RetrievedRule]:
    """
    Returns up to top_k relevant knowledge base rules for a normalized
    flag. If flag.candidate_rule_id is set, that rule is looked up
    directly (exact match, relevance_score=1.0) and returned first.
    Remaining slots are filled deterministically via keyword overlap
    between flag.message and each rule's title + rationale.
    """
    results: List[RetrievedRule] = []

    candidate_rule_id = getattr(flag, "candidate_rule_id", None)
    if candidate_rule_id:
        direct = _exact_lookup(candidate_rule_id)
        if direct:
            results.append(direct)

    remaining = top_k - len(results)
    if remaining > 0:
        query_text = getattr(flag, "message", "") or ""
        existing_ids = {r.rule_id for r in results}
        for rule in _keyword_match(query_text, remaining + len(existing_ids)):
            if rule.rule_id in existing_ids:
                continue
            results.append(rule)
            existing_ids.add(rule.rule_id)
            if len(results) >= top_k:
                break

    return results[:top_k]