"""
GETOLS ONU Model
Handles ONU device records.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class ONUStatus(str, enum.Enum):
    """ONU operational status."""
    ONLINE = "online"
    OFFLINE = "offline"
    LOW_SIGNAL = "low_signal"
    UNKNOWN = "unknown"


class ONU(Base):
    """ONU device model."""
    
    __tablename__ = "onus"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # OLT reference
    olt_id = Column(Integer, ForeignKey("olts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ONU identification
    serial_number = Column(String(50), nullable=False, index=True)
    pon_port = Column(String(20), nullable=False)  # e.g., "1/1/1"
    onu_id = Column(Integer, nullable=False)  # ONU ID on the PON port
    
    # ONU information
    name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    onu_type = Column(String(50), nullable=True)  # e.g., "F660", "F670L"
    
    # Provisioning info
    line_profile = Column(String(100), nullable=True)
    service_profile = Column(String(100), nullable=True)
    vlan = Column(Integer, nullable=True)
    service_port = Column(Integer, nullable=True)
    
    # Template used (if any)
    template_id = Column(Integer, ForeignKey("provisioning_templates.id", ondelete="SET NULL"), nullable=True)
    
    # Status
    status = Column(Enum(ONUStatus), default=ONUStatus.UNKNOWN, nullable=False)
    is_provisioned = Column(Boolean, default=False, nullable=False)
    
    # Monitoring data (updated via SNMP)
    rx_power = Column(Float, nullable=True)  # dBm
    tx_power = Column(Float, nullable=True)  # dBm
    last_seen = Column(DateTime, nullable=True)
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    provisioned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit
    provisioned_by = Column(String(50), nullable=True)  # Username who provisioned
    
    # Relationships
    olt = relationship("OLT", back_populates="onus")
    template = relationship("ProvisioningTemplate", back_populates="onus")
    
    def __repr__(self) -> str:
        return f"<ONU(id={self.id}, sn='{self.serial_number}', port='{self.pon_port}')>"
    
    @property
    def full_location(self) -> str:
        """Get full ONU location string."""
        return f"{self.pon_port}:{self.onu_id}"
    
    @property
    def status_display(self) -> str:
        """Get human-readable status."""
        status_map = {
            ONUStatus.ONLINE: "Online",
            ONUStatus.OFFLINE: "Offline",
            ONUStatus.LOW_SIGNAL: "Low Signal",
            ONUStatus.UNKNOWN: "Unknown",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def rx_power_display(self) -> str:
        """Get formatted RX power."""
        if self.rx_power is None:
            return "N/A"
        return f"{self.rx_power:.2f} dBm"
    
    @property
    def tx_power_display(self) -> str:
        """Get formatted TX power."""
        if self.tx_power is None:
            return "N/A"
        return f"{self.tx_power:.2f} dBm"
    
    @property
    def signal_quality(self) -> str:
        """Get signal quality indicator based on RX power."""
        if self.rx_power is None:
            return "unknown"
        
        # Typical GPON RX power thresholds
        if self.rx_power >= -25:
            return "good"
        elif self.rx_power >= -27:
            return "fair"
        elif self.rx_power >= -30:
            return "poor"
        else:
            return "critical"
