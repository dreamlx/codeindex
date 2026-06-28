"""Domain models."""

from dataclasses import dataclass


@dataclass
class User:
    """An application user."""

    id: int
    name: str
    password_hash: str

    def check_password(self, password: str) -> bool:
        """Naive password check for fixture purposes."""
        return self.password_hash == f"hash:{password}"
