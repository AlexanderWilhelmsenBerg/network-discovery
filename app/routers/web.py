from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.discovery import DiscoveredDevice
from app.models.device_inventory import DeviceRecord, HomelabDevice
from app.services.device_inventory_service import DeviceInventoryService
from app.services.discovery_service import DiscoveryService, compute_effective_name
from app.services.homelab_service import HomelabService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def flash(request: Request, level: str, message: str) -> None:
    request.session["flash"] = {"level": level, "message": message}


@router.get("/discovery")
def discovery_page(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(select(DiscoveredDevice).where(DiscoveredDevice.managed_in.is_(None)).order_by(DiscoveredDevice.effective_name)).all()
    return templates.TemplateResponse("discovery.html", {"request": request, "rows": rows, "flash": request.session.pop("flash", None)})


@router.post("/discovery/run")
def run_discovery(request: Request, db: Session = Depends(get_db)):
    try:
        DiscoveryService(db).run_discovery()
        flash(request, "success", "Discovery completed")
    except Exception as exc:
        flash(request, "error", f"Discovery failed: {exc}")
    return RedirectResponse("/discovery", status_code=303)


@router.post("/discovery/{device_id}/override")
def save_override(device_id: int, request: Request, hostname_override: str = Form(""), db: Session = Depends(get_db)):
    row = db.get(DiscoveredDevice, device_id)
    if row:
        row.hostname_override = hostname_override.strip() or None
        row.effective_name = compute_effective_name(row)
        row.hostname = row.effective_name
        db.commit()
        flash(request, "success", "Override saved")
    else:
        flash(request, "error", "Device not found")
    return RedirectResponse("/discovery", status_code=303)


@router.post("/discovery/{device_id}/move-homelab")
def move_homelab(device_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        HomelabService(db).move_from_discovery(device_id)
        flash(request, "success", "Moved to Homelab")
    except Exception as exc:
        flash(request, "error", str(exc))
    return RedirectResponse("/discovery", status_code=303)


@router.post("/discovery/{device_id}/move-devices")
def move_devices(device_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        DeviceInventoryService(db).move_from_discovery(device_id)
        flash(request, "success", "Moved to Devices")
    except Exception as exc:
        flash(request, "error", str(exc))
    return RedirectResponse("/discovery", status_code=303)


@router.get("/homelab")
def homelab_page(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(select(HomelabDevice).order_by(HomelabDevice.name)).all()
    return templates.TemplateResponse("homelab.html", {"request": request, "rows": rows, "flash": request.session.pop("flash", None)})


@router.post("/homelab/{row_id}/delete")
def homelab_delete(row_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        HomelabService(db).delete_to_discovery(row_id)
        flash(request, "success", "Returned to Discovery")
    except Exception as exc:
        flash(request, "error", str(exc))
    return RedirectResponse("/homelab", status_code=303)


@router.get("/devices")
def devices_page(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(select(DeviceRecord).order_by(DeviceRecord.name)).all()
    return templates.TemplateResponse("devices.html", {"request": request, "rows": rows, "flash": request.session.pop("flash", None)})


@router.post("/devices/{row_id}/delete")
def devices_delete(row_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        DeviceInventoryService(db).delete_to_discovery(row_id)
        flash(request, "success", "Returned to Discovery")
    except Exception as exc:
        flash(request, "error", str(exc))
    return RedirectResponse("/devices", status_code=303)
