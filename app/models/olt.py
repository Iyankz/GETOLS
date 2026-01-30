"""
GETOLS OLT Model
Handles OLT device configuration and credentials.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class OLTType(str, enum.Enum):
    """Supported OLT types."""
    ZTE_C300 = "zte_c300"
    ZTE_C320 = "zte_c320"


class OLT(Base):
    """OLT device model."""
    
    __tablename__ = "olts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # OLT Type
    olt_type = Column(Enum(OLTType), nullable=False)
    
    # Connection settings - Telnet only for ZTE OLT
    ip_address = Column(String(45), nullable=False)  # Supports IPv6
    cli_port = Column(Integer, default=23, nullable=False)  # Telnet port
    
    # CLI credentials (single set for Telnet access)
    cli_username = Column(String(100), nullable=False)
    cli_password_encrypted = Column(Text, nullable=False)  # AES-256-GCM encrypted
    
    # SNMP v2c settings
    snmp_ro_community_encrypted = Column(Text, nullable=False)  # AES-256-GCM encrypted (for monitoring)
    snmp_rw_community_encrypted = Column(Text, nullable=True)   # AES-256-GCM encrypted (for maintenance)
    snmp_port = Column(Integer, default=161, nullable=False)
    
    # Status
    is_enabled = Column(Boolean, default=True, nullable=False)
    last_test_cli = Column(DateTime, nullable=True)
    last_test_snmp = Column(DateTime, nullable=True)
    last_test_cli_success = Column(Boolean, nullable=True)
    last_test_snmp_success = Column(Boolean, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    onus = relationship("ONU", back_populates="olt", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<OLT(id={self.id}, name='{self.name}', type='{self.olt_type.value}')>"
    
    @property
    def type_display(self) -> str:
        """Get human-readable OLT type."""
        type_map = {
            OLTType.ZTE_C300: "ZTE ZXA10 C300",
            OLTType.ZTE_C320: "ZTE ZXA10 C320",
        }
        return type_map.get(self.olt_type, self.olt_type.value)
    
    @property
    def status_display(self) -> str:
        """Get status display string."""
        if not self.is_enabled:
            return "Disabled"
        
        if self.last_test_cli_success and self.last_test_snmp_success:
            return "Online"
        elif self.last_test_cli_success is None:
            return "Not Tested"
        else:
            return "Error"
    
    @property
    def has_snmp_rw(self) -> bool:
        """Check if SNMP RW community is configured."""
        return self.snmp_rw_community_encrypted is not None
