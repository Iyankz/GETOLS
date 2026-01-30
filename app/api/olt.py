"""
GETOLS OLT API Routes
OLT management endpoints.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.olt import OLTType
from app.models.activity import ActionType, AccessType
from app.services.olt_service import OLTService
from app.services.activity_service import ActivityService
from app.api.deps import (
    require_auth,
    require_admin,
    require_password_change_check,
    get_client_ip,
)
from app.templates import templates

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def olt_list(
    request: Request,
    message: str = None,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display OLT list page."""
    olt_service = OLTService(db)
    olts = olt_service.get_all()
    
    return templates.TemplateResponse(
        "pages/olt/list.html",
        {
            "request": request,
            "user": user,
            "olts": olts,
            "message": message,
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def olt_add_form(
    request: Request,
    user: User = Depends(require_admin),
):
    """Display OLT add form."""
    return templates.TemplateResponse(
        "pages/olt/form.html",
        {
            "request": request,
            "user": user,
            "olt": None,
            "olt_types": OLTType,
            "mode": "add",
        }
    )


@router.post("/add")
async def olt_add(
    request: Request,
    name: str = Form(...),
    olt_type: str = Form(...),
    ip_address: str = Form(...),
    cli_port: int = Form(23),
    cli_username: str = Form(...),
    cli_password: str = Form(...),
    snmp_ro_community: str = Form(...),
    snmp_rw_community: str = Form(None),
    snmp_port: int = Form(161),
    description: str = Form(None),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Process OLT add form."""
    olt_service = OLTService(db)
    activity_service = ActivityService(db)
    
    olt, error = olt_service.create(
        name=name,
        olt_type=OLTType(olt_type),
        ip_address=ip_address,
        cli_port=cli_port,
        cli_username=cli_username,
        cli_password=cli_password,
        snmp_ro_community=snmp_ro_community,
        snmp_rw_community=snmp_rw_community if snmp_rw_community else None,
        snmp_port=snmp_port,
        description=description,
    )
    
    if error:
        return templates.TemplateResponse(
            "pages/olt/form.html",
            {
                "request": request,
                "user": user,
                "olt": None,
                "olt_types": OLTType,
                "mode": "add",
                "error": error,
                "form_data": {
                    "name": name,
                    "olt_type": olt_type,
                    "ip_address": ip_address,
                    "cli_port": cli_port,
                    "cli_username": cli_username,
                    "snmp_port": snmp_port,
                    "description": description,
                },
            },
            status_code=400,
        )
    
    # Log action
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.OLT_CREATE,
        olt_id=olt.id,
        olt_name=olt.name,
        success=True,
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/olt?message=OLT+{name}+created+successfully",
        status_code=302,
    )


@router.get("/{olt_id}", response_class=HTMLResponse)
async def olt_detail(
    request: Request,
    olt_id: int,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display OLT detail page."""
    olt_service = OLTService(db)
    olt = olt_service.get_by_id(olt_id)
    
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    return templates.TemplateResponse(
        "pages/olt/detail.html",
        {
            "request": request,
            "user": user,
            "olt": olt,
        }
    )


@router.get("/{olt_id}/edit", response_class=HTMLResponse)
async def olt_edit_form(
    request: Request,
    olt_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Display OLT edit form."""
    olt_service = OLTService(db)
    olt = olt_service.get_by_id(olt_id)
    
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    return templates.TemplateResponse(
        "pages/olt/form.html",
        {
            "request": request,
            "user": user,
            "olt": olt,
            "olt_types": OLTType,
            "mode": "edit",
        }
    )


@router.post("/{olt_id}/edit")
async def olt_edit(
    request: Request,
    olt_id: int,
    name: str = Form(...),
    olt_type: str = Form(...),
    ip_address: str = Form(...),
    cli_port: int = Form(23),
    cli_username: str = Form(...),
    cli_password: str = Form(None),
    snmp_ro_community: str = Form(None),
    snmp_rw_community: str = Form(None),
    snmp_port: int = Form(161),
    description: str = Form(None),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Process OLT edit form."""
    olt_service = OLTService(db)
    activity_service = ActivityService(db)
    
    olt, error = olt_service.update(
        olt_id=olt_id,
        name=name,
        olt_type=OLTType(olt_type),
        ip_address=ip_address,
        cli_port=cli_port,
        cli_username=cli_username,
        cli_password=cli_password if cli_password else None,
        snmp_ro_community=snmp_ro_community if snmp_ro_community else None,
        snmp_rw_community=snmp_rw_community if snmp_rw_community else None,
        snmp_port=snmp_port,
        description=description,
    )
    
    if error:
        olt = olt_service.get_by_id(olt_id)
        return templates.TemplateResponse(
            "pages/olt/form.html",
            {
                "request": request,
                "user": user,
                "olt": olt,
                "olt_types": OLTType,
                "mode": "edit",
                "error": error,
            },
            status_code=400,
        )
    
    # Log action
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.OLT_UPDATE,
        olt_id=olt.id,
        olt_name=olt.name,
        success=True,
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/olt?message=OLT+{name}+updated+successfully",
        status_code=302,
    )


@router.post("/{olt_id}/delete")
async def olt_delete(
    request: Request,
    olt_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete an OLT."""
    olt_service = OLTService(db)
    activity_service = ActivityService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    olt_name = olt.name
    success, error = olt_service.delete(olt_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    # Log action
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.OLT_DELETE,
        olt_id=olt_id,
        olt_name=olt_name,
        success=True,
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/olt?message=OLT+{olt_name}+deleted+successfully",
        status_code=302,
    )


@router.post("/{olt_id}/enable")
async def olt_enable(
    request: Request,
    olt_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Enable an OLT."""
    olt_service = OLTService(db)
    activity_service = ActivityService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    success, error = olt_service.enable(olt_id)
    
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.OLT_ENABLE,
        olt_id=olt.id,
        olt_name=olt.name,
        success=success,
        error_message=error,
        ip_address=get_client_ip(request),
    )
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "components/olt_status_badge.html",
            {"request": request, "olt": olt_service.get_by_id(olt_id)},
        )
    
    return RedirectResponse(url=f"/olt/{olt_id}", status_code=302)


@router.post("/{olt_id}/disable")
async def olt_disable(
    request: Request,
    olt_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Disable an OLT."""
    olt_service = OLTService(db)
    activity_service = ActivityService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    success, error = olt_service.disable(olt_id)
    
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.OLT_DISABLE,
        olt_id=olt.id,
        olt_name=olt.name,
        success=success,
        error_message=error,
        ip_address=get_client_ip(request),
    )
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "components/olt_status_badge.html",
            {"request": request, "olt": olt_service.get_by_id(olt_id)},
        )
    
    return RedirectResponse(url=f"/olt/{olt_id}", status_code=302)


@router.post("/{olt_id}/test/cli", response_class=HTMLResponse)
async def olt_test_cli(
    request: Request,
    olt_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Test OLT CLI Telnet connection."""
    olt_service = OLTService(db)
    activity_service = ActivityService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    success, error = olt_service.test_cli_connection(olt_id)
    
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.OLT_TEST_CLI,
        olt_id=olt.id,
        olt_name=olt.name,
        success=success,
        access_type=AccessType.CLI,
        error_message=error,
        ip_address=get_client_ip(request),
    )
    
    # Return test result component
    olt = olt_service.get_by_id(olt_id)  # Refresh
    return templates.TemplateResponse(
        "components/olt_test_result.html",
        {
            "request": request,
            "test_type": "CLI",
            "success": success,
            "error": error,
            "olt": olt,
        }
    )


@router.post("/{olt_id}/test/snmp", response_class=HTMLResponse)
async def olt_test_snmp(
    request: Request,
    olt_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Test OLT SNMP RO connection."""
    olt_service = OLTService(db)
    activity_service = ActivityService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    success, error = olt_service.test_snmp_connection(olt_id)
    
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.OLT_TEST_SNMP,
        olt_id=olt.id,
        olt_name=olt.name,
        success=success,
        access_type=AccessType.SNMP,
        error_message=error,
        ip_address=get_client_ip(request),
    )
    
    olt = olt_service.get_by_id(olt_id)
    return templates.TemplateResponse(
        "components/olt_test_result.html",
        {
            "request": request,
            "test_type": "SNMP",
            "success": success,
            "error": error,
            "olt": olt,
        }
    )
