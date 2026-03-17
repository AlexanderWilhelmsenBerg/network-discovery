from __future__ import annotations

import re
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.device_inventory import DeviceRecord, HomelabDevice
from app.models.discovery import DiscoveredDevice
from app.services.device_inventory_service import DeviceInventoryService
from app.services.discovery_service import DiscoveryService, compute_effective_name
from app.services.homelab_service import HomelabService
from app.services.opnsense_service import OPNsenseService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_flash(request: Request) -> dict[str, str] | None:
    level = request.query_params.get("flash_level")
    message = request.query_params.get("flash_message")
    if not level or not message:
        return None
    return {"level": level, "message": message}


def redirect_with_flash(path: str, level: str, message: str) -> RedirectResponse:
    query = urlencode({"flash_level": level, "flash_message": message})
    return RedirectResponse(f"{path}?{query}", status_code=303)


def _slugify_hostname(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if not lowered:
        return None
    cleaned = re.sub(r"[^a-z0-9-]", "-", lowered)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or None


def _dns_suggestion(device: DiscoveredDevice) -> str | None:
    settings = get_settings()
    host = _slugify_hostname(device.hostname_override) or _slugify_hostname(device.effective_name) or _slugify_hostname(device.hostname)
    if not host:
        return None
    return f"{host}.{settings.default_domain}"


@router.get("/")
def root_page(request: Request, db: Session = Depends(get_db)):
    discovered_count = db.scalar(
        select(func.count()).select_from(DiscoveredDevice).where(DiscoveredDevice.managed_in.is_(None))
    )
    homelab_count = db.scalar(select(func.count()).select_from(HomelabDevice))
    devices_count = db.scalar(select(func.count()).select_from(DeviceRecord))
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "flash": get_flash(request),
            "discovered_count": discovered_count or 0,
            "homelab_count": homelab_count or 0,
            "devices_count": devices_count or 0,
        },
    )


@router.get("/discovery")
def discovery_page(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(DiscoveredDevice)
        .where(DiscoveredDevice.managed_in.is_(None))
        .order_by(DiscoveredDevice.effective_name, DiscoveredDevice.id)
    ).all()

    suggestions = {row.id: _dns_suggestion(row) for row in rows}
    return templates.TemplateResponse(
        "discovery.html",
        {"request": request, "rows": rows, "dns_suggestions": suggestions, "flash": get_flash(request)},
    )


@router.post("/discovery/run")
def run_discovery(db: Session = Depends(get_db)):
    try:
        DiscoveryService(db).run_discovery()
        return redirect_with_flash("/discovery", "success", "Discovery completed")
    except Exception as exc:
        return redirect_with_flash("/discovery", "error", f"Discovery failed: {exc}")


@router.post("/discovery/{device_id}/override")
def save_override(device_id: int, hostname_override: str = Form(""), db: Session = Depends(get_db)):
    row = db.get(DiscoveredDevice, device_id)
    if row:
        row.hostname_override = hostname_override.strip() or None
        row.effective_name = compute_effective_name(row)
        row.hostname = row.effective_name
        db.commit()
        return redirect_with_flash("/discovery", "success", "Override saved")
    return redirect_with_flash("/discovery", "error", "Device not found")


@router.post("/discovery/{device_id}/create-dns-override")
def create_dns_override(device_id: int, db: Session = Depends(get_db)):
    row = db.get(DiscoveredDevice, device_id)
    if not row:
        return redirect_with_flash("/discovery", "error", "Device not found")
    if not row.ip_address:
        return redirect_with_flash("/discovery", "error", "Device has no IP address")

    suggestion = _dns_suggestion(row)
    if not suggestion or "." not in suggestion:
        return redirect_with_flash("/discovery", "error", "No valid hostname available for DNS override")

    settings = get_settings()
    if not settings.opnsense_api_key or not settings.opnsense_api_secret:
        return redirect_with_flash("/discovery", "error", "OPNsense credentials are not configured")

    hostname, domain = suggestion.split(".", 1)
    try:
        opnsense = OPNsenseService(settings.opnsense_api_url, settings.opnsense_api_key, settings.opnsense_api_secret)
        opnsense.ensure_dns_override(hostname=hostname, domain=domain, ip_address=row.ip_address)
        row.dns_override = suggestion
        row.effective_name = compute_effective_name(row)
        row.hostname = row.effective_name
        db.commit()
        return redirect_with_flash("/discovery", "success", f"DNS override created: {suggestion}")
    except Exception as exc:
        db.rollback()
        return redirect_with_flash("/discovery", "error", f"DNS override creation failed: {exc}")


@router.post("/discovery/{device_id}/move-homelab")
def move_homelab(device_id: int, db: Session = Depends(get_db)):
    try:
        HomelabService(db).move_from_discovery(device_id)
        return redirect_with_flash("/discovery", "success", "Moved to Homelab")
    except Exception as exc:
        return redirect_with_flash("/discovery", "error", str(exc))


@router.post("/discovery/{device_id}/move-devices")
def move_devices(device_id: int, db: Session = Depends(get_db)):
    try:
        DeviceInventoryService(db).move_from_discovery(device_id)
        return redirect_with_flash("/discovery", "success", "Moved to Devices")
    except Exception as exc:
        return redirect_with_flash("/discovery", "error", str(exc))


@router.get("/homelab")
def homelab_page(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(select(HomelabDevice).order_by(HomelabDevice.name)).all()
    return templates.TemplateResponse(
        "homelab.html",
        {"request": request, "rows": rows, "flash": get_flash(request)},
    )


@router.post("/homelab/{row_id}/delete")
def homelab_delete(row_id: int, db: Session = Depends(get_db)):
    try:
        HomelabService(db).delete_to_discovery(row_id)
        return redirect_with_flash("/homelab", "success", "Returned to Discovery")
    except Exception as exc:
        return redirect_with_flash("/homelab", "error", str(exc))


@router.get("/devices")
def devices_page(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(select(DeviceRecord).order_by(DeviceRecord.name)).all()
    return templates.TemplateResponse(
        "devices.html",
        {"request": request, "rows": rows, "flash": get_flash(request)},
    )


@router.post("/devices/{row_id}/delete")
def devices_delete(row_id: int, db: Session = Depends(get_db)):
    try:
        DeviceInventoryService(db).delete_to_discovery(row_id)
        return redirect_with_flash("/devices", "success", "Returned to Discovery")
    except Exception as exc:
        return redirect_with_flash("/devices", "error", str(exc))
