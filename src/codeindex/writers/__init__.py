"""Smart README writer package with focused generator classes.

Provides level-specific README generation:
- OverviewGenerator: Project/root level documentation
- NavigationGenerator: Module level documentation
- DetailedGenerator: Leaf level detailed documentation
- SmartWriter: Facade that dispatches to generators
"""

from .core import LevelType, SmartWriter, WriteResult, determine_level

# Navigation-contract disclaimer prepended to every generated README_AI.md.
# Agents read raw markdown and see this comment; human renderers ignore it.
# See docs/architecture/design-philosophy.md for the rationale (codeindex
# READMEs are a navigation index, not authoritative source). The benchmark
# evidence is in commit 1e1a754 + memory project_codeindex_navigation_not_tech_doc.
NAVIGATION_DISCLAIMER = (
    "<!-- codeindex navigation index — agent: drill into source via "
    "Read/Grep for precise mechanism; do not treat this as final word. -->"
)

__all__ = [
    "SmartWriter", "WriteResult", "LevelType", "determine_level",
    "NAVIGATION_DISCLAIMER",
]
