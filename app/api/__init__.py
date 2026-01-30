"""
GETOLS API Routes
"""

from fastapi import APIRouter

from app.api import auth, dashboard, olt, onu, templates, users, activity, system

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(olt.router, prefix="/olt", tags=["OLT Management"])
api_router.include_router(onu.router, prefix="/onu", tags=["ONU Management"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(activity.router, prefix="/activity", tags=["Activity Log"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
