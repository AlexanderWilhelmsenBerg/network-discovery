from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery import DiscoveredDevice
from app.models.device_inventory import DeviceRecord


class DeviceInventoryService:
    def __init__(self, db: Session):
        self.db = db

    def move_from_discovery(self, device_id: int) -> None:
        device = self.db.get(DiscoveredDevice, device_id)
        if not device:
            raise ValueError("Device not found")
        resolved_name = (
            (device.effective_name or "").strip()
            or (device.hostname_override or "").strip()
            or (device.hostname or "").strip()
            or (device.dns_override or "").strip()
            or (device.ip_address or "").strip()
            or (device.mac_address or "").strip()
            or f"device-{device.id}"
        )
        existing = self.db.scalars(select(DeviceRecord).where(DeviceRecord.discovered_device_id == device.id)).first()
        if not existing:
            existing = DeviceRecord(
                discovered_device_id=device.id,
                name=resolved_name,
                hostname=resolved_name,
                ip_address=device.ip_address,
                mac_address=device.mac_address,
                dns_override=device.dns_override,
            )
            self.db.add(existing)
        device.managed_in = "devices"
        self.db.commit()

    def delete_to_discovery(self, record_id: int) -> None:
        row = self.db.get(DeviceRecord, record_id)
        if not row:
            raise ValueError("Device record not found")
        device = self.db.get(DiscoveredDevice, row.discovered_device_id)
        if device:
            device.managed_in = None
        self.db.delete(row)
        self.db.commit()
