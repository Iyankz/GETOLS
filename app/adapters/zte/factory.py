"""
GETOLS ZTE Adapter Factory
Factory function to get appropriate adapter based on OLT type.
"""

from typing import Type

from app.models.olt import OLTType
from app.adapters.zte.base import ZTEBaseAdapter
from app.adapters.zte.c300 import ZTEC300Adapter
from app.adapters.zte.c320 import ZTEC320Adapter


# Mapping of OLT types to adapter classes
ADAPTER_MAP: dict[OLTType, Type[ZTEBaseAdapter]] = {
    OLTType.ZTE_C300: ZTEC300Adapter,
    OLTType.ZTE_C320: ZTEC320Adapter,
}


def get_zte_adapter(
    olt_type: OLTType,
    host: str,
    port: int,
    username: str,
    password: str,
    connection_type: str = "ssh",
    connect_timeout: int = None,
    command_timeout: int = None,
) -> ZTEBaseAdapter:
    """
    Factory function to create appropriate ZTE adapter based on OLT type.
    
    Args:
        olt_type: Type of OLT (ZTE_C300 or ZTE_C320)
        host: OLT IP address
        port: CLI port
        username: Login username
        password: Login password
        connection_type: "ssh" or "telnet"
        connect_timeout: Connection timeout in seconds
        command_timeout: Command execution timeout in seconds
        
    Returns:
        Appropriate ZTE adapter instance
        
    Raises:
        ValueError: If OLT type is not supported
    """
    adapter_class = ADAPTER_MAP.get(olt_type)
    
    if adapter_class is None:
        supported = ", ".join(t.value for t in ADAPTER_MAP.keys())
        raise ValueError(f"Unsupported OLT type: {olt_type}. Supported types: {supported}")
    
    return adapter_class(
        host=host,
        port=port,
        username=username,
        password=password,
        connection_type=connection_type,
        connect_timeout=connect_timeout,
        command_timeout=command_timeout,
    )


def get_supported_olt_types() -> list[OLTType]:
    """Return list of supported OLT types."""
    return list(ADAPTER_MAP.keys())


def is_olt_type_supported(olt_type: OLTType) -> bool:
    """Check if OLT type is supported."""
    return olt_type in ADAPTER_MAP
