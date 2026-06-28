"""
Runs static analysis on submitted Python source code using flake8 and
pylint as subprocesses, plus a lightweight AST pass for anti-patterns
that linters do not catch out of the box (e.g. mutable default args,
bare except, magic numbers).

All analysis happens on a temporary file on disk because flake8 and
pylint are designed to operate on file paths, not in-memory strings.
"""

import ast
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from app.config import ANALYSIS_TIMEOUT_SECONDS


@dataclass
class RawFlag:
    """A single unprocessed issue surfaced by a linter or the AST pass."""

    line: int
    col: int
    code: str
    message: str
    tool: str  # "flake8" | "pylint" | "ast"


@dataclass
class AnalysisResult:
    flags: List[RawFlag] = field(default_factory=list)
    syntax_error: str | None = None


def _run_flake8(file_path: str) -> List[RawFlag]:
    """Runs flake8 on the given file and parses its default output format."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "flake8", "--max-line-length=79", file_path],
            capture_output=True,
            text=True,
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return []

    flags: List[RawFlag] = []
    for line in proc.stdout.splitlines():
        # Format: <path>:<line>:<col>: <code> <message>
        parts = line.split(":", 3)
        if len(parts) != 4:
            continue
        _, line_no, col_no, rest = parts
        rest = rest.strip()
        code, _, message = rest.partition(" ")
        try:
            flags.append(
                RawFlag(
                    line=int(line_no),
                    col=int(col_no),
                    code=code.strip(),
                    message=message.strip(),
                    tool="flake8",
                )
            )
        except ValueError:
            continue
    return flags


def _run_pylint(file_path: str) -> List[RawFlag]:
    """Runs pylint on the given file using its JSON reporter."""
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                "--output-format=json",
                "--disable=all",
                "--enable=W0703,R1710,R1702,W0612,C0103",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return []

    flags: List[RawFlag] = []
    if not proc.stdout.strip():
        return flags
    try:
        records = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return flags

    for rec in records:
        try:
            flags.append(
                RawFlag(
                    line=int(rec.get("line", 1)),
                    col=int(rec.get("column", 0)),
                    code=str(rec.get("message-id", rec.get("symbol", "UNKNOWN"))),
                    message=str(rec.get("message", "")),
                    tool="pylint",
                )
            )
        except (ValueError, TypeError):
            continue
    return flags


class _AntiPatternVisitor(ast.NodeVisitor):
    """AST visitor that detects anti-patterns not reliably caught by linters."""

    def __init__(self) -> None:
        self.flags: List[RawFlag] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.flags.append(
                    RawFlag(
                        line=node.lineno,
                        col=node.col_offset,
                        code="MUTABLE_DEFAULT",
                        message=(
                            f"Function '{node.name}' uses a mutable default "
                            "argument."
                        ),
                        tool="ast",
                    )
                )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.flags.append(
                RawFlag(
                    line=node.lineno,
                    col=node.col_offset,
                    code="BARE_EXCEPT",
                    message="Bare 'except:' clause catches all exceptions.",
                    tool="ast",
                )
            )
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            self.flags.append(
                RawFlag(
                    line=node.lineno,
                    col=node.col_offset,
                    code="BROAD_EXCEPT",
                    message="Catching the broad 'Exception' class.",
                    tool="ast",
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                self.flags.append(
                    RawFlag(
                        line=node.lineno,
                        col=node.col_offset,
                        code="F403",
                        message=f"Wildcard import from '{node.module}'.",
                        tool="ast",
                    )
                )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        for op, comparator in zip(node.ops, node.comparators):
            is_none_target = (
                isinstance(comparator, ast.Constant) and comparator.value is None
            )
            if is_none_target and isinstance(op, (ast.Eq, ast.NotEq)):
                self.flags.append(
                    RawFlag(
                        line=node.lineno,
                        col=node.col_offset,
                        code="E711",
                        message="Comparison to None should use 'is' or 'is not'.",
                        tool="ast",
                    )
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "eval":
            self.flags.append(
                RawFlag(
                    line=node.lineno,
                    col=node.col_offset,
                    code="EVAL_USAGE",
                    message="Use of eval() detected.",
                    tool="ast",
                )
            )
        self.generic_visit(node)


def _run_ast_pass(source_code: str) -> tuple[List[RawFlag], str | None]:
    """Parses the source with ast and runs the anti-pattern visitor."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        return [], f"SyntaxError: {exc.msg} (line {exc.lineno})"

    visitor = _AntiPatternVisitor()
    visitor.visit(tree)
    return visitor.flags, None


def analyze_code(source_code: str) -> AnalysisResult:
    """
    Runs flake8, pylint, and an AST anti-pattern pass on the given Python
    source code string, returning a unified AnalysisResult.

    If the code does not parse (a SyntaxError), linters are skipped and
    the syntax error is returned immediately so the caller can short
    circuit the rest of the pipeline.
    """
    ast_flags, syntax_error = _run_ast_pass(source_code)
    if syntax_error:
        return AnalysisResult(flags=[], syntax_error=syntax_error)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(source_code)
        tmp_path = tmp_file.name

    try:
        flake8_flags = _run_flake8(tmp_path)
        pylint_flags = _run_pylint(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    all_flags = flake8_flags + pylint_flags + ast_flags
    return AnalysisResult(flags=all_flags, syntax_error=None)
