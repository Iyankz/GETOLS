"""
GETOLS Provisioning Template Model
Handles provisioning templates for ONU registration.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProvisioningTemplate(Base):
    """Provisioning template model."""
    
    __tablename__ = "provisioning_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Template configuration
    line_profile = Column(String(100), nullable=False)
    service_profile = Column(String(100), nullable=False)
    vlan = Column(Integer, nullable=False)
    
    # Service port configuration
    service_port_start = Column(Integer, nullable=True)  # For auto-increment
    
    # Additional parameters (JSON for flexibility)
    additional_params = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Default template
    
    # Usage count
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=True)  # Username who created
    
    # Relationships
    onus = relationship("ONU", back_populates="template")
    
    def __repr__(self) -> str:
        return f"<ProvisioningTemplate(id={self.id}, name='{self.name}')>"
    
    @property
    def config_summary(self) -> str:
        """Get configuration summary string."""
        return f"VLAN: {self.vlan}, Line: {self.line_profile}, Service: {self.service_profile}"
    
    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1
    
    def to_dict(self) -> dict:
        """Convert template to dictionary for provisioning."""
        return {
            "line_profile": self.line_profile,
            "service_profile": self.service_profile,
            "vlan": self.vlan,
            "service_port_start": self.service_port_start,
            "additional_params": self.additional_params or {},
        }
