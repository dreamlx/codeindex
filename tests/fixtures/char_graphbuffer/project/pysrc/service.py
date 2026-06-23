"""User authentication service.

Handles login, session creation and rate limiting.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import User
from .util.helpers import now_ts


@dataclass
class Session:
    """A user session with an expiry timestamp."""

    user_id: int
    token: str
    expires_at: int


class AuthService:
    """Authenticate users and issue sessions."""

    def __init__(self, secret: str) -> None:
        self.secret = secret

    def authenticate(self, user: User, password: str) -> bool:
        """Return True if the password matches the user."""
        return user.check_password(password)

    def create_session(self, user: User) -> Session:
        """Create a new session for an authenticated user."""
        return Session(user_id=user.id, token=self._mint(user), expires_at=now_ts() + 3600)

    def _mint(self, user: User) -> str:
        return f"{user.id}:{self.secret}"


def login(service: AuthService, user: User, password: str) -> Session | None:
    """Top-level helper: authenticate then create a session."""
    if service.authenticate(user, password):
        return service.create_session(user)
    return None
