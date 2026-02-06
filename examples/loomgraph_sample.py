"""Sample Python module for LoomGraph integration testing.

This module demonstrates all features that codeindex extracts for LoomGraph:
- Symbols (classes, methods, functions)
- Imports (with aliases)
- Inheritances (single, multiple, nested)
"""

import logging
import os  # noqa: F401 - Kept for import extraction testing
from datetime import datetime as dt
from typing import Dict, List, Optional  # noqa: F401 - Kept for import extraction testing

import numpy as np  # Used for data array types

logger = logging.getLogger(__name__)

# Module-level constant
DEFAULT_TIMEOUT = 30

# Type alias using numpy
UserData = np.ndarray


class BaseModel:
    """Base model with common CRUD operations."""

    def save(self) -> bool:
        """Save model to database."""
        return True

    def delete(self) -> None:
        """Delete model from database."""
        pass


class Loggable:
    """Mixin for logging capabilities."""

    def log(self, message: str) -> None:
        """Log a message."""
        logger.info(message)


class User(BaseModel, Loggable):
    """User account model with authentication."""

    def __init__(self, username: str, email: str):
        """Initialize user account.

        Args:
            username: User's unique username
            email: User's email address
        """
        self.username = username
        self.email = email
        self.created_at = dt.now()

    def authenticate(self, password: str) -> bool:
        """Authenticate user with password.

        Args:
            password: User's password

        Returns:
            True if authentication successful
        """
        return True

    def get_permissions(self) -> List[str]:
        """Get user permissions.

        Returns:
            List of permission names
        """
        return ["read", "write"]


class AdminUser(User):
    """Admin user with elevated privileges."""

    def grant_permission(self, user_id: int, permission: str) -> bool:
        """Grant permission to another user.

        Args:
            user_id: Target user ID
            permission: Permission name to grant

        Returns:
            True if permission granted successfully
        """
        self.log(f"Granted {permission} to user {user_id}")
        return True

    def revoke_permission(self, user_id: int, permission: str) -> bool:
        """Revoke permission from user.

        Args:
            user_id: Target user ID
            permission: Permission name to revoke

        Returns:
            True if permission revoked successfully
        """
        return True

    class AuditLog:
        """Nested class for audit logging."""

        def __init__(self, admin_id: int):
            """Initialize audit log.

            Args:
                admin_id: Admin user ID
            """
            self.admin_id = admin_id

        def record(self, action: str) -> None:
            """Record admin action.

            Args:
                action: Action description
            """
            pass


def get_user_by_id(user_id: int) -> Optional[User]:
    """Retrieve user by ID.

    Args:
        user_id: User ID to lookup

    Returns:
        User object if found, None otherwise
    """
    return None


def create_user(username: str, email: str) -> User:
    """Create new user account.

    Args:
        username: Desired username
        email: User's email

    Returns:
        Newly created User object
    """
    return User(username, email)
