from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class HomelabDevice(Base):
    __tablename__ = "homelab_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discovered_device_id: Mapped[int] = mapped_column(Integer, ForeignKey("discovered_devices.id"), index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vlan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dns_override: Mapped[str | None] = mapped_column(String(255), nullable=True)
    static_ip_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    traefik_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    uptime_kuma_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceRecord(Base):
    __tablename__ = "device_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discovered_device_id: Mapped[int] = mapped_column(Integer, ForeignKey("discovered_devices.id"), index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dns_override: Mapped[str | None] = mapped_column(String(255), nullable=True)
    static_ip_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    traefik_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    uptime_kuma_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
