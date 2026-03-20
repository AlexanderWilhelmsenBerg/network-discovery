from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.discovery import DiscoveredDevice
from app.services.opnsense_service import OPNsenseService
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


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def compute_effective_name(device: DiscoveredDevice) -> str | None:
    return (
        _clean(device.hostname_override)
        or _clean(device.proxmox_service_name)
        or _clean(device.proxmox_node_name)
        or _clean(device.unifi_hostname)
        or _clean(device.unifi_display_name)
        or _clean(device.dns_override)
        or _clean(device.opnsense_hostname)
        or _clean(device.hostname)
        or _clean(device.ip_address)
    )


class DiscoveryService:
    def __init__(self, db: Session):
        self.db = db

    def run_discovery(self) -> None:
        if not _discovery_lock.acquire(blocking=False):
            raise RuntimeError("Discovery is already running")
        try:
            proxmox_rows = ProxmoxInventoryService(self.db).refresh()

            devices = self.db.scalars(select(DiscoveredDevice)).all()
            self._match_proxmox(devices, proxmox_rows)
            self._match_opnsense_dns_overrides(devices)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            _discovery_lock.release()

    def _match_opnsense_dns_overrides(self, devices: list[DiscoveredDevice]) -> None:
        settings = get_settings()
        if not settings.opnsense_api_key or not settings.opnsense_api_secret:
            return

        service = OPNsenseService(settings.opnsense_api_url, settings.opnsense_api_key, settings.opnsense_api_secret)
        overrides_by_ip = service.get_dns_overrides_by_ip()

        for device in devices:
            if not device.ip_address:
                continue
            override = overrides_by_ip.get(device.ip_address)
            if override:
                device.dns_override = override
            device.effective_name = compute_effective_name(device)
            device.hostname = device.effective_name
            device.updated_at = datetime.utcnow()

    def _match_proxmox(self, devices: list[DiscoveredDevice], proxmox_rows: list[ProxmoxServiceRow]) -> None:
        by_ip = {r.ip_address: r for r in proxmox_rows if r.ip_address}
        by_name = {r.service_name.lower(): r for r in proxmox_rows if r.service_name}

        for r in proxmox_rows:
            fallback = getattr(r, "name", None) or getattr(r, "hostname", None)
            if fallback:
                key = fallback.lower()
                if key not in by_name:
                    by_name[key] = r

        for device in devices:
            matched: ProxmoxServiceRow | None = None
            if device.ip_address and device.ip_address in by_ip:
                matched = by_ip[device.ip_address]
            if not matched:
                current_name = (
                    _clean(device.hostname_override)
                    or _clean(device.unifi_hostname)
                    or _clean(device.unifi_display_name)
                    or _clean(device.opnsense_hostname)
                    or _clean(device.hostname)
                )
                if current_name:
                    matched = by_name.get(current_name.lower())

            if matched:
                device.proxmox_service_name = _clean(matched.service_name)
                device.proxmox_node_name = _clean(matched.node_name)
                if matched.kind == "lxc":
                    device.manufacturer = "LXC Container"
                elif matched.kind == "vm":
                    device.manufacturer = "Virtual Machine"
                elif matched.kind == "node" and not _clean(device.manufacturer):
                    device.manufacturer = _clean(matched.manufacturer)

            device.effective_name = compute_effective_name(device)
            device.hostname = device.effective_name
            device.updated_at = datetime.utcnow()
