"""
GETOLS System API Routes
System settings and information endpoints.
"""

import markdown
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from app.models.user import User
from app.api.deps import require_password_change_check, require_admin
from app.templates import templates
from app import __version__

router = APIRouter()


# Changelog content
CHANGELOG = """
## [1.0.0] - 2025-01-30

### Added

#### Core Features
- Initial stable release of GETOLS
- Web-based dashboard with HTMX + Jinja2
- FastAPI backend with async support

#### OLT Management
- Support for ZTE ZXA10 C300 (GPON)
- Support for ZTE ZXA10 C320 (GPON)
- SSH and Telnet connection options
- Custom port support for port forwarding
- Separate RO and RW credentials

#### ONU Operations
- ONU Discovery via CLI
- ONU Registration with template support
- ONU Deletion with confirmation
- Manual parameter override

#### Monitoring
- SNMP v2c read-only monitoring
- ONU status monitoring
- RX/TX power levels
- PON port utilization

#### Security
- Role-Based Access Control
- AES-256-GCM encryption
- Secure session cookies
- Password policy enforcement
- Single session per user

### Security Notes
- SNMP SET operations are blocked
- RO credentials cannot perform provisioning
- RW credentials are not used for monitoring
- Telnet usage displays security warning
"""


@router.get("/settings", response_class=HTMLResponse)
async def system_settings(
    request: Request,
    user: User = Depends(require_admin),
):
    """Display system settings page."""
    return templates.TemplateResponse(
        "pages/system/settings.html",
        {
            "request": request,
            "user": user,
        }
    )


@router.get("/about", response_class=HTMLResponse)
async def system_about(
    request: Request,
    user: User = Depends(require_password_change_check),
):
    """Display about page."""
    return templates.TemplateResponse(
        "pages/system/about.html",
        {
            "request": request,
            "user": user,
            "version": __version__,
        }
    )


@router.get("/changelog", response_class=HTMLResponse)
async def system_changelog(
    request: Request,
):
    """Return changelog content (for modal)."""
    changelog_html = markdown.markdown(CHANGELOG)
    
    return templates.TemplateResponse(
        "components/changelog_modal.html",
        {
            "request": request,
            "version": __version__,
            "changelog_html": changelog_html,
        }
    )
