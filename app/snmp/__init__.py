"""
GETOLS SNMP Module
Handles SNMP v2c read-only monitoring for OLT and ONU.

Uses system snmp tools (snmpget, snmpwalk) via subprocess for maximum compatibility.
"""

from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import subprocess
import shutil
import re

from app.core import settings


def check_snmp_tools() -> Tuple[bool, Optional[str]]:
    """
    Check if SNMP tools (snmpget, snmpwalk) are installed on the system.
    
    This MUST be called before any SNMP operation to ensure tools are available.
    
    Returns:
        Tuple of (available, error_message)
        - (True, None) if tools are available
        - (False, error_message) if tools are missing
    """
    snmpget_path = shutil.which("snmpget")
    snmpwalk_path = shutil.which("snmpwalk")
    
    if not snmpget_path or not snmpwalk_path:
        missing = []
        if not snmpget_path:
            missing.append("snmpget")
        if not snmpwalk_path:
            missing.append("snmpwalk")
        
        return False, f"SNMP tools not found on server ({', '.join(missing)}). Please install the 'snmp' package: sudo apt install snmp"
    
    return True, None


# ZTE GPON MIB OIDs
class ZTEOID:
    """ZTE GPON SNMP OIDs."""
    
    # System OIDs
    SYS_DESCR = "1.3.6.1.2.1.1.1.0"
    SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
    SYS_NAME = "1.3.6.1.2.1.1.5.0"
    
    # ZTE Enterprise OID base
    ZTE_BASE = "1.3.6.1.4.1.3902"
    
    # GPON ONU OIDs (ZTE specific)
    # Note: Actual OIDs may vary by firmware version
    ONU_STATUS_BASE = "1.3.6.1.4.1.3902.1012.3.28.1.1.1"
    ONU_RX_POWER_BASE = "1.3.6.1.4.1.3902.1012.3.50.12.1.1.10"
    ONU_TX_POWER_BASE = "1.3.6.1.4.1.3902.1012.3.50.12.1.1.11"
    
    # PON Port OIDs
    PON_PORT_STATUS = "1.3.6.1.4.1.3902.1012.3.28.1.1.2"
    PON_PORT_ONU_COUNT = "1.3.6.1.4.1.3902.1012.3.28.1.1.5"
    
    # Interface OIDs (standard MIB-II)
    IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
    IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"
    IF_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"
    IF_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16"


@dataclass
class SNMPResult:
    """Result of SNMP operation."""
    success: bool
    value: Any = None
    error: Optional[str] = None


@dataclass
class ONUMonitoringData:
    """ONU monitoring data from SNMP."""
    pon_port: str
    onu_id: int
    status: str
    rx_power: Optional[float] = None
    tx_power: Optional[float] = None


class SNMPManager:
    """
    SNMP Manager for OLT monitoring.
    
    This class provides read-only SNMP operations using system snmp tools.
    SNMP SET operations are explicitly blocked.
    """
    
    def __init__(
        self,
        host: str,
        community: str,
        port: int = 161,
        timeout: int = None,
        retries: int = None,
    ):
        """
        Initialize SNMP Manager.
        
        Args:
            host: OLT IP address
            community: SNMP community string (read-only)
            port: SNMP port (default 161)
            timeout: SNMP timeout in seconds
            retries: Number of retries
        """
        self.host = host
        self.community = community
        self.port = port
        self.timeout = timeout or settings.snmp_timeout
        self.retries = retries or settings.snmp_retries
    
    def _run_snmp_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """
        Run an SNMP command and return the result.
        
        Returns:
            Tuple of (success, output_or_error)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 5  # Add buffer for subprocess overhead
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                error = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                return False, error
                
        except subprocess.TimeoutExpired:
            return False, "SNMP request timed out"
        except FileNotFoundError:
            return False, "snmp tools not installed (snmpget/snmpwalk not found)"
        except Exception as e:
            return False, str(e)
    
    def _parse_snmp_value(self, output: str) -> str:
        """
        Parse SNMP output to extract value.
        
        Example outputs:
        - SNMPv2-MIB::sysDescr.0 = STRING: "ZTE ZXA10 C320"
        - iso.3.6.1.2.1.1.1.0 = STRING: "ZTE ZXA10 C320"
        """
        # Match various SNMP output formats
        patterns = [
            r'=\s*STRING:\s*["\']?(.+?)["\']?\s*$',
            r'=\s*INTEGER:\s*(\d+)',
            r'=\s*Gauge32:\s*(\d+)',
            r'=\s*Counter32:\s*(\d+)',
            r'=\s*Counter64:\s*(\d+)',
            r'=\s*Timeticks:\s*\((\d+)\)',
            r'=\s*IpAddress:\s*(.+)',
            r'=\s*OID:\s*(.+)',
            r'=\s*Hex-STRING:\s*(.+)',
            r'=\s*"(.+)"',
            r'=\s*(\S+)\s*$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, return the raw output after '='
        if '=' in output:
            return output.split('=', 1)[1].strip()
        
        return output
    
    def get(self, oid: str) -> SNMPResult:
        """
        Perform SNMP GET operation.
        
        Args:
            oid: OID to query
            
        Returns:
            SNMPResult with value or error
        """
        cmd = [
            "snmpget",
            "-v", "2c",
            "-c", self.community,
            "-t", str(self.timeout),
            "-r", str(self.retries),
            f"{self.host}:{self.port}",
            oid
        ]
        
        success, output = self._run_snmp_command(cmd)
        
        if success:
            # Check for "No Such" errors
            if "No Such" in output or "noSuch" in output.lower():
                return SNMPResult(success=False, error="OID not found")
            
            value = self._parse_snmp_value(output)
            return SNMPResult(success=True, value=value)
        else:
            return SNMPResult(success=False, error=output)
    
    def walk(self, oid: str) -> SNMPResult:
        """
        Perform SNMP WALK operation.
        
        Args:
            oid: Base OID to walk
            
        Returns:
            SNMPResult with list of (oid, value) tuples
        """
        cmd = [
            "snmpwalk",
            "-v", "2c",
            "-c", self.community,
            "-t", str(self.timeout),
            "-r", str(self.retries),
            f"{self.host}:{self.port}",
            oid
        ]
        
        success, output = self._run_snmp_command(cmd)
        
        if success:
            results = []
            for line in output.split('\n'):
                if '=' in line and line.strip():
                    parts = line.split('=', 1)
                    oid_part = parts[0].strip()
                    value = self._parse_snmp_value(line)
                    results.append((oid_part, value))
            
            return SNMPResult(success=True, value=results)
        else:
            return SNMPResult(success=False, error=output)
    
    def get_bulk(self, oid: str, max_repetitions: int = 25) -> SNMPResult:
        """
        Perform SNMP GETBULK operation.
        
        Args:
            oid: Base OID to query
            max_repetitions: Maximum number of results
            
        Returns:
            SNMPResult with list of (oid, value) tuples
        """
        cmd = [
            "snmpbulkget",
            "-v", "2c",
            "-c", self.community,
            "-t", str(self.timeout),
            "-r", str(self.retries),
            "-Cr", str(max_repetitions),
            f"{self.host}:{self.port}",
            oid
        ]
        
        success, output = self._run_snmp_command(cmd)
        
        if success:
            results = []
            for line in output.split('\n'):
                if '=' in line and line.strip():
                    parts = line.split('=', 1)
                    oid_part = parts[0].strip()
                    value = self._parse_snmp_value(line)
                    results.append((oid_part, value))
            
            return SNMPResult(success=True, value=results)
        else:
            # Fall back to walk if bulkget not available
            return self.walk(oid)
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test SNMP connection by querying system description.
        
        IMPORTANT: First checks if SNMP tools are installed on the server.
        If tools are not found, returns error WITHOUT attempting connection.
        
        Returns:
            Tuple of (success, error_message)
        """
        # CRITICAL: Check if SNMP tools are available BEFORE attempting connection
        tools_ok, tools_error = check_snmp_tools()
        if not tools_ok:
            # Do NOT attempt connection - tools are missing
            return False, tools_error
        
        # Tools are available, proceed with connection test
        result = self.get(ZTEOID.SYS_DESCR)
        
        if result.success:
            return True, None
        else:
            return False, result.error
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get basic system information via SNMP.
        
        Returns:
            Dictionary with system info
        """
        info = {
            "description": None,
            "uptime": None,
            "name": None,
        }
        
        # Get system description
        result = self.get(ZTEOID.SYS_DESCR)
        if result.success:
            info["description"] = result.value
        
        # Get system uptime
        result = self.get(ZTEOID.SYS_UPTIME)
        if result.success:
            info["uptime"] = result.value
        
        # Get system name
        result = self.get(ZTEOID.SYS_NAME)
        if result.success:
            info["name"] = result.value
        
        return info
    
    def get_onu_optical_power(self, pon_port: str, onu_id: int) -> Dict[str, Optional[float]]:
        """
        Get ONU optical power levels.
        
        Args:
            pon_port: PON port identifier
            onu_id: ONU ID
            
        Returns:
            Dictionary with rx_power and tx_power (in dBm)
        """
        result = {
            "rx_power": None,
            "tx_power": None,
        }
        
        # Build ONU-specific OID
        # Note: OID construction depends on ZTE firmware version
        try:
            # RX Power
            rx_oid = f"{ZTEOID.ONU_RX_POWER_BASE}.{pon_port.replace('/', '.')}.{onu_id}"
            rx_result = self.get(rx_oid)
            if rx_result.success and rx_result.value:
                try:
                    # Convert from 0.1 dBm units if applicable
                    result["rx_power"] = float(rx_result.value) / 10.0
                except ValueError:
                    pass
            
            # TX Power
            tx_oid = f"{ZTEOID.ONU_TX_POWER_BASE}.{pon_port.replace('/', '.')}.{onu_id}"
            tx_result = self.get(tx_oid)
            if tx_result.success and tx_result.value:
                try:
                    result["tx_power"] = float(tx_result.value) / 10.0
                except ValueError:
                    pass
                    
        except Exception:
            pass
        
        return result
    
    def get_onu_status(self, pon_port: str, onu_id: int) -> Optional[str]:
        """
        Get ONU operational status.
        
        Args:
            pon_port: PON port identifier
            onu_id: ONU ID
            
        Returns:
            Status string or None
        """
        try:
            oid = f"{ZTEOID.ONU_STATUS_BASE}.{pon_port.replace('/', '.')}.{onu_id}"
            result = self.get(oid)
            
            if result.success:
                # Map status codes to strings
                status_map = {
                    "1": "online",
                    "2": "offline",
                    "3": "low_signal",
                }
                return status_map.get(result.value, "unknown")
            
            return None
            
        except Exception:
            return None
    
    # ============================================
    # SNMP SET OPERATIONS - BLOCKED
    # ============================================
    
    def set(self, oid: str, value: Any) -> SNMPResult:
        """
        SNMP SET operation - BLOCKED.
        
        SNMP write operations are not allowed per security policy.
        """
        return SNMPResult(
            success=False,
            error="SNMP SET operations are not allowed. This is a security violation."
        )
    
    def __repr__(self) -> str:
        return f"<SNMPManager(host='{self.host}', port={self.port})>"
