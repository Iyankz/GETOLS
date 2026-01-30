"""
GETOLS ONU API Routes
ONU discovery, provisioning, and monitoring endpoints.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.activity import ActionType, AccessType
from app.services.olt_service import OLTService
from app.services.onu_service import ONUService
from app.services.template_service import TemplateService
from app.services.activity_service import ActivityService
from app.api.deps import (
    require_auth,
    require_password_change_check,
    can_provision,
    can_discover,
    get_client_ip,
)
from app.templates import templates

router = APIRouter()


# ============================================
# ONU LIST & MONITORING
# ============================================

@router.get("", response_class=HTMLResponse)
async def onu_list(
    request: Request,
    olt_id: int = None,
    message: str = None,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display ONU list page."""
    olt_service = OLTService(db)
    onu_service = ONUService(db)
    
    olts = olt_service.get_enabled()
    
    if olt_id:
        onus = onu_service.get_by_olt(olt_id)
        selected_olt = olt_service.get_by_id(olt_id)
    else:
        onus = onu_service.get_all()
        selected_olt = None
    
    return templates.TemplateResponse(
        "pages/onu/list.html",
        {
            "request": request,
            "user": user,
            "onus": onus,
            "olts": olts,
            "selected_olt": selected_olt,
            "message": message,
        }
    )


@router.get("/monitoring", response_class=HTMLResponse)
async def onu_monitoring(
    request: Request,
    olt_id: int = None,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display ONU monitoring page (read-only)."""
    olt_service = OLTService(db)
    onu_service = ONUService(db)
    
    olts = olt_service.get_enabled()
    
    if olt_id:
        onus = onu_service.get_provisioned(olt_id)
        selected_olt = olt_service.get_by_id(olt_id)
    else:
        onus = onu_service.get_provisioned()
        selected_olt = None
    
    return templates.TemplateResponse(
        "pages/onu/monitoring.html",
        {
            "request": request,
            "user": user,
            "onus": onus,
            "olts": olts,
            "selected_olt": selected_olt,
        }
    )


@router.post("/monitoring/refresh", response_class=HTMLResponse)
async def onu_refresh_monitoring(
    request: Request,
    olt_id: int = Form(...),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Refresh ONU monitoring data via SNMP."""
    onu_service = ONUService(db)
    
    updated, failed = onu_service.refresh_onu_status(olt_id)
    onus = onu_service.get_provisioned(olt_id)
    
    return templates.TemplateResponse(
        "components/onu_monitoring_table.html",
        {
            "request": request,
            "onus": onus,
            "updated": updated,
            "failed": failed,
        }
    )


# ============================================
# ONU DISCOVERY
# ============================================

@router.get("/discovery", response_class=HTMLResponse)
async def onu_discovery_page(
    request: Request,
    olt_id: int = None,
    user: User = Depends(can_discover),
    db: Session = Depends(get_db),
):
    """Display ONU discovery page."""
    olt_service = OLTService(db)
    olts = olt_service.get_enabled()
    
    selected_olt = None
    if olt_id:
        selected_olt = olt_service.get_by_id(olt_id)
    
    return templates.TemplateResponse(
        "pages/onu/discovery.html",
        {
            "request": request,
            "user": user,
            "olts": olts,
            "selected_olt": selected_olt,
            "discovered_onus": [],
        }
    )


@router.post("/discovery/run", response_class=HTMLResponse)
async def onu_discovery_run(
    request: Request,
    olt_id: int = Form(...),
    user: User = Depends(can_discover),
    db: Session = Depends(get_db),
):
    """Run ONU discovery on an OLT."""
    olt_service = OLTService(db)
    onu_service = ONUService(db)
    activity_service = ActivityService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        return templates.TemplateResponse(
            "components/discovery_result.html",
            {
                "request": request,
                "success": False,
                "error": "OLT not found",
                "discovered_onus": [],
            }
        )
    
    # Run discovery using RO credentials
    success, discovered_onus, error = onu_service.discover(olt_id)
    
    # Log action
    activity_service.log_olt_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.ONU_DISCOVER,
        olt_id=olt.id,
        olt_name=olt.name,
        success=success,
        access_type=AccessType.RO,
        error_message=error,
        ip_address=get_client_ip(request),
    )
    
    return templates.TemplateResponse(
        "components/discovery_result.html",
        {
            "request": request,
            "success": success,
            "error": error,
            "discovered_onus": discovered_onus,
            "olt": olt,
        }
    )


# ============================================
# ONU PROVISIONING
# ============================================

@router.get("/provision", response_class=HTMLResponse)
async def onu_provision_form(
    request: Request,
    olt_id: int,
    pon_port: str,
    onu_id: int,
    serial_number: str,
    user: User = Depends(can_provision),
    db: Session = Depends(get_db),
):
    """Display ONU provisioning form."""
    olt_service = OLTService(db)
    template_service = TemplateService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    templates_list = template_service.get_active()
    default_template = template_service.get_default()
    
    return templates.TemplateResponse(
        "pages/onu/provision.html",
        {
            "request": request,
            "user": user,
            "olt": olt,
            "pon_port": pon_port,
            "onu_id": onu_id,
            "serial_number": serial_number,
            "templates": templates_list,
            "default_template": default_template,
        }
    )


@router.post("/provision")
async def onu_provision(
    request: Request,
    olt_id: int = Form(...),
    pon_port: str = Form(...),
    onu_id: int = Form(...),
    serial_number: str = Form(...),
    name: str = Form(...),
    template_id: int = Form(None),
    line_profile: str = Form(None),
    service_profile: str = Form(None),
    vlan: int = Form(None),
    service_port: int = Form(None),
    user: User = Depends(can_provision),
    db: Session = Depends(get_db),
):
    """Process ONU provisioning."""
    olt_service = OLTService(db)
    onu_service = ONUService(db)
    activity_service = ActivityService(db)
    
    olt = olt_service.get_by_id(olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    # Register ONU using RW credentials
    onu, error = onu_service.register(
        olt_id=olt_id,
        pon_port=pon_port,
        onu_id=onu_id,
        serial_number=serial_number,
        name=name,
        template_id=template_id,
        line_profile=line_profile,
        service_profile=service_profile,
        vlan=vlan,
        service_port=service_port,
        provisioned_by=user.username,
    )
    
    # Log action
    activity_service.log_onu_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.ONU_REGISTER,
        onu_id=onu.id if onu else 0,
        onu_serial=serial_number,
        olt_name=olt.name,
        success=onu is not None,
        access_type=AccessType.RW,
        error_message=error,
        ip_address=get_client_ip(request),
        extra_data={
            "pon_port": pon_port,
            "onu_id": onu_id,
            "template_id": template_id,
            "vlan": vlan,
        },
    )
    
    if error:
        template_service = TemplateService(db)
        return templates.TemplateResponse(
            "pages/onu/provision.html",
            {
                "request": request,
                "user": user,
                "olt": olt,
                "pon_port": pon_port,
                "onu_id": onu_id,
                "serial_number": serial_number,
                "templates": template_service.get_active(),
                "default_template": template_service.get_default(),
                "error": error,
                "form_data": {
                    "name": name,
                    "template_id": template_id,
                    "line_profile": line_profile,
                    "service_profile": service_profile,
                    "vlan": vlan,
                    "service_port": service_port,
                },
            },
            status_code=400,
        )
    
    return RedirectResponse(
        url=f"/onu?olt_id={olt_id}&message=ONU+{serial_number}+provisioned+successfully",
        status_code=302,
    )


@router.get("/{onu_db_id}", response_class=HTMLResponse)
async def onu_detail(
    request: Request,
    onu_db_id: int,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display ONU detail page."""
    onu_service = ONUService(db)
    activity_service = ActivityService(db)
    
    onu = onu_service.get_by_id(onu_db_id)
    if not onu:
        raise HTTPException(status_code=404, detail="ONU not found")
    
    # Get activity for this ONU
    activities = activity_service.get_by_target("onu", onu_db_id, limit=20)
    
    return templates.TemplateResponse(
        "pages/onu/detail.html",
        {
            "request": request,
            "user": user,
            "onu": onu,
            "activities": activities,
        }
    )


@router.post("/{onu_db_id}/delete")
async def onu_delete(
    request: Request,
    onu_db_id: int,
    delete_from_olt: bool = Form(True),
    user: User = Depends(can_provision),
    db: Session = Depends(get_db),
):
    """Delete an ONU."""
    onu_service = ONUService(db)
    activity_service = ActivityService(db)
    
    onu = onu_service.get_by_id(onu_db_id)
    if not onu:
        raise HTTPException(status_code=404, detail="ONU not found")
    
    olt_id = onu.olt_id
    onu_serial = onu.serial_number
    olt_name = onu.olt.name
    
    success, error = onu_service.delete_onu(onu_db_id, delete_from_olt)
    
    # Log action
    activity_service.log_onu_action(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.ONU_DELETE,
        onu_id=onu_db_id,
        onu_serial=onu_serial,
        olt_name=olt_name,
        success=success,
        access_type=AccessType.RW if delete_from_olt else AccessType.NONE,
        error_message=error,
        ip_address=get_client_ip(request),
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return RedirectResponse(
        url=f"/onu?olt_id={olt_id}&message=ONU+{onu_serial}+deleted+successfully",
        status_code=302,
    )
