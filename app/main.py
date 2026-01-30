"""
GETOLS v1.0.0 - Gateway for Extended OLT Services
Main FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core import settings
from app.core.database import engine, Base, SessionLocal
from app.api import api_router
from app.services.user_service import UserService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("=" * 60)
    print("GETOLS v1.0.0 Starting...")
    print("=" * 60)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Create default admin user if needed
    db = SessionLocal()
    try:
        admin, generated_password = UserService.create_default_admin(db)
        if admin and generated_password:
            print("")
            print("=" * 60)
            print("  !! IMPORTANT - SAVE THIS PASSWORD !!")
            print("=" * 60)
            print(f"  Default admin user created")
            print(f"  Username : admin")
            print(f"  Password : {generated_password}")
            print("=" * 60)
            print("  ⚠ You MUST change this password on first login!")
            print("  ⚠ This password will NOT be shown again!")
            print("=" * 60)
            print("")
        else:
            print("✓ Admin user already exists")
    finally:
        db.close()
    
    print("=" * 60)
    print(f"GETOLS is running at http://{settings.host}:{settings.port}")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("GETOLS shutting down...")


# Create FastAPI app
app = FastAPI(
    title="GETOLS",
    description="Gateway for Extended OLT Services",
    version="1.0.0",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root(request: Request):
    """Redirect root to login (will redirect to dashboard if authenticated)."""
    return RedirectResponse(url="/login", status_code=302)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "app": "GETOLS",
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    from app.templates import templates
    from app.api.deps import get_current_user, get_db
    
    # Try to get current user for error page
    db = SessionLocal()
    try:
        user = await get_current_user(request, db)
    except:
        user = None
    finally:
        db.close()
    
    if user:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "user": user,
                "error_code": 404,
                "error_message": "Page not found",
            },
            status_code=404,
        )
    
    return RedirectResponse(url="/login")


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 errors."""
    from app.templates import templates
    
    return templates.TemplateResponse(
        "pages/error.html",
        {
            "request": request,
            "user": None,
            "error_code": 500,
            "error_message": "Internal server error",
        },
        status_code=500,
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
