"""
GETOLS ZTE ZXA10 C320 Adapter
Specific implementation for ZTE C320 OLT.
"""

import re
from typing import List, Optional

from app.adapters.zte.base import ZTEBaseAdapter, ONUDiscoveryResult


class ZTEC320Adapter(ZTEBaseAdapter):
    """
    Adapter for ZTE ZXA10 C320 OLT.
    
    The C320 is a compact GPON OLT typically used in smaller deployments.
    While similar to C300, it has some differences in CLI behavior.
    """
    
    @property
    def model_name(self) -> str:
        return "ZTE ZXA10 C320"
    
    def get_unconfigured_onu_command(self) -> str:
        """Return command to show unconfigured ONUs on C320."""
        return "show gpon onu uncfg"
    
    def parse_unconfigured_onus(self, output: str) -> List[ONUDiscoveryResult]:
        """
        Parse unconfigured ONU output from C320.
        
        Example output format (C320 may have slight variations):
        OnuIndex                Sn              State
        gpon-onu_1/1/1:1        ZTEGC1234567    unknown
        gpon-onu_1/1/2:1        ZTEGC7654321    unknown
        """
        onus = []
        
        # Pattern to match ONU entries
        # C320 format is similar to C300
        pattern = r"gpon-onu_(\d+/\d+/\d+):(\d+)\s+(\S+)\s+(\S+)"
        
        for match in re.finditer(pattern, output):
            pon_port = match.group(1)
            onu_id = int(match.group(2))
            serial_number = match.group(3)
            status = match.group(4)
            
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
        
        type_map = {
            "ZTEG": "ZTE GPON",
            "HWTC": "Huawei",
            "ALCL": "Alcatel",
            "FHTT": "Fiberhome",
            "ZNTS": "ZTE Smart",
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
        Generate commands to register ONU on C320.
        
        The C320 command structure is similar to C300 but may have
        some firmware-specific variations.
        """
        commands = []
        
        # Enter configure mode
        commands.append("configure terminal")
        
        # Enter GPON OLT interface
        commands.append(f"interface gpon-olt_{pon_port}")
        
        # Register ONU
        commands.append(f"onu {onu_id} type auto sn {serial_number}")
        
        # Exit PON interface
        commands.append("exit")
        
        # Configure ONU interface
        commands.append(f"interface gpon-onu_{pon_port}:{onu_id}")
        
        # Set name
        if name:
            safe_name = name.replace(" ", "_")[:32]
            commands.append(f"name {safe_name}")
        
        # Configure TCONT and GEMPORT
        commands.append(f"tcont 1 profile {line_profile}")
        commands.append(f"gemport 1 tcont 1")
        
        # Configure service
        commands.append(f"switchport mode trunk vport 1")
        commands.append(f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}")
        
        # Exit ONU interface
        commands.append("exit")
        
        # Commit and exit
        commands.append("exit")
        
        return commands
    
    def get_delete_onu_commands(self, pon_port: str, onu_id: int) -> List[str]:
        """
        Generate commands to delete ONU on C320.
        """
        commands = []
        
        # Enter configure mode
        commands.append("configure terminal")
        
        # Enter PON interface
        commands.append(f"interface gpon-olt_{pon_port}")
        
        # Remove ONU
        commands.append(f"no onu {onu_id}")
        
        # Exit
        commands.append("exit")
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
        """Parse optical power information for specific ONU."""
        result = {"rx_power": None, "tx_power": None}
        
        # Try multiple patterns as format may vary
        patterns = [
            rf":\s*{onu_id}\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)",
            rf"ONU\s+{onu_id}[^\n]*\n.*?RX:\s*(-?\d+\.?\d*).*?TX:\s*(-?\d+\.?\d*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    result["rx_power"] = float(match.group(1))
                    result["tx_power"] = float(match.group(2))
                    break
                except (ValueError, IndexError):
                    continue
        
        return result
    
    def get_board_info_command(self) -> str:
        """Get command to show board information."""
        return "show card"
    
    def get_running_config_command(self) -> str:
        """Get command to show running configuration."""
        return "show running-config"
