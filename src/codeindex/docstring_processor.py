"""Docstring Processor - AI-powered documentation extraction.

Story 9.1: Docstring Processor Core

This module provides AI-powered docstring extraction and normalization
for any programming language, following the KISS principle (no complex parsers).

Modes:
- hybrid: Simple extraction + selective AI (cost-effective, <$1 per 250 dirs)
- all-ai: AI processes everything (highest quality, higher cost)

Architecture:
- Batch processing: 1 AI call per file (not per comment)
- Fallback strategy: Graceful degradation if AI fails
- Cost tracking: Token counting for budget management
"""

import json
import re
import subprocess
from pathlib import Path

from .parser import Symbol


class DocstringProcessor:
    """AI-powered docstring extraction and normalization.

    Uses external AI CLI (Claude, GPT-4, etc.) to understand and normalize
    documentation comments from any format:
    - PHPDoc (/** @param */)
    - JavaDoc (/** ... */)
    - JSDoc (/** ... */)
    - Inline comments (// ...)
    - Mixed language (Chinese + English)
    - Irregular formats

    Attributes:
        ai_command: AI CLI command template with {prompt} placeholder
        mode: Processing mode ("hybrid" or "all-ai")
        total_tokens: Total tokens processed (for cost tracking)
    """

    def __init__(self, ai_command: str, mode: str = "hybrid"):
        """
        Initialize docstring processor.

        Args:
            ai_command: AI CLI command template (e.g., 'claude -p "{prompt}"')
            mode: Processing mode - "hybrid" (default) or "all-ai"
        """
        if mode not in ("hybrid", "all-ai"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'hybrid' or 'all-ai'")

        self.ai_command = ai_command
        self.mode = mode
        self.total_tokens = 0

    def process_file(
        self, file_path: Path, symbols: list[Symbol]
    ) -> dict[str, str]:
        """
        Process all docstrings in a file.

        Batch processing: Makes single AI call for all symbols in the file
        (not per symbol).

        Args:
            file_path: Path to source file
            symbols: List of symbols with raw docstrings

        Returns:
            Dict mapping symbol name to normalized description
        """
        if not symbols:
            return {}

        # Filter symbols that need processing
        symbols_to_process = [
            s for s in symbols if self._should_process(s.docstring)
        ]

        if not symbols_to_process:
            return {}

        # Decide whether to use AI
        if self.mode == "all-ai":
            # All-AI mode: always use AI
            return self._process_with_ai(file_path, symbols_to_process, symbols)

        # Hybrid mode: selective AI usage
        needs_ai = any(self._should_use_ai(s.docstring) for s in symbols_to_process)

        if needs_ai:
            return self._process_with_ai(file_path, symbols_to_process, symbols)

        # Simple extraction without AI
        return self._process_simple(symbols_to_process)

    def _should_process(self, docstring: str) -> bool:
        """Check if docstring should be processed."""
        return bool(docstring and docstring.strip())

    def _should_use_ai(self, docstring: str) -> bool:
        """
        Decide if AI is needed for this docstring.

        Hybrid mode uses AI only when necessary:
        - Simple cases: NO AI (fast, free)
        - Complex cases: YES AI (accurate, costs tokens)

        Args:
            docstring: Raw docstring text

        Returns:
            True if AI is needed
        """
        if not docstring or len(docstring.strip()) == 0:
            return False

        # Check for structured documentation markers
        structured_markers = ["@param", "@return", "@throws", "@var", "/**", "*/"]
        if any(marker in docstring for marker in structured_markers):
            return True  # Structured doc → AI

        # Simple case: Clean one-liner in English (<= 60 chars, no newlines)
        if len(docstring) <= 60 and "\n" not in docstring:
            # Check if contains non-ASCII (Chinese, etc.)
            if not self._contains_non_ascii(docstring):
                return False  # Simple English → No AI

        # Complex cases that need AI:
        # - Mixed language (Chinese + English)
        # - Multi-line with structure (@param, @return)
        # - Irregular formatting
        # - Very long (>60 chars)
        return True

    def _contains_non_ascii(self, text: str) -> bool:
        """Check if text contains non-ASCII characters."""
        return any(ord(c) > 127 for c in text)

    def _process_simple(self, symbols: list[Symbol]) -> dict[str, str]:
        """
        Process docstrings without AI (simple extraction).

        Args:
            symbols: Symbols to process

        Returns:
            Dict mapping symbol name to description
        """
        result = {}
        for symbol in symbols:
            if symbol.docstring:
                result[symbol.name] = self._fallback_extract(symbol.docstring)
        return result

    def _process_with_ai(
        self,
        file_path: Path,
        symbols_to_process: list[Symbol],
        all_symbols: list[Symbol],
    ) -> dict[str, str]:
        """
        Process docstrings with AI (batch processing).

        Args:
            file_path: Source file path
            symbols_to_process: Symbols that need processing
            all_symbols: All symbols (for context)

        Returns:
            Dict mapping symbol name to normalized description
        """
        # Generate prompt
        prompt = self._generate_prompt(file_path, symbols_to_process)

        # Call AI
        try:
            ai_result = self._call_ai(prompt)

            # Parse JSON response
            parsed = self._parse_ai_response(ai_result)

            # Update token count (estimate)
            self.total_tokens += len(prompt) // 4 + len(ai_result) // 4

            return parsed

        except Exception:
            # Fallback on AI failure
            return self._process_simple(symbols_to_process)

    def _generate_prompt(self, file_path: Path, symbols: list[Symbol]) -> str:
        """
        Generate AI prompt for batch processing.

        Args:
            file_path: Source file path
            symbols: Symbols to process

        Returns:
            Prompt string
        """
        symbols_list = "\n".join(
            (
                f"- {s.name} ({s.kind}): {s.docstring[:100]}..."
                if len(s.docstring) > 100
                else f"- {s.name} ({s.kind}): {s.docstring}"
            )
            for s in symbols
        )

        prompt = f"""You are analyzing source code documentation comments.

Extract and normalize docstrings for the following symbols:

File: {file_path}

Symbols:
{symbols_list}

For each symbol, generate a concise description (max 60 characters):
1. Use imperative mood ("Get user list", not "Gets user list")
2. Focus on WHAT the code does, not HOW
3. Combine information from all comment types (PHPDoc, inline, etc.)
4. Handle mixed languages (prefer English if available)
5. Remove noise (@param, @return, TODO, etc.)

Return JSON format:
{{
  "symbols": [
    {{
      "name": "methodName",
      "description": "Concise description here",
      "quality": "high|medium|low"
    }}
  ]
}}

If a symbol has no meaningful documentation, omit it from the response."""

        return prompt

    def _call_ai(self, prompt: str) -> str:
        """
        Call AI CLI and get response.

        Args:
            prompt: Prompt to send

        Returns:
            AI response text

        Raises:
            Exception: If AI call fails
        """
        # Replace {prompt} placeholder in command
        command = self.ai_command.replace("{prompt}", prompt)

        # Execute AI CLI
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise Exception(f"AI CLI failed: {result.stderr}")

        return result.stdout

    def _parse_ai_response(self, response: str) -> dict[str, str]:
        """
        Parse AI JSON response.

        Args:
            response: AI response text

        Returns:
            Dict mapping symbol name to description

        Raises:
            Exception: If JSON parsing fails
        """
        try:
            data = json.loads(response)
            symbols = data.get("symbols", [])

            result = {}
            for symbol in symbols:
                name = symbol.get("name")
                description = symbol.get("description")
                if name and description:
                    result[name] = description

            return result

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI JSON response: {e}")

    def _fallback_extract(self, docstring: str) -> str:
        """
        Simple fallback: extract first line, max 60 chars.

        Args:
            docstring: Raw docstring text

        Returns:
            Cleaned description (max 60 chars + "...")
        """
        if not docstring:
            return ""

        # Clean up docstring
        cleaned = docstring.strip()

        # Remove comment markers
        cleaned = re.sub(r"^/\*\*\s*", "", cleaned)  # /** at start
        cleaned = re.sub(r"\s*\*/$", "", cleaned)  # */ at end
        cleaned = re.sub(r"^\s*\*\s*", "", cleaned, flags=re.MULTILINE)  # * lines
        cleaned = re.sub(r"^//\s*", "", cleaned)  # // comments
        cleaned = re.sub(r"^#\s*", "", cleaned)  # # comments

        # Take first line
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        if not lines:
            return ""

        first_line = lines[0]

        # Remove @tags
        first_line = re.sub(r"@\w+.*", "", first_line).strip()

        # Truncate if too long
        if len(first_line) > 60:
            return first_line[:60] + "..."

        return first_line
