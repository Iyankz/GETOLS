"""
GETOLS Activity Log Model
Handles audit trail for all actions.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActionType(str, enum.Enum):
    """Types of actions that can be logged."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ROLE_CHANGE = "user_role_change"
    
    # OLT management
    OLT_CREATE = "olt_create"
    OLT_UPDATE = "olt_update"
    OLT_DELETE = "olt_delete"
    OLT_ENABLE = "olt_enable"
    OLT_DISABLE = "olt_disable"
    OLT_TEST_RO = "olt_test_ro"
    OLT_TEST_RW = "olt_test_rw"
    OLT_TEST_SNMP = "olt_test_snmp"
    
    # ONU operations
    ONU_DISCOVER = "onu_discover"
    ONU_REGISTER = "onu_register"
    ONU_DELETE = "onu_delete"
    ONU_UPDATE = "onu_update"
    
    # Template management
    TEMPLATE_CREATE = "template_create"
    TEMPLATE_UPDATE = "template_update"
    TEMPLATE_DELETE = "template_delete"
    
    # System
    SYSTEM_SETTING_CHANGE = "system_setting_change"
    
    # Security violations
    SECURITY_VIOLATION = "security_violation"
    ACCESS_DENIED = "access_denied"


class AccessType(str, enum.Enum):
    """Type of OLT access used for the action."""
    RO = "ro"
    RW = "rw"
    SNMP = "snmp"
    NONE = "none"


class ActivityLog(Base):
    """Activity log model for audit trail."""
    
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(50), nullable=False)  # Stored separately in case user is deleted
    role = Column(String(20), nullable=False)
    
    # What
    action = Column(Enum(ActionType), nullable=False, index=True)
    action_detail = Column(Text, nullable=True)  # Human-readable description
    
    # Where
    target_type = Column(String(50), nullable=True)  # e.g., "olt", "onu", "user"
    target_id = Column(Integer, nullable=True)
    target_name = Column(String(100), nullable=True)
    
    # OLT access type used (if applicable)
    access_type = Column(Enum(AccessType), default=AccessType.NONE, nullable=False)
    
    # Result
    success = Column(Integer, nullable=False)  # 1 = success, 0 = failure
    error_message = Column(Text, nullable=True)
    
    # Additional data (JSON for flexibility)
    extra_data = Column(JSON, nullable=True)
    
    # Client info
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    user_agent = Column(String(255), nullable=True)
    
    # When
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, user='{self.username}', action='{self.action.value}')>"
    
    @property
    def success_display(self) -> str:
        """Get success/failure display string."""
        return "Success" if self.success else "Failed"
    
    @property
    def action_display(self) -> str:
        """Get human-readable action name."""
        action_names = {
            ActionType.LOGIN: "User Login",
            ActionType.LOGOUT: "User Logout",
            ActionType.LOGIN_FAILED: "Failed Login Attempt",
            ActionType.PASSWORD_CHANGE: "Password Change",
            ActionType.USER_CREATE: "User Created",
            ActionType.USER_UPDATE: "User Updated",
            ActionType.USER_DELETE: "User Deleted",
            ActionType.USER_ROLE_CHANGE: "User Role Changed",
            ActionType.OLT_CREATE: "OLT Added",
            ActionType.OLT_UPDATE: "OLT Updated",
            ActionType.OLT_DELETE: "OLT Deleted",
            ActionType.OLT_ENABLE: "OLT Enabled",
            ActionType.OLT_DISABLE: "OLT Disabled",
            ActionType.OLT_TEST_RO: "OLT Test (RO)",
            ActionType.OLT_TEST_RW: "OLT Test (RW)",
            ActionType.OLT_TEST_SNMP: "OLT Test (SNMP)",
            ActionType.ONU_DISCOVER: "ONU Discovery",
            ActionType.ONU_REGISTER: "ONU Registered",
            ActionType.ONU_DELETE: "ONU Deleted",
            ActionType.ONU_UPDATE: "ONU Updated",
            ActionType.TEMPLATE_CREATE: "Template Created",
            ActionType.TEMPLATE_UPDATE: "Template Updated",
            ActionType.TEMPLATE_DELETE: "Template Deleted",
            ActionType.SYSTEM_SETTING_CHANGE: "System Setting Changed",
            ActionType.SECURITY_VIOLATION: "Security Violation",
            ActionType.ACCESS_DENIED: "Access Denied",
        }
        return action_names.get(self.action, self.action.value)
    
    @classmethod
    def create_log(
        cls,
        user_id: Optional[int],
        username: str,
        role: str,
        action: ActionType,
        success: bool,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        access_type: AccessType = AccessType.NONE,
        action_detail: Optional[str] = None,
        error_message: Optional[str] = None,
        extra_data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "ActivityLog":
        """Factory method to create activity log entry."""
        return cls(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            success=1 if success else 0,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            access_type=access_type,
            action_detail=action_detail,
            error_message=error_message,
            extra_data=extra_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
