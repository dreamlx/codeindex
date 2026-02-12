"""
codeindex - AI-native code indexing tool for large codebases

Usage:
    codeindex scan <path>     # Scan a directory and generate README_AI.md
    codeindex init            # Initialize .codeindex.yaml
    codeindex status          # Show indexing status
"""

try:
    from importlib.metadata import version

    __version__ = version("ai-codeindex")
except Exception:
    __version__ = "0.0.0-dev"
__all__ = ["__version__"]
