"""AI invoker — external CLI (ADR-002) + direct HTTP API (ADR-008)."""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from codeindex.config import AIConfig

console = Console()

# GH #97: transient failure signals worth retrying within a single run. A
# `scan-all --ai` pass is serial, so a one-off haiku timeout / rate-limit
# otherwise loses that directory until a manual re-run. Matched case-insensitively
# against the InvokeResult.error text. Deliberately conservative — an unlabeled
# non-zero exit (e.g. bare "Exit code: 1") or a config error (command not found,
# exit 127) is NOT treated as transient, so a misconfigured ai_command fails fast
# instead of being retried N× across every directory.
_TRANSIENT_ERROR_PATTERNS = (
    "timed out",
    "timeout",
    "rate limit",
    "rate-limit",
    "ratelimit",
    "429",
    "overload",            # anthropic "overloaded_error"
    "502",
    "503",
    "529",
    "temporarily unavailable",
    "service unavailable",
    "connection reset",
    "connection error",
    "connection aborted",
    "econnreset",
)


# Default retry budget for scan paths (GH #97). 3 attempts = original + 2 retries,
# with exponential backoff, absorbs the common one-off jitter in a single run.
AI_SCAN_MAX_ATTEMPTS = 3


def _is_transient(error: str) -> bool:
    """Return True if an InvokeResult.error looks like a retryable transient failure.

    Conservative by design (GH #97): only recognised transient signals retry;
    everything else (config errors, unlabeled non-zero exits) fails fast.
    """
    if not error:
        return False
    low = error.lower()
    return any(p in low for p in _TRANSIENT_ERROR_PATTERNS)


def _retry_transient(
    attempt_fn,            # callable() -> InvokeResult
    max_attempts: int,
    retry_backoff: float,
) -> InvokeResult:
    """Run ``attempt_fn``, retrying recognised-transient failures (GH #97).

    Shared by the CLI path (``invoke_ai_cli``) and the HTTP API path
    (``invoke_ai_api``, ADR-008). Retries only transient signals
    (timeout/rate-limit/5xx/connection); refusals (success=True) and
    permanent errors (auth/quota/404) fail fast. Backoff: attempt N sleeps
    ``retry_backoff * 2**(N-1)`` (0 disables sleeping, used in tests).
    """
    attempts = max(1, max_attempts)
    result = attempt_fn()
    attempt = 1
    while (
        not result.success
        and attempt < attempts
        and _is_transient(result.error)
    ):
        time.sleep(retry_backoff * (2 ** (attempt - 1)))
        result = attempt_fn()
        attempt += 1
    return result


def clean_ai_output(output: str) -> str:
    """
    Clean AI output to extract valid markdown content.

    Handles cases where AI includes explanations before/after markdown.
    """
    if not output or not output.strip():
        return ""

    lines = output.strip().split("\n")

    # Find the first markdown heading
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            start_idx = i
            break

    # Extract from first heading onwards
    cleaned = "\n".join(lines[start_idx:])

    # Remove any trailing non-markdown content (common AI commentary)
    # Look for patterns like "---" followed by explanations
    final_lines = []
    in_code_block = False
    for line in cleaned.split("\n"):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
        # Skip lines that look like AI commentary (not in code block)
        if not in_code_block and line.strip().startswith(("Note:", "I ", "This ")):
            if not any(
                line.strip().startswith(f"- {x}") for x in ["Note:", "I ", "This "]
            ):
                continue
        final_lines.append(line)

    return "\n".join(final_lines).strip()


def validate_markdown_output(output: str) -> bool:
    """Check if output looks like valid README markdown."""
    if not output or len(output) < 50:
        return False
    # Must start with a heading
    first_line = output.strip().split("\n")[0]
    if not first_line.startswith("#"):
        return False
    # Should have some structure
    if output.count("#") < 2:
        return False
    return True


@dataclass
class InvokeResult:
    """Result of invoking AI CLI."""

    success: bool
    output: str
    error: str = ""
    command: str = ""


def format_prompt(
    dir_path: Path,
    files_info: str,
    symbols_info: str,
    imports_info: str,
) -> str:
    """
    Format the prompt to send to AI CLI.

    Uses Markdown format for readability.
    """
    dir_name = dir_path.name
    prompt = f"""CRITICAL: Output ONLY valid markdown. No explanations.
Start with: # README_AI.md - {dir_name}

## Directory
{dir_path}

## Files
{files_info}

## Symbols (Classes, Functions)
{symbols_info}

## Imports/Dependencies
{imports_info}

## Task
Generate a README_AI.md for this module. Include:
1. Purpose - what this module does (1-2 sentences)
2. Architecture - key components and data flow
3. Key Components - classes/functions with roles
4. Consumes - dependencies on other modules
5. Provides - exports for other modules

Requirements:
- Start with: # README_AI.md - {dir_name}
- Use markdown tables for Consumes/Provides
- Focus on WHAT and WHY, not HOW
- Keep it concise (~50-100 lines)
- Output ONLY markdown, no commentary
"""
    return prompt


def _invoke_once(command: str, timeout: int) -> InvokeResult:
    """Run the AI CLI command exactly once."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return InvokeResult(
                success=True,
                output=result.stdout,
                command=command,
            )
        else:
            return InvokeResult(
                success=False,
                output=result.stdout,
                error=result.stderr or f"Exit code: {result.returncode}",
                command=command,
            )

    except subprocess.TimeoutExpired:
        return InvokeResult(
            success=False,
            output="",
            error=f"Command timed out after {timeout} seconds",
            command=command,
        )
    except Exception as e:
        return InvokeResult(
            success=False,
            output="",
            error=str(e),
            command=command,
        )


def invoke_ai_cli(
    command_template: str,
    prompt: str,
    timeout: int = 120,
    dry_run: bool = False,
    max_attempts: int = 1,
    retry_backoff: float = 2.0,
) -> InvokeResult:
    """
    Invoke the AI CLI with the given prompt.

    Args:
        command_template: Command template with {prompt} placeholder
        prompt: The prompt to send
        timeout: Timeout in seconds
        dry_run: If True, just print the command without executing
        max_attempts: Max total attempts. >1 retries transient failures
            (timeout / rate-limit / 5xx) with exponential backoff (GH #97).
            Default 1 preserves single-shot behavior for all existing callers.
        retry_backoff: Base seconds for backoff; attempt N sleeps
            ``retry_backoff * 2**N`` (0 disables sleeping, used in tests).

    Returns:
        InvokeResult with output or error
    """
    # Escape the prompt for shell
    escaped_prompt = prompt.replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")

    # Build the command
    command = command_template.replace("{prompt}", escaped_prompt)

    if dry_run:
        console.print("[dim]Would execute:[/dim]")
        console.print(f"[cyan]{command[:200]}...[/cyan]")
        return InvokeResult(
            success=True,
            output="[DRY RUN] No actual execution",
            command=command,
        )

    return _retry_transient(
        lambda: _invoke_once(command, timeout),
        max_attempts,
        retry_backoff,
    )


def invoke_ai_api(
    ai_cfg: AIConfig,
    prompt: str,
    timeout: int | None = None,
    max_attempts: int = 1,
    retry_backoff: float = 2.0,
) -> InvokeResult:
    """POST ``prompt`` to an OpenAI-compatible ``/chat/completions`` endpoint.

    Reuses the GH-97 transient-retry framework via ``_retry_transient``:
    error strings are phrased to match ``_TRANSIENT_ERROR_PATTERNS`` so
    429/5xx/timeout/connection retry identically to the CLI path.
    401/402/403 (auth/quota) are NOT transient → fail fast (avoid hammering
    on a bad key). httpx is imported lazily so non-AI users pay no import
    cost. ADR-008.
    """
    import httpx

    url = ai_cfg.base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {ai_cfg.resolved_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": ai_cfg.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": ai_cfg.max_tokens,
        "stream": False,
    }
    effective_timeout = timeout if timeout is not None else ai_cfg.timeout

    def _once() -> InvokeResult:
        try:
            with httpx.Client(timeout=effective_timeout) as client:
                resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return InvokeResult(success=True, output=content, command=f"POST {url}")
            # Non-2xx → error string shaped to match _TRANSIENT_ERROR_PATTERNS
            # ("HTTP 429:..." / "HTTP 503:..." retry; "HTTP 401:..." fail fast).
            return InvokeResult(
                success=False,
                output="",
                error=f"HTTP {resp.status_code}: {resp.text[:300]}",
                command=f"POST {url}",
            )
        except httpx.TimeoutException as e:
            return InvokeResult(
                success=False, output="", error=f"timed out: {e}", command=f"POST {url}"
            )
        except httpx.HTTPError as e:  # ConnectError, RemoteProtocolError, etc.
            return InvokeResult(
                success=False,
                output="",
                error=f"connection error: {e}",
                command=f"POST {url}",
            )

    return _retry_transient(_once, max_attempts, retry_backoff)


def resolve_ai_backend(config) -> tuple[str, object]:
    """Decide which AI backend a call site should use (ADR-008).

    Precedence: ``ai_command`` (CLI escape hatch) wins if set; else
    ``ai.api_key`` (direct HTTP API); else ``("none", "")`` so the caller
    surfaces a clear configure-it message.

    Returns ``(kind, value)``: ``("cli", command_template)`` |
    ``("api", AIConfig)`` | ``("none", "")``.
    """
    if config.ai_command:
        return ("cli", config.ai_command)
    if config.ai and config.ai.resolved_api_key:
        return ("api", config.ai)
    return ("none", "")


def invoke_ai(
    config,
    prompt: str,
    *,
    timeout: int = 120,
    max_attempts: int = 1,
    retry_backoff: float = 2.0,
    dry_run: bool = False,
) -> InvokeResult:
    """Single entry: resolve backend from ``config`` and dispatch.

    Prefer this over ``invoke_ai_cli(config.ai_command, ...)`` at call sites
    so the ``ai:`` section (DeepSeek API, ADR-008) is the default and
    ``ai_command`` is the escape hatch. See ``resolve_ai_backend``.
    """
    backend, value = resolve_ai_backend(config)
    if backend == "cli":
        return invoke_ai_cli(
            value, prompt, timeout=timeout, dry_run=dry_run,
            max_attempts=max_attempts, retry_backoff=retry_backoff,
        )
    if backend == "api":
        if dry_run:
            return InvokeResult(
                success=True,
                output="[DRY RUN]",
                command=f"POST {value.base_url}/chat/completions",
            )
        return invoke_ai_api(
            value, prompt, timeout=timeout,
            max_attempts=max_attempts, retry_backoff=retry_backoff,
        )
    # ("none", "")
    return InvokeResult(
        success=False,
        output="",
        command="",
        error="No AI backend configured. Set the CODEINDEX_AI_API_KEY env var, "
              "add an `ai:` section to .codeindex.yaml, or set ai_command "
              "(CLI escape hatch). See ADR-008.",
    )


def invoke_ai_cli_stdin(
    command: str,
    prompt: str,
    timeout: int = 120,
    dry_run: bool = False,
) -> InvokeResult:
    """
    Alternative: invoke AI CLI with prompt via stdin.

    Some CLI tools prefer stdin input for long prompts.

    Args:
        command: Command to run (without prompt)
        prompt: The prompt to send via stdin
        timeout: Timeout in seconds
        dry_run: If True, just print the command without executing

    Returns:
        InvokeResult with output or error
    """
    if dry_run:
        console.print("[dim]Would execute:[/dim]")
        console.print(f"[cyan]{command}[/cyan]")
        console.print(f"[dim]With stdin prompt ({len(prompt)} chars)[/dim]")
        return InvokeResult(
            success=True,
            output="[DRY RUN] No actual execution",
            command=command,
        )

    try:
        result = subprocess.run(
            shlex.split(command),
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return InvokeResult(
                success=True,
                output=result.stdout,
                command=command,
            )
        else:
            return InvokeResult(
                success=False,
                output=result.stdout,
                error=result.stderr or f"Exit code: {result.returncode}",
                command=command,
            )

    except subprocess.TimeoutExpired:
        return InvokeResult(
            success=False,
            output="",
            error=f"Command timed out after {timeout} seconds",
            command=command,
        )
    except Exception as e:
        return InvokeResult(
            success=False,
            output="",
            error=str(e),
            command=command,
        )
