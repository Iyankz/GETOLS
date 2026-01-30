"""
GETOLS Auth API Routes
Handles login, logout, and password change.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import settings
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.activity_service import ActivityService
from app.models.activity import ActionType
from app.api.deps import (
    SESSION_COOKIE_NAME,
    get_current_user,
    require_auth,
    get_client_ip,
    get_user_agent,
)
from app.templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    db: Session = Depends(get_db),
    error: str = None,
):
    """Display login page."""
    # If already logged in, redirect to dashboard
    user = await get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "pages/login.html",
        {
            "request": request,
            "error": error,
        }
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process login form."""
    auth_service = AuthService(db)
    activity_service = ActivityService(db)
    
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Authenticate user
    user, error = auth_service.authenticate(username, password)
    
    if not user:
        # Log failed attempt
        activity_service.log_login(
            user_id=None,
            username=username,
            role="unknown",
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error,
        )
        
        return templates.TemplateResponse(
            "pages/login.html",
            {
                "request": request,
                "error": error or "Invalid credentials",
                "username": username,
            },
            status_code=401,
        )
    
    # Create session
    session = auth_service.create_session(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    # Log successful login
    activity_service.log_login(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    # Create response with redirect
    if user.must_change_password:
        response = RedirectResponse(url="/change-password", status_code=302)
    else:
        response = RedirectResponse(url="/dashboard", status_code=302)
    
    # Set session cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_id,
        httponly=settings.cookie_httponly,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.session_lifetime * 60,
    )
    
    return response


@router.get("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
):
    """Log out the current user."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    
    if session_id:
        auth_service = AuthService(db)
        activity_service = ActivityService(db)
        
        # Get user before invalidating session
        user, _ = auth_service.validate_session(session_id)
        
        if user:
            activity_service.log_logout(
                user_id=user.id,
                username=user.username,
                role=user.role.value,
                ip_address=get_client_ip(request),
            )
        
        # Invalidate session
        auth_service.invalidate_session(session_id)
    
    # Clear cookie and redirect
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME)
    
    return response


@router.get("/change-password", response_class=HTMLResponse)
async def change_password_page(
    request: Request,
    user = Depends(require_auth),
):
    """Display password change page."""
    return templates.TemplateResponse(
        "pages/change_password.html",
        {
            "request": request,
            "user": user,
            "must_change": user.must_change_password,
        }
    )


@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Process password change form."""
    user_service = UserService(db)
    activity_service = ActivityService(db)
    
    # Validate new password matches confirmation
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "pages/change_password.html",
            {
                "request": request,
                "user": user,
                "must_change": user.must_change_password,
                "error": "New passwords do not match",
            },
            status_code=400,
        )
    
    # Change password
    success, error = user_service.change_password(
        user_id=user.id,
        current_password=current_password,
        new_password=new_password,
    )
    
    if not success:
        return templates.TemplateResponse(
            "pages/change_password.html",
            {
                "request": request,
                "user": user,
                "must_change": user.must_change_password,
                "error": error,
            },
            status_code=400,
        )
    
    # Log password change
    activity_service.log(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.PASSWORD_CHANGE,
        success=True,
        action_detail=f"User {user.username} changed their password",
        ip_address=get_client_ip(request),
    )
    
    # Redirect to dashboard
    return RedirectResponse(url="/dashboard?message=Password+changed+successfully", status_code=302)
