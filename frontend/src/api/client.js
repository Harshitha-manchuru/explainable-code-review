const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Submits Python source code to the backend review pipeline.
 * Mirrors backend/app/api/schemas.py: CodeSubmissionRequest -> CodeSubmissionResponse.
 *
 * @param {string} code
 * @returns {Promise<{
 *   syntax_error: string|null,
 *   total_flags: number,
 *   feedback: Array<{
 *     flag_id: string,
 *     line: number,
 *     severity: string,
 *     raw_code: string,
 *     linter_message: string,
 *     explanation_text: string,
 *     cited_rules: Array<{rule_id: string, source: string, title: string, rationale: string, good_example: string, bad_example: string, relevance_score: number}>,
 *     faithfulness: {flag_id: string, entailment_score: number, contradiction_score: number, neutral_score: number, label: string} | null
 *   }>,
 *   faithfulness_summary: {overall_score: number, faithful_count: number, unfaithful_count: number, uncertain_count: number, total_checked: number, label: string}
 * }>}
 */
export async function submitCode(code) {
  const response = await fetch(`${API_BASE_URL}/api/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ code }),
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const errorBody = await response.json();
      if (errorBody?.detail) {
        detail = errorBody.detail;
      }
    } catch {
      // response body was not JSON; keep the generic message
    }
    throw new Error(detail);
  }

  return response.json();
}

/**
 * Checks backend health and reports whether the LLM is live or stubbed.
 * @returns {Promise<{status: string, llm_mode: "live"|"stub"}>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json();
}
