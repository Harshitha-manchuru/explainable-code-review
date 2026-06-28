import React from "react";
import Editor from "@monaco-editor/react";

const DEFAULT_SNIPPET = `def CalculateTotal(Items=[]):
    for i in Items:
        Items.append(i*2)
    try:
        x=Items[0]
    except:
        x = None
    if x == None:
        return
    return x
`;

/**
 * Wraps Monaco Editor configured for Python, dark theme, with an
 * Analyze action the parent controls via onAnalyze.
 */
export default function CodeEditor({ code, onChange, onAnalyze, isLoading }) {
  return (
    <div className="editor-pane">
      <div className="editor-toolbar">
        <span className="editor-toolbar__label">submission.py</span>
        <button
          className="btn btn--primary"
          onClick={onAnalyze}
          disabled={isLoading}
        >
          {isLoading ? "Analyzing…" : "Analyze Code"}
        </button>
      </div>
      <div className="editor-surface">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          defaultValue={DEFAULT_SNIPPET}
          onChange={(value) => onChange(value ?? "")}
          options={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on",
            padding: { top: 16 },
            lineNumbersMinChars: 3,
            renderLineHighlight: "gutter",
          }}
        />
      </div>
    </div>
  );
}
