# Architecture

## Overview

This system reviews Python source code submitted by a student and returns
structured, citation-backed, faithfulness-checked feedback. Every
explanation shown to the student is grounded in a specific, retrievable
rule from a curated knowledge base, and every explanation is scored for
how faithfully it reflects that grounding rule before being returned.

## Pipeline

```
Student code (POST /api/submit)
        |
        v
1. Static Analysis        (app/analysis/static_analyzer.py)
   - flake8 subprocess
   - pylint subprocess (JSON reporter)
   - AST visitor for anti-patterns linters miss
   - short-circuits on SyntaxError
        |
        v
2. Flag Normalization     (app/analysis/flag_normalizer.py)
   - deduplicates overlapping flags from multiple tools
   - maps raw linter/AST codes -> knowledge base rule_id
   - assigns severity (info / warning / high)
        |
        v
3. Retrieval (RAG)         (app/retrieval/retriever.py, embed_rules.py)
   - direct lookup by candidate_rule_id when known
   - semantic fallback via ChromaDB cosine similarity search
   - knowledge base embedded with sentence-transformers (all-MiniLM-L6-v2)
        |
        v
4. Explanation Generation  (app/generation/explainer.py, llm_client.py,
                             prompt_templates.py)
   - prompts Gemini with ONLY the retrieved rule's rationale + examples
   - explicitly instructs the model not to introduce ungrounded claims
   - falls back to a deterministic offline stub if no API key is set
        |
        v
5. Faithfulness Checking   (app/faithfulness/faithfulness_checker.py,
                             metrics.py)
   - NLI CrossEncoder (cross-encoder/nli-deberta-v3-base) scores
     entailment between the retrieved rule (premise) and the generated
     explanation (hypothesis)
   - labels each explanation: faithful / unfaithful / uncertain
   - aggregates submission-level faithfulness summary
        |
        v
6. Structured JSON Response (app/api/schemas.py, routes_submission.py)
        |
        v
React Frontend (Monaco editor + feedback panel with citations and
                entailment score bars)
```

## Why faithfulness checking matters

Explainability is only valuable if the explanation can be trusted. An
LLM can produce a fluent-sounding explanation that subtly contradicts
or extends beyond the actual cited rule. The NLI faithfulness layer
treats the retrieved rule text as the ground truth premise and checks
whether the generated explanation is logically entailed by it. This
gives the student (and the research evaluation) a quantitative signal
for how grounded each piece of feedback actually is, rather than
trusting LLM output on its own.

## Knowledge base

Three JSON files under `backend/knowledge_base/` hold 23 curated rules
across PEP 8, the Google Python Style Guide, and common anti-patterns.
Each rule has a stable `rule_id`, a citable `rationale`, and a paired
`good_example` / `bad_example`, which serve as both the retrieval
corpus and the faithfulness-checking premise.

## Stub mode

If `GEMINI_API_KEY` is not set in `backend/.env`, `app/config.py` sets
`USE_LLM_STUB = True` and `llm_client.py` returns a deterministic
offline explanation built directly from the retrieved rule's title and
rationale. This allows the entire pipeline, including faithfulness
checking, to run end-to-end without any external API access.
