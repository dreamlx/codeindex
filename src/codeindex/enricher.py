"""AI enrichment module for generating one-line module descriptions.

Epic 25: Instead of AI generating entire README_AI.md files, AI only
produces a short functional description (~20 chars) per module.
This is injected as a blockquote line after the title in README_AI.md.

Cost: ~200-400 tokens input, ~20-50 tokens output per directory.
"""

from pathlib import Path

from .parser import ParseResult

# Maximum symbol names to include per file in the prompt
_MAX_SYMBOLS_PER_FILE = 10

# Maximum total files to include in the prompt
_MAX_FILES = 15


def extract_symbol_summary(parse_results: list[ParseResult]) -> str:
    """Extract a compact summary of file names + symbol names for AI prompt.

    Args:
        parse_results: Parsed file results for a directory

    Returns:
        Compact string like "ImageController.php: uploadAvatar, login; User.php: getUserInfo"
    """
    if not parse_results:
        return ""

    parts = []
    for result in parse_results[:_MAX_FILES]:
        if result.error:
            continue
        filename = result.path.name
        symbol_names = [
            s.name for s in result.symbols[:_MAX_SYMBOLS_PER_FILE]
        ]
        if symbol_names:
            parts.append(f"{filename}: {', '.join(symbol_names)}")
        else:
            parts.append(filename)

    return "; ".join(parts)


def build_enrich_prompt(dir_name: str, symbol_summary: str) -> str:
    """Build a minimal prompt for AI to generate a one-line module description.

    Args:
        dir_name: Directory name (e.g., "SmallProgramApi")
        symbol_summary: Output of extract_symbol_summary()

    Returns:
        Prompt string for AI CLI
    """
    return (
        f"Directory: {dir_name}\n"
        f"Contents: {symbol_summary}\n"
        "\n"
        "Based on the file names and symbol names above, write a brief functional "
        "description of this module in 20 characters or less. "
        "Describe WHAT it does (e.g., '会员等级管理、积分兑换' or 'Payment gateway integration'). "
        "Output ONLY the description, nothing else. No quotes, no markdown, no explanation."
    )


def inject_blockquote(readme_path: Path, description: str) -> None:
    """Inject or replace a blockquote description line in README_AI.md.

    Inserts `> description` after the first `# Title` line.
    If a blockquote already exists after the title, it is replaced.

    Args:
        readme_path: Path to README_AI.md file
        description: The one-line description to inject
    """
    content = readme_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    # Find the title line (first line starting with "# ")
    title_idx = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title_idx = i
            break

    if title_idx is None:
        # No title found — prepend blockquote at top
        lines.insert(0, f"> {description}")
        readme_path.write_text("\n".join(lines), encoding="utf-8")
        return

    # Check if next non-empty line is already a blockquote
    next_content_idx = title_idx + 1
    while next_content_idx < len(lines) and lines[next_content_idx].strip() == "":
        next_content_idx += 1

    if next_content_idx < len(lines) and lines[next_content_idx].startswith(">"):
        # Replace existing blockquote
        lines[next_content_idx] = f"> {description}"
    else:
        # Insert after title
        lines.insert(title_idx + 1, f"> {description}")

    readme_path.write_text("\n".join(lines), encoding="utf-8")


def should_enrich(level: str) -> bool:
    """Determine if a directory at this level should get AI enrichment.

    Only overview and navigation levels benefit from AI descriptions.
    Detailed (leaf) levels have enough symbol information already.

    Args:
        level: One of "overview", "navigation", "detailed"
    """
    return level in ("overview", "navigation")
