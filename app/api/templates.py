"""
GETOLS Templates API Routes
Provisioning template management endpoints.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.activity import ActionType
from app.services.template_service import TemplateService
from app.services.activity_service import ActivityService
from app.api.deps import (
    require_password_change_check,
    can_manage_templates,
    get_client_ip,
)
from app.templates import templates

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def template_list(
    request: Request,
    message: str = None,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display template list page."""
    template_service = TemplateService(db)
    template_list = template_service.get_all()
    
    return templates.TemplateResponse(
        "pages/templates/list.html",
        {
            "request": request,
            "user": user,
            "templates": template_list,
            "message": message,
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def template_add_form(
    request: Request,
    user: User = Depends(can_manage_templates),
):
    """Display template add form."""
    return templates.TemplateResponse(
        "pages/templates/form.html",
        {
            "request": request,
            "user": user,
            "template": None,
            "mode": "add",
        }
    )


@router.post("/add")
async def template_add(
    request: Request,
    name: str = Form(...),
    line_profile: str = Form(...),
    service_profile: str = Form(...),
    vlan: int = Form(...),
    description: str = Form(None),
    service_port_start: int = Form(None),
    is_default: bool = Form(False),
    user: User = Depends(can_manage_templates),
    db: Session = Depends(get_db),
):
    """Process template add form."""
    template_service = TemplateService(db)
    activity_service = ActivityService(db)
    
    template, error = template_service.create(
        name=name,
        line_profile=line_profile,
        service_profile=service_profile,
        vlan=vlan,
        description=description,
        service_port_start=service_port_start,
        is_default=is_default,
        created_by=user.username,
    )
    
    if error:
        return templates.TemplateResponse(
            "pages/templates/form.html",
            {
                "request": request,
                "user": user,
                "template": None,
                "mode": "add",
                "error": error,
                "form_data": {
                    "name": name,
                    "line_profile": line_profile,
                    "service_profile": service_profile,
                    "vlan": vlan,
                    "description": description,
                    "service_port_start": service_port_start,
                    "is_default": is_default,
                },
            },
            status_code=400,
        )
    
    # Log action
    activity_service.log(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.TEMPLATE_CREATE,
        success=True,
        target_type="template",
        target_id=template.id,
        target_name=template.name,
        action_detail=f"Created template {template.name}",
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/templates?message=Template+{name}+created+successfully",
        status_code=302,
    )


@router.get("/{template_id}", response_class=HTMLResponse)
async def template_detail(
    request: Request,
    template_id: int,
    user: User = Depends(require_password_change_check),
    db: Session = Depends(get_db),
):
    """Display template detail page."""
    template_service = TemplateService(db)
    template = template_service.get_by_id(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return templates.TemplateResponse(
        "pages/templates/detail.html",
        {
            "request": request,
            "user": user,
            "template": template,
        }
    )


@router.get("/{template_id}/edit", response_class=HTMLResponse)
async def template_edit_form(
    request: Request,
    template_id: int,
    user: User = Depends(can_manage_templates),
    db: Session = Depends(get_db),
):
    """Display template edit form."""
    template_service = TemplateService(db)
    template = template_service.get_by_id(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return templates.TemplateResponse(
        "pages/templates/form.html",
        {
            "request": request,
            "user": user,
            "template": template,
            "mode": "edit",
        }
    )


@router.post("/{template_id}/edit")
async def template_edit(
    request: Request,
    template_id: int,
    name: str = Form(...),
    line_profile: str = Form(...),
    service_profile: str = Form(...),
    vlan: int = Form(...),
    description: str = Form(None),
    service_port_start: int = Form(None),
    is_active: bool = Form(True),
    is_default: bool = Form(False),
    user: User = Depends(can_manage_templates),
    db: Session = Depends(get_db),
):
    """Process template edit form."""
    template_service = TemplateService(db)
    activity_service = ActivityService(db)
    
    template, error = template_service.update(
        template_id=template_id,
        name=name,
        line_profile=line_profile,
        service_profile=service_profile,
        vlan=vlan,
        description=description,
        service_port_start=service_port_start,
        is_active=is_active,
        is_default=is_default,
    )
    
    if error:
        template = template_service.get_by_id(template_id)
        return templates.TemplateResponse(
            "pages/templates/form.html",
            {
                "request": request,
                "user": user,
                "template": template,
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
        action=ActionType.TEMPLATE_UPDATE,
        success=True,
        target_type="template",
        target_id=template.id,
        target_name=template.name,
        action_detail=f"Updated template {template.name}",
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/templates?message=Template+{name}+updated+successfully",
        status_code=302,
    )


@router.post("/{template_id}/delete")
async def template_delete(
    request: Request,
    template_id: int,
    user: User = Depends(can_manage_templates),
    db: Session = Depends(get_db),
):
    """Delete a template."""
    template_service = TemplateService(db)
    activity_service = ActivityService(db)
    
    template = template_service.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template_name = template.name
    success, error = template_service.delete(template_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    # Log action
    activity_service.log(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        action=ActionType.TEMPLATE_DELETE,
        success=True,
        target_type="template",
        target_id=template_id,
        target_name=template_name,
        action_detail=f"Deleted template {template_name}",
        ip_address=get_client_ip(request),
    )
    
    return RedirectResponse(
        url=f"/templates?message=Template+{template_name}+deleted+successfully",
        status_code=302,
    )


@router.post("/{template_id}/set-default")
async def template_set_default(
    request: Request,
    template_id: int,
    user: User = Depends(can_manage_templates),
    db: Session = Depends(get_db),
):
    """Set a template as default."""
    template_service = TemplateService(db)
    
    success, error = template_service.set_default(template_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    template = template_service.get_by_id(template_id)
    
    return RedirectResponse(
        url=f"/templates?message=Template+{template.name}+set+as+default",
        status_code=302,
    )
