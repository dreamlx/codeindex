#!/usr/bin/env python3
"""Validate codeindex against real projects.

Runs codeindex CLI commands against real-world PHP/Java/Python projects,
collects structured metrics, uses `claude -p` for AI quality evaluation,
and generates comparison reports with regression detection.

Three validation layers:
  L1: Functional — All CLI commands execute without errors
  L2: Quality   — Output metrics + AI accuracy evaluation
  L3: Experience — Flow continuity and instruction clarity

Usage:
    python scripts/validate_real_projects.py                     # All layers, all projects
    python scripts/validate_real_projects.py --layer l1          # L1 only (fast, no AI)
    python scripts/validate_real_projects.py --layer l2          # L2 metrics + AI
    python scripts/validate_real_projects.py --layer l3          # L3 experience AI
    python scripts/validate_real_projects.py --project php_admin # Single project
    python scripts/validate_real_projects.py --save-baseline     # Save as baseline
    python scripts/validate_real_projects.py --dry-run           # Show plan only

Exit codes:
    0 - All validations passed
    1 - Validation failures or regressions detected
    2 - Configuration/setup error
"""
# ruff: noqa: T201

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATION_DIR = SCRIPT_DIR / "validation"
PROJECTS_YAML = VALIDATION_DIR / "projects.yaml"
BASELINES_DIR = VALIDATION_DIR / "baselines"
REPORTS_DIR = VALIDATION_DIR / "reports"

TIMEOUT_SCAN_ALL = 600  # 10 min
TIMEOUT_PARSE = 30
TIMEOUT_DEFAULT = 120
TIMEOUT_AI_EVAL = 90


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CommandResult:
    """Result of a single CLI command execution."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    elapsed_seconds: float
    timed_out: bool = False


@dataclass
class L1Result:
    """L1 Functional validation results for one project."""

    project_name: str
    commands: list[CommandResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    total_time: float = 0.0

    @property
    def success(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project_name,
            "passed": self.passed,
            "failed": self.failed,
            "total_time": round(self.total_time, 2),
            "commands": [
                {
                    "command": c.command,
                    "exit_code": c.exit_code,
                    "elapsed": round(c.elapsed_seconds, 2),
                    "timed_out": c.timed_out,
                    "stderr_snippet": c.stderr[:200] if c.stderr else "",
                }
                for c in self.commands
            ],
        }


@dataclass
class L2Metrics:
    """L2 Quality metrics for one project."""

    readme_count: int = 0
    readme_total_size_kb: float = 0.0
    parse_success_rate: float = 0.0
    total_files_parsed: int = 0
    total_symbols: int = 0
    total_errors: int = 0
    route_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "readme_count": self.readme_count,
            "readme_total_size_kb": round(self.readme_total_size_kb, 2),
            "parse_success_rate": round(self.parse_success_rate, 4),
            "total_files_parsed": self.total_files_parsed,
            "total_symbols": self.total_symbols,
            "total_errors": self.total_errors,
            "route_count": self.route_count,
        }


@dataclass
class AIEvalResult:
    """Result of a single AI evaluation."""

    eval_name: str
    score: float  # 0-10
    findings: str
    raw_response: str
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "eval_name": self.eval_name,
            "score": self.score,
            "findings": self.findings,
            "success": self.success,
        }


@dataclass
class L2Result:
    """L2 Quality validation results for one project."""

    project_name: str
    metrics: L2Metrics = field(default_factory=L2Metrics)
    ai_evals: list[AIEvalResult] = field(default_factory=list)
    threshold_failures: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.threshold_failures) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project_name,
            "metrics": self.metrics.to_dict(),
            "ai_evals": [e.to_dict() for e in self.ai_evals],
            "threshold_failures": self.threshold_failures,
        }


@dataclass
class L3Result:
    """L3 Experience validation results for one project."""

    project_name: str
    ai_evals: list[AIEvalResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(e.success for e in self.ai_evals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project_name,
            "ai_evals": [e.to_dict() for e in self.ai_evals],
        }


@dataclass
class ProjectResult:
    """Combined results for one project across all layers."""

    project_name: str
    l1: L1Result | None = None
    l2: L2Result | None = None
    l3: L3Result | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"project": self.project_name}
        if self.l1:
            d["l1"] = self.l1.to_dict()
        if self.l2:
            d["l2"] = self.l2.to_dict()
        if self.l3:
            d["l3"] = self.l3.to_dict()
        return d


@dataclass
class Regression:
    """A detected regression between current run and baseline."""

    project: str
    metric: str
    baseline_value: Any
    current_value: Any
    severity: str  # "WARNING" or "REGRESSION"

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "metric": self.metric,
            "baseline": self.baseline_value,
            "current": self.current_value,
            "severity": self.severity,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_projects_yaml() -> dict[str, Any]:
    """Load project registry from YAML file."""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml")
        sys.exit(2)

    if not PROJECTS_YAML.exists():
        print(f"ERROR: {PROJECTS_YAML} not found")
        sys.exit(2)

    with open(PROJECTS_YAML) as f:
        data = yaml.safe_load(f)

    return data.get("projects", {})


def expand_path(path_str: str) -> Path:
    """Expand ~ and resolve path."""
    return Path(os.path.expanduser(path_str)).resolve()


def get_codeindex_version() -> str:
    """Get current codeindex version from pyproject.toml."""
    pyproject = SCRIPT_DIR.parent / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
    return "unknown"


def check_prerequisites() -> tuple[bool, bool]:
    """Check that codeindex and claude are available.

    Returns:
        (codeindex_available, claude_available)
    """
    ci_ok = subprocess.run(
        ["codeindex", "--version"],
        capture_output=True,
        text=True,
    ).returncode == 0

    claude_ok = subprocess.run(
        ["which", "claude"],
        capture_output=True,
        text=True,
    ).returncode == 0

    return ci_ok, claude_ok


# ---------------------------------------------------------------------------
# Command runner
# ---------------------------------------------------------------------------


def run_codeindex_command(
    args: list[str],
    cwd: Path,
    timeout: int = TIMEOUT_DEFAULT,
) -> CommandResult:
    """Run a codeindex CLI command and capture results.

    Args:
        args: Command arguments (without 'codeindex' prefix)
        cwd: Working directory
        timeout: Timeout in seconds
    """
    cmd = ["codeindex"] + args
    cmd_str = " ".join(cmd)
    start = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start
        return CommandResult(
            command=cmd_str,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            elapsed_seconds=elapsed,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return CommandResult(
            command=cmd_str,
            exit_code=-1,
            stdout="",
            stderr=f"Timed out after {timeout}s",
            elapsed_seconds=elapsed,
            timed_out=True,
        )
    except Exception as e:
        elapsed = time.monotonic() - start
        return CommandResult(
            command=cmd_str,
            exit_code=-2,
            stdout="",
            stderr=str(e),
            elapsed_seconds=elapsed,
        )


# ---------------------------------------------------------------------------
# AI Evaluator
# ---------------------------------------------------------------------------


def invoke_claude_eval(prompt: str, timeout: int = TIMEOUT_AI_EVAL) -> dict[str, Any]:
    """Invoke claude -p with a JSON-structured prompt.

    Args:
        prompt: The full prompt text (should end with JSON instruction)
        timeout: Timeout in seconds

    Returns:
        Parsed JSON dict, or fallback dict with score=0 on failure
    """
    fallback = {"score": 0, "findings": "AI evaluation failed", "answer": ""}

    try:
        # Remove CLAUDECODE env var to allow nested invocation via `claude -p`
        env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if result.returncode != 0:
            fallback["findings"] = f"claude exited with code {result.returncode}: {result.stderr[:200]}"
            return fallback

        output = result.stdout.strip()

        # Try to extract JSON from markdown code fences
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", output, re.DOTALL)
        if json_match:
            output = json_match.group(1).strip()

        # Try direct JSON parse
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            # Try to find JSON object in output
            brace_match = re.search(r"\{.*\}", output, re.DOTALL)
            if brace_match:
                try:
                    return json.loads(brace_match.group(0))
                except json.JSONDecodeError:
                    pass

            fallback["findings"] = f"Could not parse JSON from claude output: {output[:200]}"
            return fallback

    except subprocess.TimeoutExpired:
        fallback["findings"] = f"claude timed out after {timeout}s"
        return fallback
    except FileNotFoundError:
        fallback["findings"] = "claude CLI not found in PATH"
        return fallback
    except Exception as e:
        fallback["findings"] = f"Unexpected error: {e}"
        return fallback


# ---------------------------------------------------------------------------
# L1 Validator
# ---------------------------------------------------------------------------


class L1Validator:
    """L1 Functional validation: all CLI commands execute without errors."""

    def validate(self, project_name: str, project_cfg: dict[str, Any]) -> L1Result:
        project_path = expand_path(project_cfg["path"])
        result = L1Result(project_name=project_name)

        if not project_path.exists():
            print(f"  SKIP: {project_path} does not exist")
            return result

        print(f"  [L1] Validating {project_name} ({project_path.name})")

        # 1. init --yes
        cmd_result = run_codeindex_command(["init", "--yes"], cwd=project_path)
        self._record(result, cmd_result, "init --yes")

        # 2. scan-all --fallback (no AI, just structural)
        cmd_result = run_codeindex_command(
            ["scan-all", "--fallback"],
            cwd=project_path,
            timeout=TIMEOUT_SCAN_ALL,
        )
        self._record(result, cmd_result, "scan-all --fallback")

        # 3. status
        cmd_result = run_codeindex_command(["status"], cwd=project_path)
        self._record(result, cmd_result, "status")

        # 4. tech-debt on sample dir
        sample_dir = project_cfg.get("sample_dir", ".")
        cmd_result = run_codeindex_command(
            ["tech-debt", sample_dir],
            cwd=project_path,
        )
        self._record(result, cmd_result, f"tech-debt {sample_dir}")

        # 5. parse sample files
        for sample_file in project_cfg.get("sample_files", []):
            cmd_result = run_codeindex_command(
                ["parse", sample_file],
                cwd=project_path,
                timeout=TIMEOUT_PARSE,
            )
            self._record(result, cmd_result, f"parse {sample_file}")

        # 6. symbols
        cmd_result = run_codeindex_command(["symbols"], cwd=project_path, timeout=TIMEOUT_SCAN_ALL)
        self._record(result, cmd_result, "symbols")

        return result

    def _record(self, result: L1Result, cmd_result: CommandResult, label: str) -> None:
        result.commands.append(cmd_result)
        result.total_time += cmd_result.elapsed_seconds
        if cmd_result.exit_code == 0:
            result.passed += 1
            print(f"    PASS  {label} ({cmd_result.elapsed_seconds:.1f}s)")
        else:
            result.failed += 1
            snippet = cmd_result.stderr[:120] if cmd_result.stderr else "no stderr"
            print(f"    FAIL  {label} (exit={cmd_result.exit_code}) {snippet}")


# ---------------------------------------------------------------------------
# L2 Validator
# ---------------------------------------------------------------------------


class L2Validator:
    """L2 Quality validation: metrics collection + AI accuracy evaluation."""

    def __init__(self, claude_available: bool = False):
        self.claude_available = claude_available

    def validate(self, project_name: str, project_cfg: dict[str, Any]) -> L2Result:
        project_path = expand_path(project_cfg["path"])
        result = L2Result(project_name=project_name)

        if not project_path.exists():
            print(f"  SKIP: {project_path} does not exist")
            return result

        print(f"  [L2] Validating {project_name}")

        # Collect metrics
        result.metrics = self._collect_metrics(project_path, project_cfg)
        self._print_metrics(result.metrics)

        # Check thresholds
        thresholds = project_cfg.get("thresholds", {})
        self._check_thresholds(result, thresholds)

        # AI evaluations (if claude available)
        if self.claude_available:
            self._run_ai_evals(result, project_path, project_cfg)
        else:
            print("    SKIP  AI evaluations (claude not available)")

        return result

    def _collect_metrics(self, project_path: Path, project_cfg: dict[str, Any]) -> L2Metrics:
        metrics = L2Metrics()

        # Count README_AI.md files and sizes
        readme_files = list(project_path.rglob("README_AI.md"))
        metrics.readme_count = len(readme_files)
        metrics.readme_total_size_kb = sum(f.stat().st_size for f in readme_files) / 1024.0

        # Run scan-all --output json for parse stats
        cmd_result = run_codeindex_command(
            ["scan-all", "--output", "json"],
            cwd=project_path,
            timeout=TIMEOUT_SCAN_ALL,
        )
        if cmd_result.exit_code == 0 and cmd_result.stdout.strip():
            try:
                parse_data = json.loads(cmd_result.stdout)
                # Handle both formats: plain list or {"success":..., "results":[...]}
                if isinstance(parse_data, dict) and "results" in parse_data:
                    file_results = parse_data["results"]
                elif isinstance(parse_data, list):
                    file_results = parse_data
                else:
                    file_results = []
                if file_results:
                    total = len(file_results)
                    success = sum(1 for d in file_results if not d.get("error"))
                    symbols = sum(len(d.get("symbols", [])) for d in file_results)
                    errors = total - success
                    metrics.total_files_parsed = total
                    metrics.parse_success_rate = success / total if total > 0 else 0.0
                    metrics.total_symbols = symbols
                    metrics.total_errors = errors
            except json.JSONDecodeError:
                pass

        # Count routes from README_AI.md content (look for route tables)
        route_count = 0
        for readme in readme_files:
            try:
                content = readme.read_text(errors="replace")
                # Count lines that look like route table entries (| /path | ... |)
                route_count += len(re.findall(r"^\|\s*/\w+", content, re.MULTILINE))
            except OSError:
                pass
        metrics.route_count = route_count

        return metrics

    def _print_metrics(self, m: L2Metrics) -> None:
        print(f"    README_AI.md count:   {m.readme_count}")
        print(f"    README total size:    {m.readme_total_size_kb:.1f} KB")
        print(f"    Parse success rate:   {m.parse_success_rate:.1%}")
        print(f"    Total files parsed:   {m.total_files_parsed}")
        print(f"    Total symbols:        {m.total_symbols}")
        print(f"    Parse errors:         {m.total_errors}")
        print(f"    Route count:          {m.route_count}")

    def _check_thresholds(self, result: L2Result, thresholds: dict[str, Any]) -> None:
        m = result.metrics

        if "min_parse_success_rate" in thresholds:
            if m.parse_success_rate < thresholds["min_parse_success_rate"]:
                msg = (
                    f"Parse success rate {m.parse_success_rate:.1%} "
                    f"< threshold {thresholds['min_parse_success_rate']:.1%}"
                )
                result.threshold_failures.append(msg)
                print(f"    THRESHOLD FAIL: {msg}")

        if "min_symbol_count" in thresholds:
            if m.total_symbols < thresholds["min_symbol_count"]:
                msg = (
                    f"Symbol count {m.total_symbols} "
                    f"< threshold {thresholds['min_symbol_count']}"
                )
                result.threshold_failures.append(msg)
                print(f"    THRESHOLD FAIL: {msg}")

        if "min_readme_count" in thresholds:
            if m.readme_count < thresholds["min_readme_count"]:
                msg = (
                    f"README_AI.md count {m.readme_count} "
                    f"< threshold {thresholds['min_readme_count']}"
                )
                result.threshold_failures.append(msg)
                print(f"    THRESHOLD FAIL: {msg}")

    def _run_ai_evals(self, result: L2Result, project_path: Path, project_cfg: dict[str, Any]) -> None:
        # Eval 1: Architecture comprehension
        readme_root = project_path / "README_AI.md"
        if readme_root.exists():
            content = readme_root.read_text(errors="replace")[:8000]
            prompt = (
                "You are evaluating the quality of an AI-generated architecture document.\n\n"
                f"Here is the README_AI.md for a {project_cfg.get('language', 'unknown')} project "
                f"using {project_cfg.get('framework', 'no specific')} framework:\n\n"
                f"---\n{content}\n---\n\n"
                "Based on this document:\n"
                "1. Describe the project's architecture in 2-3 sentences\n"
                "2. Rate the document's quality for helping an AI agent understand the codebase (1-10)\n"
                "3. List any gaps or missing information\n\n"
                'RESPOND WITH ONLY VALID JSON: {"score": <1-10>, "architecture": "<description>", '
                '"findings": "<gaps or issues>", "answer": "<full assessment>"}'
            )
            print("    AI: Architecture comprehension...")
            ai_result = invoke_claude_eval(prompt)
            result.ai_evals.append(AIEvalResult(
                eval_name="architecture_comprehension",
                score=float(ai_result.get("score", 0)),
                findings=ai_result.get("findings", ""),
                raw_response=json.dumps(ai_result),
                success=float(ai_result.get("score", 0)) > 0,
            ))
            print(f"         Score: {ai_result.get('score', 0)}/10")

        # Eval 2: Symbol navigation
        symbols_file = project_path / "PROJECT_SYMBOLS.md"
        known_class = project_cfg.get("known_class", "")
        if symbols_file.exists() and known_class:
            sym_content = symbols_file.read_text(errors="replace")[:8000]
            prompt = (
                "You are evaluating a symbol index for AI code navigation.\n\n"
                f"Here is the PROJECT_SYMBOLS.md:\n\n---\n{sym_content}\n---\n\n"
                f"Task: Locate the class or symbol named '{known_class}'.\n"
                "1. Can you find it? In which file?\n"
                "2. Rate the index's usefulness for symbol navigation (1-10)\n"
                "3. List any issues with the index format\n\n"
                'RESPOND WITH ONLY VALID JSON: {"score": <1-10>, "found": <true/false>, '
                '"file_path": "<path if found>", "findings": "<issues>", "answer": "<assessment>"}'
            )
            print("    AI: Symbol navigation...")
            ai_result = invoke_claude_eval(prompt)
            result.ai_evals.append(AIEvalResult(
                eval_name="symbol_navigation",
                score=float(ai_result.get("score", 0)),
                findings=ai_result.get("findings", ""),
                raw_response=json.dumps(ai_result),
                success=ai_result.get("found", False),
            ))
            print(f"         Score: {ai_result.get('score', 0)}/10, Found: {ai_result.get('found', 'N/A')}")

        # Eval 3: Documentation accuracy
        sample_files = project_cfg.get("sample_files", [])
        if sample_files and readme_root.exists():
            sample_path = project_path / sample_files[0]
            if sample_path.exists():
                source_content = sample_path.read_text(errors="replace")[:4000]
                readme_content = readme_root.read_text(errors="replace")[:4000]
                prompt = (
                    "You are checking documentation accuracy.\n\n"
                    f"Source file ({sample_files[0]}):\n---\n{source_content}\n---\n\n"
                    f"README_AI.md excerpt:\n---\n{readme_content}\n---\n\n"
                    "Does the README_AI.md accurately describe the source file's content?\n"
                    "1. Rate accuracy (1-10)\n"
                    "2. List any inaccuracies or missing info\n\n"
                    'RESPOND WITH ONLY VALID JSON: {"score": <1-10>, '
                    '"findings": "<inaccuracies>", "answer": "<assessment>"}'
                )
                print("    AI: Documentation accuracy...")
                ai_result = invoke_claude_eval(prompt)
                result.ai_evals.append(AIEvalResult(
                    eval_name="documentation_accuracy",
                    score=float(ai_result.get("score", 0)),
                    findings=ai_result.get("findings", ""),
                    raw_response=json.dumps(ai_result),
                    success=float(ai_result.get("score", 0)) > 0,
                ))
                print(f"         Score: {ai_result.get('score', 0)}/10")


# ---------------------------------------------------------------------------
# L3 Validator
# ---------------------------------------------------------------------------


class L3Validator:
    """L3 Experience validation: flow continuity and instruction clarity."""

    def __init__(self, claude_available: bool = False):
        self.claude_available = claude_available

    def validate(self, project_name: str, project_cfg: dict[str, Any]) -> L3Result:
        project_path = expand_path(project_cfg["path"])
        result = L3Result(project_name=project_name)

        if not project_path.exists():
            print(f"  SKIP: {project_path} does not exist")
            return result

        if not self.claude_available:
            print(f"  [L3] SKIP {project_name} (claude not available)")
            return result

        print(f"  [L3] Validating {project_name}")

        # Eval 1: Onboarding flow
        claude_md = project_path / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(errors="replace")[:6000]
            prompt = (
                "You are an AI coding agent starting work on a new project.\n"
                "You have just been given the project's CLAUDE.md:\n\n"
                f"---\n{content}\n---\n\n"
                "Based on this document:\n"
                "1. What are your first 3 steps to understand this project?\n"
                "2. Rate the onboarding clarity (1-10)\n"
                "3. Is there anything missing or confusing?\n\n"
                'RESPOND WITH ONLY VALID JSON: {"score": <1-10>, "steps": ["<step1>", "<step2>", "<step3>"], '
                '"findings": "<missing or confusing items>", "answer": "<assessment>"}'
            )
            print("    AI: Onboarding flow...")
            ai_result = invoke_claude_eval(prompt)
            result.ai_evals.append(AIEvalResult(
                eval_name="onboarding_flow",
                score=float(ai_result.get("score", 0)),
                findings=ai_result.get("findings", ""),
                raw_response=json.dumps(ai_result),
                success=float(ai_result.get("score", 0)) >= 5,
            ))
            print(f"         Score: {ai_result.get('score', 0)}/10")

        # Eval 2: Step-by-step flow simulation
        readme_root = project_path / "README_AI.md"
        if readme_root.exists():
            readme_content = readme_root.read_text(errors="replace")[:4000]
            prompt = (
                "You are an AI agent. You've been asked to add a new feature to this project.\n"
                f"The project uses {project_cfg.get('language', 'unknown')} "
                f"with {project_cfg.get('framework', 'no specific')} framework.\n\n"
                "You have already run:\n"
                "  1. codeindex init --yes (created .codeindex.yaml)\n"
                "  2. codeindex scan-all --fallback (generated README_AI.md files)\n"
                "  3. codeindex status (shows indexing coverage)\n\n"
                f"Here is the project's README_AI.md:\n---\n{readme_content}\n---\n\n"
                "Now you need to understand the codebase to add a feature.\n"
                "1. Can you identify the right module to modify from the documentation?\n"
                "2. Rate the workflow continuity (1-10) — does each step logically lead to the next?\n"
                "3. Where does the flow break down (if anywhere)?\n\n"
                'RESPOND WITH ONLY VALID JSON: {"score": <1-10>, "can_identify_module": <true/false>, '
                '"findings": "<flow issues>", "answer": "<assessment>"}'
            )
            print("    AI: Step-by-step flow...")
            ai_result = invoke_claude_eval(prompt)
            result.ai_evals.append(AIEvalResult(
                eval_name="step_by_step_flow",
                score=float(ai_result.get("score", 0)),
                findings=ai_result.get("findings", ""),
                raw_response=json.dumps(ai_result),
                success=float(ai_result.get("score", 0)) >= 5,
            ))
            print(f"         Score: {ai_result.get('score', 0)}/10")

        # Eval 3: Ambiguity detection
        if claude_md.exists() and readme_root.exists():
            claude_content = claude_md.read_text(errors="replace")[:3000]
            readme_excerpt = readme_root.read_text(errors="replace")[:3000]
            prompt = (
                "You are reviewing project documentation for an AI coding agent.\n\n"
                f"CLAUDE.md excerpt:\n---\n{claude_content}\n---\n\n"
                f"README_AI.md excerpt:\n---\n{readme_excerpt}\n---\n\n"
                "Identify any unclear, ambiguous, or missing instructions that would "
                "confuse an AI agent trying to work on this project.\n"
                "1. List specific ambiguities\n"
                "2. Rate overall instruction clarity (1-10)\n"
                "3. Suggest improvements\n\n"
                'RESPOND WITH ONLY VALID JSON: {"score": <1-10>, "ambiguities": ["<issue1>", "<issue2>"], '
                '"findings": "<summary>", "answer": "<suggestions>"}'
            )
            print("    AI: Ambiguity detection...")
            ai_result = invoke_claude_eval(prompt)
            result.ai_evals.append(AIEvalResult(
                eval_name="ambiguity_detection",
                score=float(ai_result.get("score", 0)),
                findings=ai_result.get("findings", ""),
                raw_response=json.dumps(ai_result),
                success=float(ai_result.get("score", 0)) >= 5,
            ))
            print(f"         Score: {ai_result.get('score', 0)}/10")

        return result


# ---------------------------------------------------------------------------
# Baseline comparator
# ---------------------------------------------------------------------------


class BaselineComparator:
    """Compare current results against stored baselines for regression detection."""

    def __init__(self, baselines_dir: Path = BASELINES_DIR):
        self.baselines_dir = baselines_dir

    def get_latest_baseline(self) -> dict[str, Any] | None:
        """Load the most recent baseline file."""
        baselines = sorted(self.baselines_dir.glob("baseline_*.json"), reverse=True)
        if not baselines:
            return None
        with open(baselines[0]) as f:
            return json.load(f)

    def save_baseline(self, results: list[ProjectResult], version: str) -> Path:
        """Save current results as a new baseline."""
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_v{version}_{timestamp}.json"
        filepath = self.baselines_dir / filename

        data = {
            "version": version,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "projects": {r.project_name: r.to_dict() for r in results},
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\nBaseline saved: {filepath}")
        return filepath

    def compare(self, results: list[ProjectResult]) -> list[Regression]:
        """Compare current results against latest baseline."""
        baseline = self.get_latest_baseline()
        if baseline is None:
            print("\n  No baseline found — skipping regression check")
            return []

        print(f"\n  Comparing against baseline v{baseline.get('version', '?')} "
              f"({baseline.get('timestamp', '?')})")

        regressions: list[Regression] = []
        baseline_projects = baseline.get("projects", {})

        for result in results:
            bp = baseline_projects.get(result.project_name, {})
            if not bp:
                continue

            # L1: check for new failures
            if result.l1 and "l1" in bp:
                bl1 = bp["l1"]
                if result.l1.failed > bl1.get("failed", 0):
                    regressions.append(Regression(
                        project=result.project_name,
                        metric="l1_failures",
                        baseline_value=bl1.get("failed", 0),
                        current_value=result.l1.failed,
                        severity="REGRESSION",
                    ))

            # L2: check metrics
            if result.l2 and "l2" in bp:
                bm = bp["l2"].get("metrics", {})
                cm = result.l2.metrics

                # Parse success rate drop > 1%
                b_psr = bm.get("parse_success_rate", 0)
                if b_psr > 0 and cm.parse_success_rate < b_psr - 0.01:
                    regressions.append(Regression(
                        project=result.project_name,
                        metric="parse_success_rate",
                        baseline_value=b_psr,
                        current_value=cm.parse_success_rate,
                        severity="REGRESSION",
                    ))

                # Symbol count drop > 5%
                b_sym = bm.get("total_symbols", 0)
                if b_sym > 0 and cm.total_symbols < b_sym * 0.95:
                    regressions.append(Regression(
                        project=result.project_name,
                        metric="total_symbols",
                        baseline_value=b_sym,
                        current_value=cm.total_symbols,
                        severity="REGRESSION",
                    ))

                # AI score drops > 1.0
                b_evals = {e["eval_name"]: e for e in bp["l2"].get("ai_evals", [])}
                for eval_r in result.l2.ai_evals:
                    b_eval = b_evals.get(eval_r.eval_name)
                    if b_eval and eval_r.score < b_eval.get("score", 0) - 1.0:
                        regressions.append(Regression(
                            project=result.project_name,
                            metric=f"ai_{eval_r.eval_name}_score",
                            baseline_value=b_eval.get("score", 0),
                            current_value=eval_r.score,
                            severity="WARNING",
                        ))

        return regressions


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------


class ReportGenerator:
    """Generate markdown validation reports."""

    def generate(
        self,
        results: list[ProjectResult],
        regressions: list[Regression],
        version: str,
        layers: list[str],
    ) -> str:
        """Generate a markdown report string."""
        now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines: list[str] = []

        lines.append("# codeindex Validation Report")
        lines.append("")
        lines.append(f"**Version**: v{version}  ")
        lines.append(f"**Date**: {now}  ")
        lines.append(f"**Layers**: {', '.join(layers)}  ")
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Project | L1 | L2 | L3 |")
        lines.append("|---------|----|----|-----|")
        for r in results:
            l1_status = self._status_emoji(r.l1.success) if r.l1 else "-"
            l2_status = self._status_emoji(r.l2.success) if r.l2 else "-"
            l3_status = self._status_emoji(r.l3.success) if r.l3 else "-"
            lines.append(f"| {r.project_name} | {l1_status} | {l2_status} | {l3_status} |")
        lines.append("")

        # Regressions
        if regressions:
            lines.append("## Regressions Detected")
            lines.append("")
            for reg in regressions:
                lines.append(f"- **{reg.severity}** [{reg.project}] {reg.metric}: "
                             f"{reg.baseline_value} -> {reg.current_value}")
            lines.append("")

        # Per-project details
        for r in results:
            lines.append(f"## {r.project_name}")
            lines.append("")

            if r.l1:
                lines.append("### L1 Functional")
                lines.append("")
                lines.append(f"- Passed: {r.l1.passed}, Failed: {r.l1.failed}, "
                             f"Time: {r.l1.total_time:.1f}s")
                lines.append("")
                if r.l1.commands:
                    lines.append("| Command | Exit | Time | Status |")
                    lines.append("|---------|------|------|--------|")
                    for c in r.l1.commands:
                        status = "PASS" if c.exit_code == 0 else "FAIL"
                        lines.append(f"| `{c.command}` | {c.exit_code} | {c.elapsed_seconds:.1f}s | {status} |")
                    lines.append("")

            if r.l2:
                lines.append("### L2 Quality")
                lines.append("")
                m = r.l2.metrics
                lines.append(f"- README_AI.md count: {m.readme_count}")
                lines.append(f"- Parse success rate: {m.parse_success_rate:.1%}")
                lines.append(f"- Total symbols: {m.total_symbols}")
                lines.append(f"- Routes detected: {m.route_count}")
                lines.append("")

                if r.l2.threshold_failures:
                    lines.append("**Threshold failures:**")
                    for tf in r.l2.threshold_failures:
                        lines.append(f"- {tf}")
                    lines.append("")

                if r.l2.ai_evals:
                    lines.append("**AI Evaluations:**")
                    lines.append("")
                    for ev in r.l2.ai_evals:
                        lines.append(f"- **{ev.eval_name}**: {ev.score}/10")
                        if ev.findings:
                            lines.append(f"  - {ev.findings[:300]}")
                    lines.append("")

            if r.l3:
                lines.append("### L3 Experience")
                lines.append("")
                if r.l3.ai_evals:
                    for ev in r.l3.ai_evals:
                        lines.append(f"- **{ev.eval_name}**: {ev.score}/10")
                        if ev.findings:
                            lines.append(f"  - {ev.findings[:300]}")
                    lines.append("")

        return "\n".join(lines)

    def save_report(self, report: str, version: str) -> Path:
        """Save report to reports directory."""
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"validation_v{version}_{timestamp}.md"
        filepath = REPORTS_DIR / filename
        filepath.write_text(report)
        print(f"\nReport saved: {filepath}")
        return filepath

    def _status_emoji(self, success: bool) -> str:
        return "PASS" if success else "FAIL"


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate codeindex against real projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--layer",
        choices=["l1", "l2", "l3"],
        help="Run specific layer only (default: all)",
    )
    parser.add_argument(
        "--project",
        help="Run for specific project only (by name from projects.yaml)",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save results as new baseline for regression detection",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without executing",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip all AI evaluations (L1 metrics only for L2/L3)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Determine layers to run
    if args.layer:
        layers = [args.layer]
    else:
        layers = ["l1", "l2", "l3"]

    # Load project registry
    projects = load_projects_yaml()
    if args.project:
        if args.project not in projects:
            print(f"ERROR: Unknown project '{args.project}'. Available: {', '.join(projects.keys())}")
            return 2
        projects = {args.project: projects[args.project]}

    version = get_codeindex_version()

    # Check prerequisites
    print(f"=== codeindex Real Project Validation v{version} ===")
    print()
    ci_ok, claude_ok = check_prerequisites()
    if not ci_ok:
        print("ERROR: 'codeindex' not found in PATH")
        return 2
    print("  codeindex: OK")
    print(f"  claude:    {'OK' if claude_ok else 'NOT FOUND (AI evals will be skipped)'}")
    if args.no_ai:
        claude_ok = False
        print("  --no-ai:   AI evaluations disabled")
    print()

    # Dry run
    if args.dry_run:
        print("DRY RUN — would execute:")
        print(f"  Layers: {', '.join(layers)}")
        print("  Projects:")
        for name, cfg in projects.items():
            path = expand_path(cfg["path"])
            exists = "exists" if path.exists() else "NOT FOUND"
            print(f"    {name}: {path} ({exists})")
        print(f"  AI evaluations: {'yes' if claude_ok else 'no'}")
        print(f"  Save baseline: {'yes' if args.save_baseline else 'no'}")
        return 0

    # Run validations
    all_results: list[ProjectResult] = []

    for project_name, project_cfg in projects.items():
        print(f"\n--- {project_name} ---")
        pr = ProjectResult(project_name=project_name)

        if "l1" in layers:
            pr.l1 = L1Validator().validate(project_name, project_cfg)

        if "l2" in layers:
            pr.l2 = L2Validator(claude_available=claude_ok).validate(project_name, project_cfg)

        if "l3" in layers:
            pr.l3 = L3Validator(claude_available=claude_ok).validate(project_name, project_cfg)

        all_results.append(pr)

    # Regression detection
    comparator = BaselineComparator()
    regressions = comparator.compare(all_results)

    if regressions:
        print(f"\n{'='*50}")
        print(f"REGRESSIONS DETECTED: {len(regressions)}")
        for reg in regressions:
            print(f"  [{reg.severity}] {reg.project}/{reg.metric}: "
                  f"{reg.baseline_value} -> {reg.current_value}")

    # Save baseline if requested
    if args.save_baseline:
        comparator.save_baseline(all_results, version)

    # Generate report
    generator = ReportGenerator()
    report = generator.generate(all_results, regressions, version, layers)
    generator.save_report(report, version)

    # Print to stdout too
    print(f"\n{'='*50}")
    print(report)

    # Exit code
    has_failures = any(
        (r.l1 and not r.l1.success)
        or (r.l2 and not r.l2.success)
        for r in all_results
    )
    has_regressions = any(r.severity == "REGRESSION" for r in regressions)

    if has_failures or has_regressions:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
