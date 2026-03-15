from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass
class ProxmoxServiceRow:
    kind: str
    vmid: str | None
    service_name: str | None
    node_name: str | None
    ip_address: str | None
    mac_address: str | None
    manufacturer: str | None


class ProxmoxInventoryService:
    """Read Proxmox inventory over SSH.

    Notes:
    - This service intentionally does not commit. Let the caller commit once.
    - It returns normalized rows for the discovery service to match against.
    """

    def __init__(self, db: Session, ssh_target: str = "root@proxmox.lab"):
        self.db = db
        self.ssh_target = ssh_target

    def _run(self, command: str) -> str:
        result = subprocess.run(
            ["ssh", self.ssh_target, command],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def refresh(self) -> list[ProxmoxServiceRow]:
        rows: list[ProxmoxServiceRow] = []

        # Node itself
        try:
            node_hostname = self._run("hostname -s").strip()
            node_ip = self._run("hostname -I | awk '{print $1}'").strip() or None
            rows.append(
                ProxmoxServiceRow(
                    kind="node",
                    vmid=None,
                    service_name=node_hostname,
                    node_name=node_hostname,
                    ip_address=node_ip,
                    mac_address=None,
                    manufacturer=None,
                )
            )
        except Exception:
            pass

        # LXC containers
        try:
            pct_json = self._run("pct list --output-format json")
            containers = json.loads(pct_json)
        except Exception:
            containers = []

        for ct in containers:
            vmid = str(ct.get("vmid"))
            name = ct.get("name")
            node_name = ct.get("node") or rows[0].node_name if rows else None
            ip_address = None
            try:
                ip_raw = self._run(f"pct exec {vmid} -- sh -lc \"ip -j -4 addr show scope global\"")
                ip_data = json.loads(ip_raw)
                for iface in ip_data:
                    for addr in iface.get("addr_info", []):
                        local = addr.get("local")
                        if local and not local.startswith("127."):
                            ip_address = local
                            break
                    if ip_address:
                        break
            except Exception:
                pass
            rows.append(
                ProxmoxServiceRow(
                    kind="lxc",
                    vmid=vmid,
                    service_name=name,
                    node_name=node_name,
                    ip_address=ip_address,
                    mac_address=None,
                    manufacturer="LXC Container",
                )
            )

        return rows
