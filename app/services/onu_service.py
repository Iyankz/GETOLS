"""
GETOLS ONU Service
Handles ONU discovery, provisioning, and monitoring.
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.olt import OLT
from app.models.onu import ONU, ONUStatus
from app.models.template import ProvisioningTemplate
from app.services.olt_service import OLTService
from app.adapters.zte.base import ONUDiscoveryResult


class ONUService:
    """Service for ONU operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.olt_service = OLTService(db)
    
    def get_by_id(self, onu_id: int) -> Optional[ONU]:
        """Get ONU by ID."""
        return self.db.query(ONU).filter(ONU.id == onu_id).first()
    
    def get_by_serial(self, serial_number: str) -> Optional[ONU]:
        """Get ONU by serial number."""
        return self.db.query(ONU).filter(ONU.serial_number == serial_number).first()
    
    def get_by_olt(self, olt_id: int) -> List[ONU]:
        """Get all ONUs for an OLT."""
        return self.db.query(ONU).filter(ONU.olt_id == olt_id).all()
    
    def get_by_olt_and_location(
        self,
        olt_id: int,
        pon_port: str,
        onu_id: int,
    ) -> Optional[ONU]:
        """Get ONU by OLT and location."""
        return self.db.query(ONU).filter(
            ONU.olt_id == olt_id,
            ONU.pon_port == pon_port,
            ONU.onu_id == onu_id,
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ONU]:
        """Get all ONUs with pagination."""
        return self.db.query(ONU).offset(skip).limit(limit).all()
    
    def get_provisioned(self, olt_id: Optional[int] = None) -> List[ONU]:
        """Get all provisioned ONUs."""
        query = self.db.query(ONU).filter(ONU.is_provisioned == True)
        if olt_id:
            query = query.filter(ONU.olt_id == olt_id)
        return query.all()
    
    def count(self, olt_id: Optional[int] = None) -> int:
        """Get ONU count."""
        query = self.db.query(ONU)
        if olt_id:
            query = query.filter(ONU.olt_id == olt_id)
        return query.count()
    
    def count_by_status(self, status: ONUStatus, olt_id: Optional[int] = None) -> int:
        """Get ONU count by status."""
        query = self.db.query(ONU).filter(ONU.status == status)
        if olt_id:
            query = query.filter(ONU.olt_id == olt_id)
        return query.count()
    
    def discover(self, olt_id: int) -> Tuple[bool, List[ONUDiscoveryResult], Optional[str]]:
        """
        Discover unconfigured ONUs on an OLT.
        
        Uses RO (Read-Only) credentials.
        
        Returns:
            Tuple of (success, list of discovered ONUs, error_message)
        """
        olt = self.olt_service.get_by_id(olt_id)
        if not olt:
            return False, [], "OLT not found"
        
        if not olt.is_enabled:
            return False, [], "OLT is disabled"
        
        try:
            # Use RO adapter for discovery
            adapter = self.olt_service.get_ro_adapter(olt)
            
            with adapter:
                success, onus, error = adapter.discover_onus()
            
            return success, onus, error
            
        except Exception as e:
            return False, [], str(e)
    
    def register(
        self,
        olt_id: int,
        pon_port: str,
        onu_id: int,
        serial_number: str,
        name: str,
        template_id: Optional[int] = None,
        line_profile: Optional[str] = None,
        service_profile: Optional[str] = None,
        vlan: Optional[int] = None,
        service_port: Optional[int] = None,
        provisioned_by: Optional[str] = None,
    ) -> Tuple[Optional[ONU], Optional[str]]:
        """
        Register (provision) an ONU.
        
        Uses RW (Read-Write) credentials.
        
        Args:
            olt_id: OLT ID
            pon_port: PON port (e.g., "1/1/1")
            onu_id: ONU ID on the PON port
            serial_number: ONU serial number
            name: ONU name/description
            template_id: Provisioning template ID (optional)
            line_profile: Override line profile (optional)
            service_profile: Override service profile (optional)
            vlan: Override VLAN (optional)
            service_port: Override service port (optional)
            provisioned_by: Username who performed provisioning
            
        Returns:
            Tuple of (ONU, error_message)
        """
        olt = self.olt_service.get_by_id(olt_id)
        if not olt:
            return None, "OLT not found"
        
        if not olt.is_enabled:
            return None, "OLT is disabled"
        
        # Check if ONU already exists
        existing = self.get_by_serial(serial_number)
        if existing and existing.is_provisioned:
            return None, f"ONU {serial_number} is already provisioned"
        
        # Get template if specified
        template = None
        if template_id:
            template = self.db.query(ProvisioningTemplate).filter(
                ProvisioningTemplate.id == template_id
            ).first()
            
            if not template:
                return None, "Provisioning template not found"
            
            if not template.is_active:
                return None, "Provisioning template is inactive"
        
        # Determine final parameters (override template if specified)
        final_line_profile = line_profile or (template.line_profile if template else None)
        final_service_profile = service_profile or (template.service_profile if template else None)
        final_vlan = vlan or (template.vlan if template else None)
        
        # Validate required parameters
        if not final_line_profile:
            return None, "Line profile is required"
        if not final_service_profile:
            return None, "Service profile is required"
        if not final_vlan:
            return None, "VLAN is required"
        
        try:
            # Use RW adapter for provisioning
            adapter = self.olt_service.get_rw_adapter(olt)
            
            with adapter:
                success, error = adapter.register_onu(
                    pon_port=pon_port,
                    onu_id=onu_id,
                    serial_number=serial_number,
                    name=name,
                    line_profile=final_line_profile,
                    service_profile=final_service_profile,
                    vlan=final_vlan,
                    service_port=service_port,
                )
            
            if not success:
                return None, error
            
            # Create or update ONU record
            onu = existing or ONU(
                olt_id=olt_id,
                serial_number=serial_number,
                pon_port=pon_port,
                onu_id=onu_id,
            )
            
            onu.name = name
            onu.line_profile = final_line_profile
            onu.service_profile = final_service_profile
            onu.vlan = final_vlan
            onu.service_port = service_port
            onu.template_id = template_id
            onu.is_provisioned = True
            onu.provisioned_at = datetime.utcnow()
            onu.provisioned_by = provisioned_by
            onu.status = ONUStatus.ONLINE
            
            if not existing:
                self.db.add(onu)
            
            # Update template usage count
            if template:
                template.increment_usage()
            
            self.db.commit()
            self.db.refresh(onu)
            
            return onu, None
            
        except Exception as e:
            self.db.rollback()
            return None, str(e)
    
    def delete_onu(
        self,
        onu_id: int,
        delete_from_olt: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete an ONU.
        
        Uses RW (Read-Write) credentials if deleting from OLT.
        
        Args:
            onu_id: ONU database ID
            delete_from_olt: Whether to also delete from OLT
            
        Returns:
            Tuple of (success, error_message)
        """
        onu = self.get_by_id(onu_id)
        if not onu:
            return False, "ONU not found"
        
        if delete_from_olt and onu.is_provisioned:
            olt = self.olt_service.get_by_id(onu.olt_id)
            if not olt:
                return False, "OLT not found"
            
            if not olt.is_enabled:
                return False, "OLT is disabled"
            
            try:
                # Use RW adapter for deletion
                adapter = self.olt_service.get_rw_adapter(olt)
                
                with adapter:
                    success, error = adapter.delete_onu(
                        pon_port=onu.pon_port,
                        onu_id=onu.onu_id,
                    )
                
                if not success:
                    return False, error
                    
            except Exception as e:
                return False, str(e)
        
        # Delete from database
        self.db.delete(onu)
        self.db.commit()
        
        return True, None
    
    def update_monitoring_data(
        self,
        onu_id: int,
        status: Optional[ONUStatus] = None,
        rx_power: Optional[float] = None,
        tx_power: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Update ONU monitoring data.
        
        Returns:
            Tuple of (success, error_message)
        """
        onu = self.get_by_id(onu_id)
        if not onu:
            return False, "ONU not found"
        
        if status is not None:
            onu.status = status
        
        if rx_power is not None:
            onu.rx_power = rx_power
        
        if tx_power is not None:
            onu.tx_power = tx_power
        
        onu.last_seen = datetime.utcnow()
        
        self.db.commit()
        
        return True, None
    
    def refresh_onu_status(self, olt_id: int) -> Tuple[int, int]:
        """
        Refresh status for all ONUs on an OLT via SNMP.
        
        Returns:
            Tuple of (updated_count, failed_count)
        """
        olt = self.olt_service.get_by_id(olt_id)
        if not olt:
            return 0, 0
        
        onus = self.get_by_olt(olt_id)
        if not onus:
            return 0, 0
        
        try:
            snmp = self.olt_service.get_snmp_manager(olt)
            
            updated = 0
            failed = 0
            
            for onu in onus:
                try:
                    # Get optical power
                    power_data = snmp.get_onu_optical_power(onu.pon_port, onu.onu_id)
                    
                    # Get status
                    status_str = snmp.get_onu_status(onu.pon_port, onu.onu_id)
                    status = ONUStatus(status_str) if status_str else None
                    
                    # Update ONU
                    self.update_monitoring_data(
                        onu_id=onu.id,
                        status=status,
                        rx_power=power_data.get("rx_power"),
                        tx_power=power_data.get("tx_power"),
                    )
                    
                    updated += 1
                    
                except Exception:
                    failed += 1
            
            return updated, failed
            
        except Exception:
            return 0, len(onus)
    
    def search(self, query: str, olt_id: Optional[int] = None) -> List[ONU]:
        """Search ONUs by serial number or name."""
        search_term = f"%{query}%"
        db_query = self.db.query(ONU).filter(
            (ONU.serial_number.ilike(search_term)) |
            (ONU.name.ilike(search_term))
        )
        
        if olt_id:
            db_query = db_query.filter(ONU.olt_id == olt_id)
        
        return db_query.all()
