from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine

from app import models  # noqa: F401


def _ensure_column(table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(engine)
    columns = {col['name'] for col in inspector.get_columns(table_name)}
    if column_name in columns:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_column("discovered_devices", "unifi_hostname", "unifi_hostname VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "hostname", "hostname VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "effective_name", "effective_name VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "unifi_display_name", "unifi_display_name VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "opnsense_hostname", "opnsense_hostname VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "hostname_override", "hostname_override VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "dns_override", "dns_override VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "has_dns_override", "has_dns_override BOOL NOT NULL DEFAULT 0")
    _ensure_column("discovered_devices", "manufacturer", "manufacturer VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "proxmox_service_name", "proxmox_service_name VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "proxmox_node_name", "proxmox_node_name VARCHAR(255) NULL")
    _ensure_column("discovered_devices", "vlan", "vlan VARCHAR(64) NULL")
    _ensure_column("discovered_devices", "connected_since", "connected_since DATETIME NULL")
    _ensure_column("discovered_devices", "source_primary", "source_primary VARCHAR(64) NULL")
    _ensure_column("discovered_devices", "managed_in", "managed_in VARCHAR(32) NULL")
    _ensure_column("discovered_devices", "has_traefik", "has_traefik BOOL NOT NULL DEFAULT 0")
    _ensure_column("discovered_devices", "has_uptime_kuma", "has_uptime_kuma BOOL NOT NULL DEFAULT 0")
    _ensure_column("device_records", "dns_override", "dns_override VARCHAR(255) NULL")
    _ensure_column("device_records", "static_ip_enabled", "static_ip_enabled BOOL NOT NULL DEFAULT 0")
    _ensure_column("device_records", "traefik_enabled", "traefik_enabled BOOL NOT NULL DEFAULT 0")
    _ensure_column("device_records", "uptime_kuma_enabled", "uptime_kuma_enabled BOOL NOT NULL DEFAULT 0")
