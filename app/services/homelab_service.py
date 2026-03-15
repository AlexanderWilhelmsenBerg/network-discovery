from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery import DiscoveredDevice
from app.models.device_inventory import HomelabDevice


class HomelabService:
    def __init__(self, db: Session):
        self.db = db

    def move_from_discovery(self, device_id: int) -> None:
        device = self.db.get(DiscoveredDevice, device_id)
        if not device:
            raise ValueError("Device not found")
        existing = self.db.scalars(select(HomelabDevice).where(HomelabDevice.discovered_device_id == device.id)).first()
        if not existing:
            existing = HomelabDevice(
                discovered_device_id=device.id,
                name=device.effective_name,
                hostname=device.effective_name,
                ip_address=device.ip_address,
                mac_address=device.mac_address,
                dns_override=device.dns_override,
            )
            self.db.add(existing)
        device.managed_in = "homelab"
        self.db.commit()

    def delete_to_discovery(self, homelab_id: int) -> None:
        row = self.db.get(HomelabDevice, homelab_id)
        if not row:
            raise ValueError("Homelab device not found")
        device = self.db.get(DiscoveredDevice, row.discovered_device_id)
        if device:
            device.managed_in = None
        self.db.delete(row)
        self.db.commit()
