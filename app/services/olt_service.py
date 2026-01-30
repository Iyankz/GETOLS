"""
GETOLS OLT Service
Handles OLT management and connection testing.
"""

from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.olt import OLT, OLTType
from app.core.security import encrypt_credential, decrypt_credential
from app.adapters.zte import get_zte_adapter
from app.snmp import SNMPManager


class OLTService:
    """Service for OLT management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, olt_id: int) -> Optional[OLT]:
        """Get OLT by ID."""
        return self.db.query(OLT).filter(OLT.id == olt_id).first()
    
    def get_by_name(self, name: str) -> Optional[OLT]:
        """Get OLT by name."""
        return self.db.query(OLT).filter(OLT.name == name).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[OLT]:
        """Get all OLTs with pagination."""
        return self.db.query(OLT).offset(skip).limit(limit).all()
    
    def get_enabled(self) -> List[OLT]:
        """Get all enabled OLTs."""
        return self.db.query(OLT).filter(OLT.is_enabled == True).all()
    
    def count(self) -> int:
        """Get total OLT count."""
        return self.db.query(OLT).count()
    
    def create(
        self,
        name: str,
        olt_type: OLTType,
        ip_address: str,
        cli_port: int,
        ro_username: str,
        ro_password: str,
        rw_username: str,
        rw_password: str,
        snmp_ro_community: str,
        snmp_rw_community: Optional[str] = None,
        snmp_port: int = 161,
        description: Optional[str] = None,
    ) -> Tuple[Optional[OLT], Optional[str]]:
        """
        Create a new OLT.
        
        Returns:
            Tuple of (OLT, error_message)
        """
        # Check if name already exists
        if self.get_by_name(name):
            return None, "OLT name already exists"
        
        # Encrypt credentials
        olt = OLT(
            name=name,
            olt_type=olt_type,
            ip_address=ip_address,
            cli_port=cli_port,
            ro_username=ro_username,
            ro_password_encrypted=encrypt_credential(ro_password),
            rw_username=rw_username,
            rw_password_encrypted=encrypt_credential(rw_password),
            snmp_ro_community_encrypted=encrypt_credential(snmp_ro_community),
            snmp_rw_community_encrypted=encrypt_credential(snmp_rw_community) if snmp_rw_community else None,
            snmp_port=snmp_port,
            description=description,
            is_enabled=True,
        )
        
        self.db.add(olt)
        self.db.commit()
        self.db.refresh(olt)
        
        return olt, None
    
    def update(
        self,
        olt_id: int,
        name: Optional[str] = None,
        olt_type: Optional[OLTType] = None,
        ip_address: Optional[str] = None,
        cli_port: Optional[int] = None,
        ro_username: Optional[str] = None,
        ro_password: Optional[str] = None,
        rw_username: Optional[str] = None,
        rw_password: Optional[str] = None,
        snmp_ro_community: Optional[str] = None,
        snmp_rw_community: Optional[str] = None,
        snmp_port: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Tuple[Optional[OLT], Optional[str]]:
        """
        Update OLT information.
        
        Returns:
            Tuple of (OLT, error_message)
        """
        olt = self.get_by_id(olt_id)
        if not olt:
            return None, "OLT not found"
        
        # Check name uniqueness if changing
        if name and name != olt.name:
            existing = self.get_by_name(name)
            if existing:
                return None, "OLT name already exists"
            olt.name = name
        
        if olt_type is not None:
            olt.olt_type = olt_type
        
        if ip_address is not None:
            olt.ip_address = ip_address
        
        if cli_port is not None:
            olt.cli_port = cli_port
        
        if ro_username is not None:
            olt.ro_username = ro_username
        
        if ro_password is not None:
            olt.ro_password_encrypted = encrypt_credential(ro_password)
        
        if rw_username is not None:
            olt.rw_username = rw_username
        
        if rw_password is not None:
            olt.rw_password_encrypted = encrypt_credential(rw_password)
        
        if snmp_ro_community is not None:
            olt.snmp_ro_community_encrypted = encrypt_credential(snmp_ro_community)
        
        if snmp_rw_community is not None:
            olt.snmp_rw_community_encrypted = encrypt_credential(snmp_rw_community) if snmp_rw_community else None
        
        if snmp_port is not None:
            olt.snmp_port = snmp_port
        
        if description is not None:
            olt.description = description
        
        self.db.commit()
        self.db.refresh(olt)
        
        return olt, None
    
    def delete(self, olt_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete an OLT.
        
        Returns:
            Tuple of (success, error_message)
        """
        olt = self.get_by_id(olt_id)
        if not olt:
            return False, "OLT not found"
        
        self.db.delete(olt)
        self.db.commit()
        
        return True, None
    
    def enable(self, olt_id: int) -> Tuple[bool, Optional[str]]:
        """Enable an OLT."""
        olt = self.get_by_id(olt_id)
        if not olt:
            return False, "OLT not found"
        
        olt.is_enabled = True
        self.db.commit()
        
        return True, None
    
    def disable(self, olt_id: int) -> Tuple[bool, Optional[str]]:
        """Disable an OLT."""
        olt = self.get_by_id(olt_id)
        if not olt:
            return False, "OLT not found"
        
        olt.is_enabled = False
        self.db.commit()
        
        return True, None
    
    def test_ro_connection(self, olt_id: int) -> Tuple[bool, Optional[str]]:
        """
        Test Read-Only CLI connection to OLT via Telnet.
        
        Returns:
            Tuple of (success, error_message)
        """
        olt = self.get_by_id(olt_id)
        if not olt:
            return False, "OLT not found"
        
        try:
            # Decrypt credentials
            password = decrypt_credential(olt.ro_password_encrypted)
            
            # Get appropriate adapter (Telnet only)
            adapter = get_zte_adapter(
                olt_type=olt.olt_type,
                host=olt.ip_address,
                port=olt.cli_port,
                username=olt.ro_username,
                password=password,
                connection_type="telnet",
            )
            
            # Test connection
            success, error = adapter.test_connection()
            
            # Update test result
            olt.last_test_ro = datetime.utcnow()
            olt.last_test_ro_success = success
            self.db.commit()
            
            return success, error
            
        except Exception as e:
            olt.last_test_ro = datetime.utcnow()
            olt.last_test_ro_success = False
            self.db.commit()
            return False, str(e)
    
    def test_rw_connection(self, olt_id: int) -> Tuple[bool, Optional[str]]:
        """
        Test Read-Write CLI connection to OLT via Telnet.
        
        Returns:
            Tuple of (success, error_message)
        """
        olt = self.get_by_id(olt_id)
        if not olt:
            return False, "OLT not found"
        
        try:
            # Decrypt credentials
            password = decrypt_credential(olt.rw_password_encrypted)
            
            # Get appropriate adapter (Telnet only)
            adapter = get_zte_adapter(
                olt_type=olt.olt_type,
                host=olt.ip_address,
                port=olt.cli_port,
                username=olt.rw_username,
                password=password,
                connection_type="telnet",
            )
            
            # Test connection
            success, error = adapter.test_connection()
            
            # Update test result
            olt.last_test_rw = datetime.utcnow()
            olt.last_test_rw_success = success
            self.db.commit()
            
            return success, error
            
        except Exception as e:
            olt.last_test_rw = datetime.utcnow()
            olt.last_test_rw_success = False
            self.db.commit()
            return False, str(e)
    
    def test_snmp_connection(self, olt_id: int) -> Tuple[bool, Optional[str]]:
        """
        Test SNMP RO connection to OLT.
        
        Returns:
            Tuple of (success, error_message)
        """
        olt = self.get_by_id(olt_id)
        if not olt:
            return False, "OLT not found"
        
        try:
            # Decrypt community string (use RO for testing)
            community = decrypt_credential(olt.snmp_ro_community_encrypted)
            
            # Create SNMP manager
            snmp = SNMPManager(
                host=olt.ip_address,
                community=community,
                port=olt.snmp_port,
            )
            
            # Test connection
            success, error = snmp.test_connection()
            
            # Update test result
            olt.last_test_snmp = datetime.utcnow()
            olt.last_test_snmp_success = success
            self.db.commit()
            
            return success, error
            
        except Exception as e:
            olt.last_test_snmp = datetime.utcnow()
            olt.last_test_snmp_success = False
            self.db.commit()
            return False, str(e)
    
    def get_ro_adapter(self, olt: OLT):
        """
        Get a Read-Only adapter for an OLT.
        
        This should be used for discovery and monitoring operations.
        Uses Telnet connection.
        """
        password = decrypt_credential(olt.ro_password_encrypted)
        
        return get_zte_adapter(
            olt_type=olt.olt_type,
            host=olt.ip_address,
            port=olt.cli_port,
            username=olt.ro_username,
            password=password,
            connection_type="telnet",
        )
    
    def get_rw_adapter(self, olt: OLT):
        """
        Get a Read-Write adapter for an OLT.
        
        This should be used for provisioning operations only.
        Uses Telnet connection.
        """
        password = decrypt_credential(olt.rw_password_encrypted)
        
        return get_zte_adapter(
            olt_type=olt.olt_type,
            host=olt.ip_address,
            port=olt.cli_port,
            username=olt.rw_username,
            password=password,
            connection_type="telnet",
        )
    
    def get_snmp_ro_manager(self, olt: OLT) -> SNMPManager:
        """
        Get SNMP RO manager for an OLT.
        
        Used for monitoring operations.
        """
        community = decrypt_credential(olt.snmp_ro_community_encrypted)
        
        return SNMPManager(
            host=olt.ip_address,
            community=community,
            port=olt.snmp_port,
        )
    
    def get_snmp_rw_manager(self, olt: OLT) -> Optional[SNMPManager]:
        """
        Get SNMP RW manager for an OLT.
        
        Used for limited maintenance operations (ONU reset, etc).
        Returns None if SNMP RW is not configured.
        
        WARNING: All SNMP RW usage must be logged!
        """
        if not olt.snmp_rw_community_encrypted:
            return None
        
        community = decrypt_credential(olt.snmp_rw_community_encrypted)
        
        return SNMPManager(
            host=olt.ip_address,
            community=community,
            port=olt.snmp_port,
        )
