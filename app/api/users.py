"""
GETOLS Users API Routes
User management endpoints.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.activity import ActionType
from app.services.user_service import UserService
from app.services.activity_service import ActivityService
from app.api.deps import (
    require_password_change_check,
    can_manage_users,
    get_client_ip,
)
from app.templates import templates

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def user_list(
    request: Request,
    message: str = None,
    user: User = Depends(can_manage_users),
    db: Session = Depends(get_db),
):
    """Display user list page."""
    user_service = UserService(db)
    users = user_service.get_all()
    
    return templates.TemplateResponse(
        "pages/users/list.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "message": message,
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def user_add_form(
    request: Request,
    user: User = Depends(can_manage_users),
):
    """Display user add form."""
    return templates.TemplateResponse(
        "pages/users/form.html",
        {
            "request": request,
            "user": user,
            "edit_user": None,
            "roles": UserRole,
            "mode": "add",
        }
    )


@router.post("/add")
async def user_add(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role: str = Form(...),
    email: str = Form(None),
    full_name: str = Form(None),
    user: User = Depends(can_manage_users),
    db: Session = Depends(get_db),
):
    """Process user add form."""
    user_service = UserService(db)
    activity_service = ActivityService(db)
    
    # Validate password match
    if password != confirm_password:
        return templates.TemplateResponse(
            "pages/users/form.html",
            {
                "request": request,
                "user": user,
                "edit_user": None,
                "roles": UserRole,
                "mode": "add",
                "error": "Passwords do not match",
                "form_data": {
                    "username": username,
                    "role": role,
                    "email": email,
                    "full_name": full_name,
                },
            },
            status_code=400,
        )
    
    new_user, error = user_service.create(
        username=username,
        password=password,
        role=UserRole(role),
        email=email if email else None,
        full_name=full_name if full_name else None,
        must_change_password=True,
    )
    
    if error:
        return templates.TemplateResponse(
            "pages/users/form.html",
            {
                "request": request,
                "user": user,
                "edit_user": None,
                "roles": UserRole,
                "mode": "add",
                "error": error,
                "form_data": {
                    "username": username,
                    "role": role,
                    "email": email,
                    "full_name": full_name,
                },
            },
            status_code=400,
        )
    
    # Log action
    activity_service.log(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.USER_CREATE,
        success=True,
        target_type="user",
        target_id=new_user.id,
        target_name=new_user.username,
        action_detail=f"Created user {new_user.username} with role {new_user.role.value}",
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/users?message=User+{username}+created+successfully",
        status_code=302,
    )


@router.get("/{user_id}", response_class=HTMLResponse)
async def user_detail(
    request: Request,
    user_id: int,
    user: User = Depends(can_manage_users),
    db: Session = Depends(get_db),
):
    """Display user detail page."""
    user_service = UserService(db)
    activity_service = ActivityService(db)
    
    edit_user = user_service.get_by_id(user_id)
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user activity
    activities = activity_service.get_by_user(user_id, limit=20)
    
    return templates.TemplateResponse(
        "pages/users/detail.html",
        {
            "request": request,
            "user": user,
            "edit_user": edit_user,
            "activities": activities,
        }
    )


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def user_edit_form(
    request: Request,
    user_id: int,
    user: User = Depends(can_manage_users),
    db: Session = Depends(get_db),
):
    """Display user edit form."""
    user_service = UserService(db)
    edit_user = user_service.get_by_id(user_id)
    
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return templates.TemplateResponse(
        "pages/users/form.html",
        {
            "request": request,
            "user": user,
            "edit_user": edit_user,
            "roles": UserRole,
            "mode": "edit",
        }
    )


@router.post("/{user_id}/edit")
async def user_edit(
    request: Request,
    user_id: int,
    role: str = Form(...),
    email: str = Form(None),
    full_name: str = Form(None),
    is_active: bool = Form(True),
    user: User = Depends(can_manage_users),
    db: Session = Depends(get_db),
):
    """Process user edit form."""
    user_service = UserService(db)
    activity_service = ActivityService(db)
    
    edit_user, error = user_service.update(
        user_id=user_id,
        email=email if email else None,
        full_name=full_name if full_name else None,
        role=UserRole(role),
        is_active=is_active,
    )
    
    if error:
        edit_user = user_service.get_by_id(user_id)
        return templates.TemplateResponse(
            "pages/users/form.html",
            {
                "request": request,
                "user": user,
                "edit_user": edit_user,
                "roles": UserRole,
                "mode": "edit",
                "error": error,
            },
            status_code=400,
        )
    
    # Log action
    activity_service.log(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.USER_UPDATE,
        success=True,
        target_type="user",
        target_id=edit_user.id,
        target_name=edit_user.username,
        action_detail=f"Updated user {edit_user.username}",
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/users?message=User+{edit_user.username}+updated+successfully",
        status_code=302,
    )


@router.post("/{user_id}/delete")
async def user_delete(
    request: Request,
    user_id: int,
    user: User = Depends(can_manage_users),
    db: Session = Depends(get_db),
):
    """Delete a user."""
    user_service = UserService(db)
    activity_service = ActivityService(db)
    
    # Prevent self-deletion
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    edit_user = user_service.get_by_id(user_id)
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    username = edit_user.username
    success, error = user_service.delete(user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    # Log action
    activity_service.log(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.USER_DELETE,
        success=True,
        target_type="user",
        target_id=user_id,
        target_name=username,
        action_detail=f"Deleted user {username}",
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/users?message=User+{username}+deleted+successfully",
        status_code=302,
    )


@router.post("/{user_id}/reset-password")
async def user_reset_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: User = Depends(can_manage_users),
    db: Session = Depends(get_db),
):
    """Reset a user's password."""
    user_service = UserService(db)
    activity_service = ActivityService(db)
    
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    edit_user = user_service.get_by_id(user_id)
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success, error = user_service.reset_password(user_id, new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    # Log action
    activity_service.log(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.PASSWORD_CHANGE,
        success=True,
        target_type="user",
        target_id=user_id,
        target_name=edit_user.username,
        action_detail=f"Admin reset password for {edit_user.username}",
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/users/{user_id}?message=Password+reset+successfully",
        status_code=302,
    )
