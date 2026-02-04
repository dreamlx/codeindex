"""Error codes and structures for JSON output.

Story 4: Structured error handling for machine-readable errors.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """Error codes for command-level errors."""

    DIRECTORY_NOT_FOUND = "DIRECTORY_NOT_FOUND"
    NO_CONFIG_FOUND = "NO_CONFIG_FOUND"
    INVALID_PATH = "INVALID_PATH"
    PARSE_ERROR = "PARSE_ERROR"  # File-level
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ErrorInfo:
    """Structured error information for JSON output."""

    code: str  # ErrorCode value
    message: str
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }


def create_error_response(
    error: ErrorInfo,
    results: Optional[list] = None,
) -> dict:
    """
    Create standardized error response for JSON output.

    Args:
        error: Error information
        results: Optional partial results (for partial success)

    Returns:
        JSON-serializable error response dict
    """
    return {
        "success": False,
        "error": error.to_dict(),
        "results": results or [],
        "summary": {
            "total_files": len(results) if results else 0,
            "total_symbols": sum(len(r.get("symbols", [])) for r in (results or [])),
            "total_imports": sum(len(r.get("imports", [])) for r in (results or [])),
            "errors": 1,
        },
    }
