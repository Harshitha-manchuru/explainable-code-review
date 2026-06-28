import React, { useState } from "react";

const SEVERITY_LABEL = {
  high: "High",
  warning: "Warning",
  info: "Info",
};

const FAITHFULNESS_LABEL = {
  faithful: "Faithful",
  unfaithful: "Unfaithful",
  uncertain: "Uncertain",
};

function EntailmentBar({ score, label }) {
  const pct = Math.round(score * 100);
  return (
    <div className={`entailment-bar entailment-bar--${label}`}>
      <div className="entailment-bar__track">
        <div
          className="entailment-bar__fill"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="entailment-bar__value">{pct}%</span>
    </div>
  );
}

function RuleCitation({ rule }) {
  return (
    <div className="citation-card">
      <div className="citation-card__header">
        <span className="citation-card__source">{rule.source}</span>
        <span className="citation-card__id">{rule.rule_id}</span>
      </div>
      <p className="citation-card__title">{rule.title}</p>
      <p className="citation-card__rationale">{rule.rationale}</p>
      <div className="citation-card__examples">
        <div className="citation-card__example citation-card__example--bad">
          <span className="citation-card__example-label">Bad</span>
          <code>{rule.bad_example}</code>
        </div>
        <div className="citation-card__example citation-card__example--good">
          <span className="citation-card__example-label">Good</span>
          <code>{rule.good_example}</code>
        </div>
      </div>
    </div>
  );
}

function FlagCard({ flag }) {
  const [expanded, setExpanded] = useState(false);
  const faithfulness = flag.faithfulness;

  return (
    <div className="flag-card">
      <button
        className="flag-card__header"
        onClick={() => setExpanded((e) => !e)}
      >
        <span className={`flag-card__severity flag-card__severity--${flag.severity}`}>
          {SEVERITY_LABEL[flag.severity] || flag.severity}
        </span>
        <span className="flag-card__line">Line {flag.line}</span>
        <span className="flag-card__code">{flag.raw_code}</span>
        <span className="flag-card__chevron">{expanded ? "▾" : "▸"}</span>
      </button>

      <p className="flag-card__linter-message">{flag.linter_message}</p>

      {expanded && (
        <div className="flag-card__body">
          <div className="flag-card__explanation">
            <span className="flag-card__section-label">Explanation</span>
            <p>{flag.explanation_text}</p>
          </div>

          {faithfulness && (
            <div className="flag-card__faithfulness">
              <span className="flag-card__section-label">
                Faithfulness ({FAITHFULNESS_LABEL[faithfulness.label] || faithfulness.label})
              </span>
              <EntailmentBar
                score={faithfulness.entailment_score}
                label={faithfulness.label}
              />
              <div className="flag-card__faithfulness-detail">
                <span>Entailment {Math.round(faithfulness.entailment_score * 100)}%</span>
                <span>Contradiction {Math.round(faithfulness.contradiction_score * 100)}%</span>
                <span>Neutral {Math.round(faithfulness.neutral_score * 100)}%</span>
              </div>
            </div>
          )}

          {flag.cited_rules?.length > 0 && (
            <div className="flag-card__citations">
              <span className="flag-card__section-label">
                Retrieved Rules ({flag.cited_rules.length})
              </span>
              {flag.cited_rules.map((rule) => (
                <RuleCitation key={rule.rule_id} rule={rule} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SummaryBar({ summary, totalFlags }) {
  if (!summary || totalFlags === 0) return null;
  return (
    <div className={`summary-bar summary-bar--${summary.label}`}>
      <div className="summary-bar__score">
        <span className="summary-bar__score-value">
          {Math.round(summary.overall_score * 100)}%
        </span>
        <span className="summary-bar__score-label">Overall Faithfulness</span>
      </div>
      <div className="summary-bar__breakdown">
        <span>{summary.faithful_count} faithful</span>
        <span>{summary.unfaithful_count} unfaithful</span>
        <span>{summary.uncertain_count} uncertain</span>
      </div>
    </div>
  );
}

export default function FeedbackPanel({ result, isLoading, error }) {
  if (isLoading) {
    return (
      <div className="feedback-pane">
        <div className="feedback-pane__empty">
          <p>Running static analysis, retrieval, and explanation pipeline…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="feedback-pane">
        <div className="feedback-pane__empty feedback-pane__empty--error">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="feedback-pane">
        <div className="feedback-pane__empty">
          <p>Submit code on the left to see grounded, citation-backed feedback.</p>
        </div>
      </div>
    );
  }

  if (result.syntax_error) {
    return (
      <div className="feedback-pane">
        <div className="feedback-pane__empty feedback-pane__empty--error">
          <p className="feedback-pane__syntax-label">Syntax Error</p>
          <p>{result.syntax_error}</p>
        </div>
      </div>
    );
  }

  if (result.total_flags === 0) {
    return (
      <div className="feedback-pane">
        <div className="feedback-pane__empty feedback-pane__empty--clean">
          <p>No issues found. The submitted code is clean.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-pane">
      <SummaryBar summary={result.faithfulness_summary} totalFlags={result.total_flags} />
      <div className="feedback-pane__list">
        {result.feedback.map((flag) => (
          <FlagCard key={flag.flag_id} flag={flag} />
        ))}
      </div>
    </div>
  );
}
