import uuid
from typing import Callable, List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate bearer token and retrieve current user from database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except Exception:
        raise credentials_exception

    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure that the authenticated user's account is currently active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account."
        )
    return current_user


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory that verifies the authenticated user has one of the allowed roles."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of [{', '.join(r.value for r in allowed_roles)}] role."
            )
        return current_user

    return role_checker


# Role shortcut dependencies
require_admin = require_role(UserRole.ADMIN)
require_donor = require_role(UserRole.DONOR)
require_donor_or_admin = require_role(UserRole.DONOR, UserRole.ADMIN)


class AdminAuthContext:
    def __init__(self, admin_user: Optional[User] = None, is_bootstrap: bool = False):
        self.admin_user = admin_user
        self.is_bootstrap = is_bootstrap


async def require_admin_or_bootstrap_secret(
    x_admin_secret: Optional[str] = Header(None, alias="X-Admin-Secret"),
    token: Optional[str] = Depends(optional_oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AdminAuthContext:
    """
    Authorization dependency supporting dual mechanisms:
    1. Break-glass X-Admin-Secret header (constant-time comparison)
    2. Authenticated administrator Bearer JWT with live database role verification
    """
    import secrets
    from app.core.config import settings

    # 1. Check Break-Glass Bootstrap Secret
    if x_admin_secret is not None:
        configured_secret = settings.ADMIN_BOOTSTRAP_SECRET.strip() if settings.ADMIN_BOOTSTRAP_SECRET else ""
        if not configured_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin bootstrap secret is not configured on this server."
            )
        if not secrets.compare_digest(x_admin_secret.strip(), configured_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin bootstrap secret."
            )
        return AdminAuthContext(admin_user=None, is_bootstrap=True)

    # 2. Check Admin JWT
    if token:
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account."
            )

        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: requires ADMIN role."
            )

        return AdminAuthContext(admin_user=user, is_bootstrap=False)

    # 3. Neither bootstrap secret nor Bearer token provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a valid Admin JWT or X-Admin-Secret header.",
        headers={"WWW-Authenticate": "Bearer"},
    )

