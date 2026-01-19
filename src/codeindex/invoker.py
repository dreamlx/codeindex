"""AI CLI invoker - calls external AI CLI tools."""

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console()


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


def invoke_ai_cli(
    command_template: str,
    prompt: str,
    timeout: int = 120,
    dry_run: bool = False,
) -> InvokeResult:
    """
    Invoke the AI CLI with the given prompt.

    Args:
        command_template: Command template with {prompt} placeholder
        prompt: The prompt to send
        timeout: Timeout in seconds
        dry_run: If True, just print the command without executing

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

    try:
        # Run the command
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
