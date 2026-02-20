"""Smart README writer package with focused generator classes.

Provides level-specific README generation:
- OverviewGenerator: Project/root level documentation
- NavigationGenerator: Module level documentation
- DetailedGenerator: Leaf level detailed documentation
- SmartWriter: Facade that dispatches to generators
"""

from .core import LevelType, SmartWriter, WriteResult, determine_level

__all__ = ["SmartWriter", "WriteResult", "LevelType", "determine_level"]
