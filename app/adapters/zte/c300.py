"""
GETOLS ZTE ZXA10 C300 Adapter
Specific implementation for ZTE C300 OLT.
"""

import re
from typing import List, Optional

from app.adapters.zte.base import ZTEBaseAdapter, ONUDiscoveryResult


class ZTEC300Adapter(ZTEBaseAdapter):
    """
    Adapter for ZTE ZXA10 C300 OLT.
    
    The C300 is a high-density GPON OLT supporting up to 64 PON ports.
    """
    
    @property
    def model_name(self) -> str:
        return "ZTE ZXA10 C300"
    
    def get_unconfigured_onu_command(self) -> str:
        """Return command to show unconfigured ONUs on C300."""
        return "show gpon onu uncfg"
    
    def parse_unconfigured_onus(self, output: str) -> List[ONUDiscoveryResult]:
        """
        Parse unconfigured ONU output from C300.
        
        Example output format:
        OnuIndex        Sn              State
        gpon-onu_1/1/1:1    ZTEGC1234567    initial
        gpon-onu_1/1/1:2    ZTEGC7654321    initial
        """
        onus = []
        
        # Pattern to match ONU entries
        # Format: gpon-onu_<slot>/<card>/<port>:<onu_id>    <serial>    <state>
        pattern = r"gpon-onu_(\d+/\d+/\d+):(\d+)\s+(\S+)\s+(\S+)"
        
        for match in re.finditer(pattern, output):
            pon_port = match.group(1)  # e.g., "1/1/1"
            onu_id = int(match.group(2))
            serial_number = match.group(3)
            status = match.group(4)
            
            # Try to determine ONU type from serial number prefix
            onu_type = self._detect_onu_type(serial_number)
            
            onus.append(ONUDiscoveryResult(
                pon_port=pon_port,
                onu_id=onu_id,
                serial_number=serial_number,
                onu_type=onu_type,
                status=status,
            ))
        
        return onus
    
    def _detect_onu_type(self, serial_number: str) -> str:
        """Detect ONU type from serial number prefix."""
        sn_upper = serial_number.upper()
        
        # Common ZTE ONU serial number prefixes
        type_map = {
            "ZTEG": "ZTE GPON",
            "HWTC": "Huawei",
            "ALCL": "Alcatel",
            "FHTT": "Fiberhome",
        }
        
        for prefix, onu_type in type_map.items():
            if sn_upper.startswith(prefix):
                return onu_type
        
        return "Unknown"
    
    def get_register_onu_commands(
        self,
        pon_port: str,
        onu_id: int,
        serial_number: str,
        name: str,
        line_profile: str,
        service_profile: str,
        vlan: int,
        service_port: Optional[int] = None,
    ) -> List[str]:
        """
        Generate commands to register ONU on C300.
        
        Args:
            pon_port: PON port (e.g., "1/1/1")
            onu_id: ONU ID on the PON port
            serial_number: ONU serial number
            name: ONU name/description
            line_profile: GPON line profile name
            service_profile: GPON service profile name
            vlan: Service VLAN
            service_port: Service port ID (optional, auto-generate if None)
        """
        commands = []
        
        # Enter configure mode
        commands.append("configure terminal")
        
        # Enter interface mode for PON port
        commands.append(f"interface gpon-olt_{pon_port}")
        
        # Register ONU with serial number
        commands.append(f"onu {onu_id} type auto sn {serial_number}")
        
        # Exit interface mode
        commands.append("exit")
        
        # Enter ONU interface mode
        commands.append(f"interface gpon-onu_{pon_port}:{onu_id}")
        
        # Set ONU name
        if name:
            safe_name = name.replace(" ", "_")[:32]  # Limit to 32 chars
            commands.append(f"name {safe_name}")
        
        # Apply profiles
        commands.append(f"tcont 1 profile {line_profile}")
        commands.append(f"gemport 1 tcont 1")
        
        # Configure service port
        commands.append(f"switchport mode trunk vport 1")
        commands.append(f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}")
        
        # Exit ONU interface
        commands.append("exit")
        
        # Exit configure mode
        commands.append("exit")
        
        return commands
    
    def get_delete_onu_commands(self, pon_port: str, onu_id: int) -> List[str]:
        """
        Generate commands to delete ONU on C300.
        
        Args:
            pon_port: PON port (e.g., "1/1/1")
            onu_id: ONU ID on the PON port
        """
        commands = []
        
        # Enter configure mode
        commands.append("configure terminal")
        
        # Enter interface mode for PON port
        commands.append(f"interface gpon-olt_{pon_port}")
        
        # Delete ONU
        commands.append(f"no onu {onu_id}")
        
        # Exit interface mode
        commands.append("exit")
        
        # Exit configure mode
        commands.append("exit")
        
        return commands
    
    def get_onu_status_command(self, pon_port: str, onu_id: int) -> str:
        """Get command to check ONU status."""
        return f"show gpon onu state gpon-olt_{pon_port}"
    
    def get_onu_info_command(self, pon_port: str, onu_id: int) -> str:
        """Get command to show ONU information."""
        return f"show gpon onu detail-info gpon-onu_{pon_port}:{onu_id}"
    
    def get_pon_power_command(self, pon_port: str) -> str:
        """Get command to show optical power levels."""
        return f"show gpon onu optical-info gpon-olt_{pon_port}"
    
    def parse_onu_optical_info(self, output: str, onu_id: int) -> dict:
        """
        Parse optical power information for specific ONU.
        
        Returns dict with rx_power and tx_power.
        """
        result = {"rx_power": None, "tx_power": None}
        
        # Pattern varies by firmware version
        # Common format: ONU_ID  RX_POWER  TX_POWER
        pattern = rf":\s*{onu_id}\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)"
        
        match = re.search(pattern, output)
        if match:
            try:
                result["rx_power"] = float(match.group(1))
                result["tx_power"] = float(match.group(2))
            except ValueError:
                pass
        
        return result
