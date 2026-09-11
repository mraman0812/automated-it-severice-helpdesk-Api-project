from typing import Generator, List, Callable
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.database.database import get_db
from app.models.user import User
from app.models.role import RoleEnum

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    if not token:
        raise UnauthorizedException("Authentication token is required")

    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired authentication token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing subject")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user identifier in token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("User no longer exists")

    if not user.is_active:
        raise ForbiddenException("User account is inactive")

    return user


def require_roles(allowed_roles: List[RoleEnum]) -> Callable:
    """
    Role-Based Access Control dependency factory.
    """
    allowed_role_names = [r.value for r in allowed_roles]

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_name = current_user.role.name if current_user.role else ""
        if user_role_name not in allowed_role_names:
            raise ForbiddenException(
                f"Action forbidden: requires one of roles {allowed_role_names}, your role is '{user_role_name}'"
            )
        return current_user

    return role_checker
