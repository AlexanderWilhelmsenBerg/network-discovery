from __future__ import annotations

import json
from datetime import datetime
from threading import Lock
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery import DeviceObservation, DiscoveredDevice
from app.services.proxmox_service import ProxmoxInventoryService, ProxmoxServiceRow

_discovery_lock = Lock()


def make_json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    return value


def compute_effective_name(device: DiscoveredDevice) -> str | None:
    return (
        (device.hostname_override or "").strip()
        or device.proxmox_service_name
        or device.proxmox_node_name
        or device.unifi_hostname
        or device.unifi_display_name
        or device.dns_override
        or device.opnsense_hostname
        or device.ip_address
    )


class DiscoveryService:
    def __init__(self, db: Session):
        self.db = db

    def run_discovery(self) -> None:
        if not _discovery_lock.acquire(blocking=False):
            raise RuntimeError("Discovery is already running")
        try:
            proxmox_rows = ProxmoxInventoryService(self.db).refresh()

            # NOTE: This file intentionally focuses on the merge/update logic.
            # Keep your existing UniFi and OPNsense collectors and feed their rows into `_upsert_row`.
            # Here, we only recompute names robustly after Proxmox matching.
            devices = self.db.scalars(select(DiscoveredDevice)).all()
            self._match_proxmox(devices, proxmox_rows)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            _discovery_lock.release()

    def _match_proxmox(self, devices: list[DiscoveredDevice], proxmox_rows: list[ProxmoxServiceRow]) -> None:
        by_ip = {r.ip_address: r for r in proxmox_rows if r.ip_address}
        by_name = {r.service_name.lower(): r for r in proxmox_rows if r.service_name}

        for device in devices:
            matched: ProxmoxServiceRow | None = None
            if device.ip_address and device.ip_address in by_ip:
                matched = by_ip[device.ip_address]
            if not matched:
                current_name = (
                    (device.hostname_override or "").strip()
                    or device.unifi_hostname
                    or device.unifi_display_name
                    or device.opnsense_hostname
                    or device.hostname
                )
                if current_name:
                    matched = by_name.get(current_name.lower())

            if matched:
                device.proxmox_service_name = matched.service_name
                device.proxmox_node_name = matched.node_name
                # Meaningful manufacturer for containers; keep node/network manufacturer for real hosts
                if matched.kind == "lxc":
                    device.manufacturer = "LXC Container"
                elif matched.kind == "node" and not device.manufacturer:
                    device.manufacturer = matched.manufacturer

            device.effective_name = compute_effective_name(device)
            device.hostname = device.effective_name
            device.updated_at = datetime.utcnow()
