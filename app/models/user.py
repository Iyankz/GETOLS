"""
GETOLS User Model
Handles user accounts and role-based access control.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # Role-based access control
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_operator(self) -> bool:
        """Check if user has operator role."""
        return self.role == UserRole.OPERATOR
    
    @property
    def is_viewer(self) -> bool:
        """Check if user has viewer role."""
        return self.role == UserRole.VIEWER
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role == UserRole.ADMIN
    
    def can_manage_olt(self) -> bool:
        """Check if user can manage OLT configurations."""
        return self.role == UserRole.ADMIN
    
    def can_provision(self) -> bool:
        """Check if user can perform ONU provisioning."""
        return self.role in (UserRole.ADMIN, UserRole.OPERATOR)
    
    def can_discover(self) -> bool:
        """Check if user can perform ONU discovery."""
        return self.role in (UserRole.ADMIN, UserRole.OPERATOR)
    
    def can_view_monitoring(self) -> bool:
        """Check if user can view monitoring data."""
        return True  # All roles can view
    
    def can_manage_templates(self) -> bool:
        """Check if user can manage provisioning templates."""
        return self.role == UserRole.ADMIN
