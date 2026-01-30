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


class ConnectionType(str, enum.Enum):
    """Connection type for CLI access."""
    SSH = "ssh"
    TELNET = "telnet"


class OLT(Base):
    """OLT device model."""
    
    __tablename__ = "olts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # OLT Type
    olt_type = Column(Enum(OLTType), nullable=False)
    
    # Connection settings
    ip_address = Column(String(45), nullable=False)  # Supports IPv6
    connection_type = Column(Enum(ConnectionType), default=ConnectionType.SSH, nullable=False)
    
    # Custom ports (for port forwarding support)
    cli_port = Column(Integer, default=22, nullable=False)  # SSH=22, Telnet=23
    
    # Read-Only credentials (for discovery, monitoring)
    ro_username = Column(String(100), nullable=False)
    ro_password_encrypted = Column(Text, nullable=False)  # AES-256-GCM encrypted
    
    # Read-Write credentials (for provisioning)
    rw_username = Column(String(100), nullable=False)
    rw_password_encrypted = Column(Text, nullable=False)  # AES-256-GCM encrypted
    
    # SNMP settings
    snmp_community_encrypted = Column(Text, nullable=False)  # AES-256-GCM encrypted
    snmp_port = Column(Integer, default=161, nullable=False)
    
    # Status
    is_enabled = Column(Boolean, default=True, nullable=False)
    last_test_ro = Column(DateTime, nullable=True)
    last_test_rw = Column(DateTime, nullable=True)
    last_test_snmp = Column(DateTime, nullable=True)
    last_test_ro_success = Column(Boolean, nullable=True)
    last_test_rw_success = Column(Boolean, nullable=True)
    last_test_snmp_success = Column(Boolean, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    onus = relationship("ONU", back_populates="olt", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<OLT(id={self.id}, name='{self.name}', type='{self.olt_type.value}')>"
    
    @property
    def connection_port_default(self) -> int:
        """Get default port based on connection type."""
        return 22 if self.connection_type == ConnectionType.SSH else 23
    
    @property
    def is_ssh(self) -> bool:
        """Check if using SSH connection."""
        return self.connection_type == ConnectionType.SSH
    
    @property
    def is_telnet(self) -> bool:
        """Check if using Telnet connection."""
        return self.connection_type == ConnectionType.TELNET
    
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
        
        if self.last_test_ro_success and self.last_test_rw_success and self.last_test_snmp_success:
            return "Online"
        elif self.last_test_ro_success is None:
            return "Not Tested"
        else:
            return "Error"
