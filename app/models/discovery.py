from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DiscoveredDevice(Base):
    __tablename__ = "discovered_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    mac_address: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    hostname_override: Mapped[str | None] = mapped_column(String(255), nullable=True)

    unifi_hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unifi_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opnsense_hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dns_override: Mapped[str | None] = mapped_column(String(255), nullable=True)

    proxmox_service_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proxmox_node_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)

    vlan: Mapped[str | None] = mapped_column(String(64), nullable=True)
    connected_since: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_primary: Mapped[str | None] = mapped_column(String(64), nullable=True)
    managed_in: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    has_traefik: Mapped[bool] = mapped_column(Boolean, default=False)
    has_uptime_kuma: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceObservation(Base):
    __tablename__ = "device_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(Integer, index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
