"""
GETOLS ZTE Base Adapter
Base class for all ZTE OLT adapters with SSH/Telnet support.
"""

import re
import time
import socket
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import paramiko

from app.core import settings


class ConnectionMode(Enum):
    """OLT connection mode."""
    RO = "ro"  # Read-Only
    RW = "rw"  # Read-Write


@dataclass
class ONUDiscoveryResult:
    """Result of ONU discovery."""
    pon_port: str
    onu_id: int
    serial_number: str
    onu_type: str
    status: str


@dataclass
class CommandResult:
    """Result of CLI command execution."""
    success: bool
    output: str
    error: Optional[str] = None


class ZTEBaseAdapter(ABC):
    """
    Base adapter for ZTE OLT devices.
    Implements common functionality for SSH/Telnet connections.
    """
    
    # CLI prompts for ZTE
    PROMPT_PATTERNS = [
        r"[>#]\s*$",          # Standard prompt
        r"\(config\)#\s*$",   # Config mode
        r"\(gpon-olt\)#\s*$", # GPON OLT mode
        r"\(gpon-onu\)#\s*$", # GPON ONU mode
    ]
    
    # Command timeouts
    DEFAULT_CONNECT_TIMEOUT = settings.olt_connection_timeout
    DEFAULT_COMMAND_TIMEOUT = settings.olt_command_timeout
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        connection_type: str = "ssh",
        connect_timeout: int = None,
        command_timeout: int = None,
    ):
        """
        Initialize ZTE adapter.
        
        Args:
            host: OLT IP address
            port: CLI port (SSH/Telnet)
            username: Login username
            password: Login password
            connection_type: "ssh" or "telnet"
            connect_timeout: Connection timeout in seconds
            command_timeout: Command execution timeout in seconds
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection_type = connection_type.lower()
        self.connect_timeout = connect_timeout or self.DEFAULT_CONNECT_TIMEOUT
        self.command_timeout = command_timeout or self.DEFAULT_COMMAND_TIMEOUT
        
        # Connection objects
        self._ssh_client: Optional[paramiko.SSHClient] = None
        self._ssh_channel: Optional[paramiko.Channel] = None
        self._telnet_client = None
        self._connected = False
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the OLT model name."""
        pass
    
    @abstractmethod
    def get_unconfigured_onu_command(self) -> str:
        """Return the command to show unconfigured ONUs."""
        pass
    
    @abstractmethod
    def parse_unconfigured_onus(self, output: str) -> List[ONUDiscoveryResult]:
        """Parse the output of unconfigured ONU command."""
        pass
    
    @abstractmethod
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
        """Return commands to register an ONU."""
        pass
    
    @abstractmethod
    def get_delete_onu_commands(self, pon_port: str, onu_id: int) -> List[str]:
        """Return commands to delete an ONU."""
        pass
    
    def connect(self) -> bool:
        """
        Establish connection to OLT.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            if self.connection_type == "ssh":
                return self._connect_ssh()
            else:
                return self._connect_telnet()
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to OLT: {str(e)}")
    
    def _connect_ssh(self) -> bool:
        """Establish SSH connection."""
        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            self._ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.connect_timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            
            # Get interactive shell
            self._ssh_channel = self._ssh_client.invoke_shell(
                width=200,
                height=50,
            )
            self._ssh_channel.settimeout(self.command_timeout)
            
            # Wait for initial prompt
            self._read_until_prompt()
            
            self._connected = True
            return True
            
        except paramiko.AuthenticationException:
            raise ConnectionError("Authentication failed")
        except paramiko.SSHException as e:
            raise ConnectionError(f"SSH error: {str(e)}")
        except socket.timeout:
            raise ConnectionError("Connection timeout")
        except Exception as e:
            raise ConnectionError(f"Connection error: {str(e)}")
    
    def _connect_telnet(self) -> bool:
        """Establish Telnet connection."""
        import telnetlib
        
        try:
            self._telnet_client = telnetlib.Telnet(
                self.host,
                self.port,
                timeout=self.connect_timeout,
            )
            
            # Wait for login prompt and send credentials
            self._telnet_client.read_until(b"Username:", timeout=self.connect_timeout)
            self._telnet_client.write(self.username.encode() + b"\n")
            
            self._telnet_client.read_until(b"Password:", timeout=self.connect_timeout)
            self._telnet_client.write(self.password.encode() + b"\n")
            
            # Wait for prompt
            time.sleep(1)
            self._read_until_prompt_telnet()
            
            self._connected = True
            return True
            
        except socket.timeout:
            raise ConnectionError("Connection timeout")
        except Exception as e:
            raise ConnectionError(f"Telnet error: {str(e)}")
    
    def disconnect(self) -> None:
        """Close connection to OLT."""
        try:
            if self._ssh_channel:
                self._ssh_channel.close()
            if self._ssh_client:
                self._ssh_client.close()
            if self._telnet_client:
                self._telnet_client.close()
        except Exception:
            pass
        finally:
            self._ssh_client = None
            self._ssh_channel = None
            self._telnet_client = None
            self._connected = False
    
    def execute_command(self, command: str) -> CommandResult:
        """
        Execute a CLI command on the OLT.
        
        Args:
            command: Command to execute
            
        Returns:
            CommandResult with output or error
        """
        if not self._connected:
            return CommandResult(success=False, output="", error="Not connected to OLT")
        
        try:
            if self.connection_type == "ssh":
                output = self._execute_ssh(command)
            else:
                output = self._execute_telnet(command)
            
            return CommandResult(success=True, output=output)
            
        except Exception as e:
            return CommandResult(success=False, output="", error=str(e))
    
    def _execute_ssh(self, command: str) -> str:
        """Execute command via SSH."""
        if not self._ssh_channel:
            raise RuntimeError("SSH channel not available")
        
        # Clear any pending output
        while self._ssh_channel.recv_ready():
            self._ssh_channel.recv(4096)
        
        # Send command
        self._ssh_channel.send(command + "\n")
        
        # Read output until prompt
        output = self._read_until_prompt()
        
        # Remove the command echo from output
        lines = output.split("\n")
        if lines and command in lines[0]:
            lines = lines[1:]
        
        return "\n".join(lines).strip()
    
    def _execute_telnet(self, command: str) -> str:
        """Execute command via Telnet."""
        if not self._telnet_client:
            raise RuntimeError("Telnet client not available")
        
        self._telnet_client.write(command.encode() + b"\n")
        output = self._read_until_prompt_telnet()
        
        # Remove command echo
        lines = output.split("\n")
        if lines and command in lines[0]:
            lines = lines[1:]
        
        return "\n".join(lines).strip()
    
    def _read_until_prompt(self, timeout: int = None) -> str:
        """Read SSH output until prompt is detected."""
        timeout = timeout or self.command_timeout
        output = ""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("Command timeout")
            
            if self._ssh_channel.recv_ready():
                chunk = self._ssh_channel.recv(4096).decode("utf-8", errors="ignore")
                output += chunk
                
                # Check for prompt
                for pattern in self.PROMPT_PATTERNS:
                    if re.search(pattern, output):
                        return output
            
            time.sleep(0.1)
    
    def _read_until_prompt_telnet(self, timeout: int = None) -> str:
        """Read Telnet output until prompt is detected."""
        timeout = timeout or self.command_timeout
        
        # Build regex pattern for prompts
        pattern = b"(" + b"|".join(p.encode() for p in self.PROMPT_PATTERNS) + b")"
        
        try:
            _, _, output = self._telnet_client.expect([pattern], timeout=timeout)
            return output.decode("utf-8", errors="ignore")
        except EOFError:
            raise ConnectionError("Connection closed by OLT")
    
    def execute_commands(self, commands: List[str]) -> List[CommandResult]:
        """
        Execute multiple commands sequentially.
        
        Args:
            commands: List of commands to execute
            
        Returns:
            List of CommandResult for each command
        """
        results = []
        for cmd in commands:
            result = self.execute_command(cmd)
            results.append(result)
            if not result.success:
                # Stop on first failure for safe operation
                break
        return results
    
    def discover_onus(self) -> Tuple[bool, List[ONUDiscoveryResult], Optional[str]]:
        """
        Discover unconfigured ONUs.
        
        Returns:
            Tuple of (success, list of discovered ONUs, error message)
        """
        cmd = self.get_unconfigured_onu_command()
        result = self.execute_command(cmd)
        
        if not result.success:
            return False, [], result.error
        
        try:
            onus = self.parse_unconfigured_onus(result.output)
            return True, onus, None
        except Exception as e:
            return False, [], f"Failed to parse ONU list: {str(e)}"
    
    def register_onu(
        self,
        pon_port: str,
        onu_id: int,
        serial_number: str,
        name: str,
        line_profile: str,
        service_profile: str,
        vlan: int,
        service_port: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Register an ONU.
        
        Returns:
            Tuple of (success, error message)
        """
        commands = self.get_register_onu_commands(
            pon_port=pon_port,
            onu_id=onu_id,
            serial_number=serial_number,
            name=name,
            line_profile=line_profile,
            service_profile=service_profile,
            vlan=vlan,
            service_port=service_port,
        )
        
        results = self.execute_commands(commands)
        
        # Check for failures
        for i, result in enumerate(results):
            if not result.success:
                return False, f"Command failed at step {i+1}: {result.error}"
            
            # Check for error messages in output
            if self._check_error_in_output(result.output):
                return False, f"OLT error at step {i+1}: {result.output}"
        
        return True, None
    
    def delete_onu(self, pon_port: str, onu_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete an ONU.
        
        Returns:
            Tuple of (success, error message)
        """
        commands = self.get_delete_onu_commands(pon_port, onu_id)
        results = self.execute_commands(commands)
        
        for i, result in enumerate(results):
            if not result.success:
                return False, f"Command failed at step {i+1}: {result.error}"
            
            if self._check_error_in_output(result.output):
                return False, f"OLT error at step {i+1}: {result.output}"
        
        return True, None
    
    def _check_error_in_output(self, output: str) -> bool:
        """Check if output contains error indicators."""
        error_patterns = [
            r"error",
            r"invalid",
            r"failed",
            r"not found",
            r"does not exist",
            r"unknown command",
        ]
        
        output_lower = output.lower()
        for pattern in error_patterns:
            if re.search(pattern, output_lower):
                return True
        return False
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test connection to OLT.
        
        Returns:
            Tuple of (success, error message)
        """
        try:
            self.connect()
            
            # Try a simple command
            result = self.execute_command("show version")
            
            self.disconnect()
            
            if result.success:
                return True, None
            else:
                return False, result.error
                
        except Exception as e:
            self.disconnect()
            return False, str(e)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
