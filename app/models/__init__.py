from app.models.discovery import DeviceObservation, DiscoveredDevice
from app.models.device_inventory import DeviceRecord
from app.models.homelab import HomelabDevice
from app.models.integrations import TraefikRoute, UptimeKumaCheck
from app.models.network import DnsOverride, Vlan
from app.models.proxmox import ProxmoxService

__all__ = [
    "DiscoveredDevice",
    "DeviceRecord",
    "DeviceObservation",
    "HomelabDevice",
    "Vlan",
    "DnsOverride",
    "TraefikRoute",
    "UptimeKumaCheck",
    "ProxmoxService",
]
