import React, { useState } from "react";
import CodeEditor from "./components/CodeEditor.jsx";
import FeedbackPanel from "./components/FeedbackPanel.jsx";
import { submitCode } from "./api/client.js";

export default function App() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAnalyze() {
    if (!code.trim()) {
      setError("Write or paste some Python code before analyzing.");
      setResult(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await submitCode(code);
      setResult(response);
    } catch (err) {
      setError(err.message || "Something went wrong while analyzing the code.");
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__title">
          <span className="app-header__mark">{"</>"}</span>
          <div>
            <h1>Explainable Code Review</h1>
            <p>RAG-grounded feedback for Python programming education</p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <CodeEditor
          code={code}
          onChange={setCode}
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
        />
        <FeedbackPanel result={result} isLoading={isLoading} error={error} />
      </main>
    </div>
  );
}
