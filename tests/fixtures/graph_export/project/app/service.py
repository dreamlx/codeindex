"""Auth service — exercises intra-file, cross-file, external, and INHERITS edges."""

import os

from app.validators import validate


class AuthService:
    """Authenticates users."""

    def authenticate(self, token: str) -> bool:
        return validate(token)  # cross-file CALLS -> app.validators.validate (resolved)

    def login(self, token: str) -> bool:
        return self.authenticate(token)  # intra-file CALLS -> AuthService.authenticate


class AdminService(AuthService):  # INHERITS -> AuthService
    """Admin auth with extra capability."""

    def cwd(self) -> str:
        return os.getcwd()  # external CALLS -> unresolved (not in fixture)
