from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProxmoxService(Base):
    __tablename__ = "proxmox_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vmid: Mapped[int] = mapped_column(Integer, index=True)
    service_type: Mapped[str] = mapped_column(String(16), default="lxc")
    node_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_name: Mapped[str] = mapped_column(String(255), index=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
