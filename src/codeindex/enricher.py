"""AI enrichment module for generating one-line module descriptions.

Epic 25: Instead of AI generating entire README_AI.md files, AI only
produces a short functional description (~30 chars) per module.
This is injected as a blockquote line after the title in README_AI.md.

Cost: ~300-800 tokens input, ~20-50 tokens output per directory.
"""

import re
from pathlib import Path

from .parser import ParseResult

# Maximum symbol names to include per file in the prompt
_MAX_SYMBOLS_PER_FILE = 5

# Maximum total files to include in the prompt
_MAX_FILES = 15

# Refusal prefixes used to detect AI responses that decline to summarise the
# directory (typically because the prompt context was thin enough that the
# model can't say anything specific). When the model returns "I don't see any
# file names..." we must NOT stamp `enrichment: ok` — that poisons the cache
# permanently (GH #85). Instead the response is treated as a failure with
# reason "ai-refused" so the next `scan-all --ai` retries automatically.
#
# Matched against the lowercased, stripped response. Keep prefixes short so
# the check is robust to upstream truncation (the cli_scan path truncates
# enrichment output to ~80 chars; refusal phrasing is always in the first 30).
_REFUSAL_PREFIXES = (
    "i don't",
    "i do not",
    "i cannot",
    "i can't",
    "i'm unable",
    "i am unable",
    "i need more",
    "no file",
    "insufficient context",
    "without more",
    "sorry, i",
    "as an ai",
)


def looks_like_refusal(text: str) -> bool:
    """Return True if the cleaned AI response looks like a refusal / inability.

    Used by ``scan-all --ai`` Phase 2 to distinguish a usable one-line
    description from boilerplate refusal text. The refusal text is never
    project-information and stamping it with ``<!-- enrichment: ok -->``
    pins it in the cache; the next run sees the marker and skips
    re-enrichment, so the garbage description sticks indefinitely (GH #85).
    """
    t = (text or "").strip().lower()
    if not t:
        return False
    return any(t.startswith(p) for p in _REFUSAL_PREFIXES)


def extract_symbol_summary(parse_results: list[ParseResult]) -> str:
    """Extract a compact summary of file names + symbol names for AI prompt.

    Uses short names (no class:: prefix) to keep prompt compact.

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
        # Use short names: "MyClass::method" → "method", "MyClass" stays
        symbol_names = []
        for s in result.symbols[:_MAX_SYMBOLS_PER_FILE]:
            short = s.name.split("::")[-1].split(".")[-1]
            symbol_names.append(short)
        if symbol_names:
            parts.append(f"{filename}: {', '.join(symbol_names)}")
        else:
            parts.append(filename)

    return "; ".join(parts)


def extract_summary_from_readme(readme_path: Path) -> str:
    """Extract a compact summary from an existing README_AI.md.

    Reads the file listing and subdirectory names from a structural
    README_AI.md to build a summary for the AI prompt. This avoids
    re-scanning the directory when Phase 1 already generated the README.

    Args:
        readme_path: Path to an existing README_AI.md

    Returns:
        Compact summary string, or empty string if unreadable
    """
    if not readme_path.exists():
        return ""

    try:
        content = readme_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

    parts = []

    # Extract subdirectory names
    for m in re.finditer(r'\*\*(\w[\w/]*)/\*\*\s*-\s*(.+?)$', content, re.MULTILINE):
        dir_name = m.group(1)
        desc = m.group(2).strip()
        # Skip stats-only descriptions like "48 files | 386 symbols"
        if re.match(r'^\d+ files', desc):
            parts.append(dir_name)
        else:
            parts.append(f"{dir_name}: {desc[:60]}")

    # Extract file names with their key symbols
    for m in re.finditer(r'\*\*(\w[\w.]*\.[\w.]+)\*\*\s*-\s*(\w[\w, ]*)', content, re.MULTILINE):
        filename = m.group(1)
        symbols = m.group(2).strip()
        parts.append(f"{filename}: {symbols[:50]}")

    if len(parts) > 20:
        parts = parts[:20]

    return "; ".join(parts)


_MAX_SAFE_CONTEXT_DIRS = 20


def build_safe_subdir_context(child_dirs: list[Path]) -> str:
    """Build prompt context from directory names only — no free text.

    Used as the preferred input for AI enrichment of overview/navigation
    directories. Avoids the injection chain where README markdown contains
    AI-generated descriptions sourced from arbitrary docstrings, which
    `extract_summary_from_readme()` then regex-extracts and feeds into the
    next enrichment prompt.

    Args:
        child_dirs: Indexed child directories (e.g. from DirectoryTree.get_children)

    Returns:
        Compact string of bare directory names, e.g. "Pay, Vip, User"
        Returns empty string if no children.
    """
    if not child_dirs:
        return ""

    names = [d.name for d in child_dirs[:_MAX_SAFE_CONTEXT_DIRS]]
    suffix = ""
    if len(child_dirs) > _MAX_SAFE_CONTEXT_DIRS:
        suffix = f" ... and {len(child_dirs) - _MAX_SAFE_CONTEXT_DIRS} more"
    return "Subdirectories: " + ", ".join(names) + suffix


def build_enrich_prompt(
    dir_name: str,
    symbol_summary: str,
    parent_name: str = "",
) -> str:
    """Build a minimal prompt for AI to generate a one-line module description.

    Args:
        dir_name: Directory name (e.g., "SmallProgramApi")
        symbol_summary: Output of extract_symbol_summary() or extract_summary_from_readme()
        parent_name: Parent directory name for context (e.g., "Application")

    Returns:
        Prompt string for AI CLI
    """
    context = f"Directory: {dir_name}\n"
    if parent_name:
        context += f"Parent: {parent_name}\n"
    context += f"Contents: {symbol_summary}\n"

    return (
        context
        + "\n"
        "Based ONLY on the file names and symbol names above, write a concise "
        "functional description of this module (30 chars or less). "
        "Describe WHAT it does, not HOW. "
        "Examples: '会员等级、积分、权益卡管理', 'Payment gateway (Alipay/WeChat)', "
        "'物流配送与运费计算'. "
        "Output ONLY the description text. No quotes, no markdown, no explanation. "
        "Do NOT invent features not evidenced by the symbol names."
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


def extract_blockquote_description(readme_path: Path) -> str | None:
    """Return the `> description` line that was injected after the title.

    Lets Phase 2 cache the previously-AI-generated description before
    Phase 1 rewrites the structural README (which would otherwise wipe
    the blockquote), so on re-run the cached description is re-injected
    without a fresh AI call.

    Only looks at the first non-empty line directly after the first `# `
    title — body-level `>` lines are ignored.

    Args:
        readme_path: Path to README_AI.md

    Returns:
        The description text (without leading `> ` and outer whitespace),
        or None if the file is missing or has no blockquote in the title region.
    """
    if not readme_path.exists():
        return None
    try:
        content = readme_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    lines = content.split("\n")
    title_idx = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title_idx = i
            break
    if title_idx is None:
        return None

    # Scan forward from title for the first non-empty line
    for j in range(title_idx + 1, len(lines)):
        candidate = lines[j].strip()
        if not candidate:
            continue
        if candidate.startswith(">"):
            return candidate.lstrip(">").strip() or None
        return None  # first non-empty line wasn't a blockquote
    return None


def has_successful_enrichment(readme_path: Path) -> bool:
    """Return True if README already has `<!-- enrichment: ok -->` marker.

    Lets `scan-all --ai` skip already-enriched dirs on re-run, making
    retry-after-transient-failure idempotent and cost-free for successes.

    Args:
        readme_path: Path to README_AI.md

    Returns:
        True iff the file exists AND contains the literal ok marker.
        False for missing files, failed-marker files, or no-marker files.
    """
    if not readme_path.exists():
        return False
    try:
        content = readme_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return "<!-- enrichment: ok -->" in content


def mark_enrichment_status(readme_path: Path, status: str, reason: str = "") -> None:
    """Record AI enrichment outcome as an HTML comment in README_AI.md.

    Lets AI consumers distinguish "structural-only by config" (no marker)
    from "AI enrichment attempted":
        <!-- enrichment: ok -->
        <!-- enrichment: failed (reason: Command timed out after 120 seconds) -->

    Sits immediately under the `<!-- Generated by codeindex ... -->` header.
    Replaces any existing `<!-- enrichment: ... -->` line.

    Args:
        readme_path: Path to README_AI.md file
        status: "ok" or "failed"
        reason: Optional one-line reason (collapsed if multi-line)
    """
    if reason:
        single_line = " ".join(reason.split())  # collapse whitespace and newlines
        marker = f"<!-- enrichment: {status} (reason: {single_line}) -->"
    else:
        marker = f"<!-- enrichment: {status} -->"

    content = readme_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    # Remove any existing enrichment marker
    lines = [line for line in lines if not line.startswith("<!-- enrichment:")]

    # Find Generated header line
    generated_idx = None
    for i, line in enumerate(lines):
        if line.startswith("<!-- Generated by codeindex"):
            generated_idx = i
            break

    if generated_idx is not None:
        lines.insert(generated_idx + 1, marker)
    else:
        lines.insert(0, marker)

    readme_path.write_text("\n".join(lines), encoding="utf-8")
