"""
GETOLS Activity API Routes
Activity log viewing endpoints.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.activity import ActionType
from app.services.activity_service import ActivityService
from app.api.deps import require_password_change_check
from app.templates import templates

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def activity_list(
    request: Request,
    action: str = None,
    user_id: int = None,
    success: str = None,
    days: int = 7,
    page: int = 1,
    per_page: int = 50,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display activity log page."""
    activity_service = ActivityService(db)
    
    # Parse filters
    action_type = ActionType(action) if action else None
    success_bool = None
    if success == "true":
        success_bool = True
    elif success == "false":
        success_bool = False
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get logs
    skip = (page - 1) * per_page
    activities = activity_service.get_all(
        skip=skip,
        limit=per_page,
        action_type=action_type,
        user_id=user_id,
        success=success_bool,
        start_date=start_date,
    )
    
    # Get statistics
    stats = activity_service.get_statistics(days=days)
    
    return templates.TemplateResponse(
        "pages/activity/list.html",
        {
            "request": request,
            "user": user,
            "activities": activities,
            "stats": stats,
            "action_types": ActionType,
            "filters": {
                "action": action,
                "user_id": user_id,
                "success": success,
                "days": days,
            },
            "page": page,
            "per_page": per_page,
        }
    )


@router.get("/{log_id}", response_class=HTMLResponse)
async def activity_detail(
    request: Request,
    log_id: int,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display activity log detail."""
    activity_service = ActivityService(db)
    activity = activity_service.get_by_id(log_id)
    
    if not activity:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "user": user,
                "error": "Activity log not found",
            },
            status_code=404,
        )
    
    return templates.TemplateResponse(
        "pages/activity/detail.html",
        {
            "request": request,
            "user": user,
            "activity": activity,
        }
    )
