"""
GETOLS Dashboard API Routes
Main dashboard page.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.user_service import UserService
from app.services.olt_service import OLTService
from app.services.onu_service import ONUService
from app.services.activity_service import ActivityService
from app.models.user import User, UserRole
from app.models.onu import ONUStatus
from app.api.deps import require_auth, require_password_change_check
from app.templates import templates

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    message: str = None,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display main dashboard."""
    user_service = UserService(db)
    olt_service = OLTService(db)
    onu_service = ONUService(db)
    activity_service = ActivityService(db)
    
    # Gather statistics
    stats = {
        "users": {
            "total": user_service.count(),
            "admins": user_service.count_by_role(UserRole.ADMIN),
            "operators": user_service.count_by_role(UserRole.OPERATOR),
            "viewers": user_service.count_by_role(UserRole.VIEWER),
        },
        "olts": {
            "total": olt_service.count(),
            "enabled": len(olt_service.get_enabled()),
        },
        "onus": {
            "total": onu_service.count(),
            "online": onu_service.count_by_status(ONUStatus.ONLINE),
            "offline": onu_service.count_by_status(ONUStatus.OFFLINE),
            "low_signal": onu_service.count_by_status(ONUStatus.LOW_SIGNAL),
        },
    }
    
    # Get OLTs for status display
    olts = olt_service.get_all(limit=10)
    
    # Get recent activity
    recent_activity = activity_service.get_recent(limit=10)
    
    # Get activity statistics
    activity_stats = activity_service.get_statistics(days=7)
    
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "olts": olts,
            "recent_activity": recent_activity,
            "activity_stats": activity_stats,
            "message": message,
        }
    )


@router.get("/stats", response_class=HTMLResponse)
async def dashboard_stats(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics (HTMX partial)."""
    olt_service = OLTService(db)
    onu_service = ONUService(db)
    
    stats = {
        "olts": {
            "total": olt_service.count(),
            "enabled": len(olt_service.get_enabled()),
        },
        "onus": {
            "total": onu_service.count(),
            "online": onu_service.count_by_status(ONUStatus.ONLINE),
            "offline": onu_service.count_by_status(ONUStatus.OFFLINE),
        },
    }
    
    return templates.TemplateResponse(
        "components/dashboard_stats.html",
        {
            "request": request,
            "stats": stats,
        }
    )


@router.get("/activity", response_class=HTMLResponse)
async def dashboard_activity(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get recent activity (HTMX partial)."""
    activity_service = ActivityService(db)
    recent_activity = activity_service.get_recent(limit=10)
    
    return templates.TemplateResponse(
        "components/activity_list.html",
        {
            "request": request,
            "activities": recent_activity,
        }
    )
