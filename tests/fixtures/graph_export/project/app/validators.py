"""Standalone validators — cross-file CALLS target."""


def validate(token: str) -> bool:
    """Return True for a non-empty token."""
    return bool(token)
