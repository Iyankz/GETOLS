"""
GETOLS API Dependencies
Common dependencies for API routes including authentication and RBAC.
"""

from typing import Optional
from functools import wraps

from fastapi import Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService


# Session cookie name
SESSION_COOKIE_NAME = "getols_session"


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get the current authenticated user from session cookie.
    
    Returns None if not authenticated.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    
    if not session_id:
        return None
    
    auth_service = AuthService(db)
    user, error = auth_service.validate_session(session_id)
    
    return user


async def require_auth(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Require authentication. Redirects to login if not authenticated.
    """
    user = await get_current_user(request, db)
    
    if not user:
        # For HTMX requests, return 401 with redirect header
        if request.headers.get("HX-Request"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"HX-Redirect": "/login"},
            )
        # For API requests (Accept: application/json), return JSON error
        accept = request.headers.get("Accept", "")
        if "application/json" in accept:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        # For regular browser requests, redirect to login
        from fastapi.responses import RedirectResponse
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
        )
    
    return user


async def require_admin(
    user: User = Depends(require_auth),
) -> User:
    """Require admin role."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_operator_or_admin(
    user: User = Depends(require_auth),
) -> User:
    """Require operator or admin role."""
    if user.role not in (UserRole.ADMIN, UserRole.OPERATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator or admin access required",
        )
    return user


async def require_password_change_check(
    request: Request,
    user: User = Depends(require_auth),
) -> User:
    """
    Check if user must change password.
    Redirects to password change page if required.
    """
    if user.must_change_password:
        # Allow access to password change endpoint
        if request.url.path == "/change-password":
            return user
        
        if request.headers.get("HX-Request"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Password change required",
                headers={"HX-Redirect": "/change-password"},
            )
        # For regular browser requests, redirect to change password
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/change-password?must_change=true"},
        )
    
    return user


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded header (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Get user agent from request."""
    return request.headers.get("User-Agent", "unknown")[:255]


class RBACChecker:
    """
    Role-Based Access Control checker.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(RBACChecker(UserRole.ADMIN))):
            ...
    """
    
    def __init__(self, *allowed_roles: UserRole):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        user: User = Depends(require_auth),
    ) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(r.value for r in self.allowed_roles)}",
            )
        return user


# Common permission checkers
can_manage_users = RBACChecker(UserRole.ADMIN)
can_manage_olt = RBACChecker(UserRole.ADMIN)
can_provision = RBACChecker(UserRole.ADMIN, UserRole.OPERATOR)
can_discover = RBACChecker(UserRole.ADMIN, UserRole.OPERATOR)
can_manage_templates = RBACChecker(UserRole.ADMIN)
