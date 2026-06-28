"""
Lightweight knowledge base loader (no vector database, no embeddings).

Loads all three knowledge base JSON files into memory and exposes them
as a simple in-memory RuleStore. This replaces the original ChromaDB-
backed implementation while keeping the same public entry point
(`build_or_get_collection`) so retriever.py does not need to change how
it obtains the store.

Run directly to sanity-check the knowledge base loads correctly:
    python -m app.retrieval.embed_rules
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.config import (
    ANTI_PATTERNS_PATH,
    GOOGLE_STYLE_PATH,
    PEP8_RULES_PATH,
)


def _load_json(path: Path) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class RuleStore:
    """
    In-memory store of all knowledge base rules, keyed by rule_id.
    Provides the minimal lookup surface retriever.py needs: get a rule
    by id, or iterate all rules for keyword matching.
    """

    def __init__(self, rules: List[dict]) -> None:
        self._rules_by_id: Dict[str, dict] = {r["rule_id"]: r for r in rules}
        self._all_rules: List[dict] = rules

    def count(self) -> int:
        return len(self._all_rules)

    def get_by_id(self, rule_id: str) -> Optional[dict]:
        return self._rules_by_id.get(rule_id)

    def all_rules(self) -> List[dict]:
        return self._all_rules


_rule_store: Optional[RuleStore] = None


def _load_all_rules() -> List[dict]:
    return (
        _load_json(PEP8_RULES_PATH)
        + _load_json(GOOGLE_STYLE_PATH)
        + _load_json(ANTI_PATTERNS_PATH)
    )


def build_or_get_collection() -> RuleStore:
    """
    Returns the in-memory RuleStore, building it on first call and
    reusing it afterwards. Name kept identical to the original ChromaDB
    version so retriever.py's import and call site are unchanged.
    """
    global _rule_store
    if _rule_store is None:
        _rule_store = RuleStore(_load_all_rules())
    return _rule_store


if __name__ == "__main__":
    store = build_or_get_collection()
    print(f"Loaded {store.count()} rules into in-memory RuleStore (no vector DB).")