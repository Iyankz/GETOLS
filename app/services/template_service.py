"""
GETOLS Template Service
Handles provisioning template management.
"""

from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from app.models.template import ProvisioningTemplate


class TemplateService:
    """Service for provisioning template management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, template_id: int) -> Optional[ProvisioningTemplate]:
        """Get template by ID."""
        return self.db.query(ProvisioningTemplate).filter(
            ProvisioningTemplate.id == template_id
        ).first()
    
    def get_by_name(self, name: str) -> Optional[ProvisioningTemplate]:
        """Get template by name."""
        return self.db.query(ProvisioningTemplate).filter(
            ProvisioningTemplate.name == name
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ProvisioningTemplate]:
        """Get all templates with pagination."""
        return self.db.query(ProvisioningTemplate).offset(skip).limit(limit).all()
    
    def get_active(self) -> List[ProvisioningTemplate]:
        """Get all active templates."""
        return self.db.query(ProvisioningTemplate).filter(
            ProvisioningTemplate.is_active == True
        ).all()
    
    def get_default(self) -> Optional[ProvisioningTemplate]:
        """Get the default template."""
        return self.db.query(ProvisioningTemplate).filter(
            ProvisioningTemplate.is_default == True,
            ProvisioningTemplate.is_active == True,
        ).first()
    
    def count(self) -> int:
        """Get total template count."""
        return self.db.query(ProvisioningTemplate).count()
    
    def create(
        self,
        name: str,
        line_profile: str,
        service_profile: str,
        vlan: int,
        description: Optional[str] = None,
        service_port_start: Optional[int] = None,
        additional_params: Optional[dict] = None,
        is_default: bool = False,
        created_by: Optional[str] = None,
    ) -> Tuple[Optional[ProvisioningTemplate], Optional[str]]:
        """
        Create a new provisioning template.
        
        Returns:
            Tuple of (ProvisioningTemplate, error_message)
        """
        # Check if name already exists
        if self.get_by_name(name):
            return None, "Template name already exists"
        
        # If setting as default, unset current default
        if is_default:
            self._unset_default()
        
        template = ProvisioningTemplate(
            name=name,
            description=description,
            line_profile=line_profile,
            service_profile=service_profile,
            vlan=vlan,
            service_port_start=service_port_start,
            additional_params=additional_params,
            is_active=True,
            is_default=is_default,
            created_by=created_by,
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template, None
    
    def update(
        self,
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        line_profile: Optional[str] = None,
        service_profile: Optional[str] = None,
        vlan: Optional[int] = None,
        service_port_start: Optional[int] = None,
        additional_params: Optional[dict] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None,
    ) -> Tuple[Optional[ProvisioningTemplate], Optional[str]]:
        """
        Update a provisioning template.
        
        Returns:
            Tuple of (ProvisioningTemplate, error_message)
        """
        template = self.get_by_id(template_id)
        if not template:
            return None, "Template not found"
        
        # Check name uniqueness if changing
        if name and name != template.name:
            existing = self.get_by_name(name)
            if existing:
                return None, "Template name already exists"
            template.name = name
        
        if description is not None:
            template.description = description
        
        if line_profile is not None:
            template.line_profile = line_profile
        
        if service_profile is not None:
            template.service_profile = service_profile
        
        if vlan is not None:
            template.vlan = vlan
        
        if service_port_start is not None:
            template.service_port_start = service_port_start
        
        if additional_params is not None:
            template.additional_params = additional_params
        
        if is_active is not None:
            template.is_active = is_active
        
        if is_default is not None:
            if is_default:
                self._unset_default()
            template.is_default = is_default
        
        self.db.commit()
        self.db.refresh(template)
        
        return template, None
    
    def delete(self, template_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a provisioning template.
        
        Returns:
            Tuple of (success, error_message)
        """
        template = self.get_by_id(template_id)
        if not template:
            return False, "Template not found"
        
        # Check if template is in use
        if template.usage_count > 0:
            return False, f"Template is in use by {template.usage_count} ONUs"
        
        self.db.delete(template)
        self.db.commit()
        
        return True, None
    
    def set_default(self, template_id: int) -> Tuple[bool, Optional[str]]:
        """
        Set a template as the default.
        
        Returns:
            Tuple of (success, error_message)
        """
        template = self.get_by_id(template_id)
        if not template:
            return False, "Template not found"
        
        if not template.is_active:
            return False, "Cannot set inactive template as default"
        
        # Unset current default
        self._unset_default()
        
        # Set new default
        template.is_default = True
        self.db.commit()
        
        return True, None
    
    def _unset_default(self) -> None:
        """Unset the current default template."""
        current_default = self.get_default()
        if current_default:
            current_default.is_default = False
            self.db.commit()
    
    def search(self, query: str) -> List[ProvisioningTemplate]:
        """Search templates by name or description."""
        search_term = f"%{query}%"
        return self.db.query(ProvisioningTemplate).filter(
            (ProvisioningTemplate.name.ilike(search_term)) |
            (ProvisioningTemplate.description.ilike(search_term))
        ).all()
