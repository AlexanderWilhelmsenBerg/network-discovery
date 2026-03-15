from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HomelabDevice(Base):
    __tablename__ = "homelab_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discovered_device_id: Mapped[int | None] = mapped_column(ForeignKey("discovered_devices.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vlan_id: Mapped[int | None] = mapped_column(ForeignKey("vlans.id"), nullable=True)
    dns_override: Mapped[str | None] = mapped_column(String(255), nullable=True)
    traefik_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    uptime_kuma_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    static_ip_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
