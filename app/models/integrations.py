from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TraefikRoute(Base):
    __tablename__ = "traefik_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True)
    target_url: Mapped[str] = mapped_column(String(512))
    middleware_chain: Mapped[str | None] = mapped_column(String(512), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class UptimeKumaCheck(Base):
    __tablename__ = "uptime_kuma_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    url: Mapped[str] = mapped_column(String(512))
    check_type: Mapped[str] = mapped_column(String(64), default="http")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
