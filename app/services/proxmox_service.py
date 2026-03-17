from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings


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

    def __init__(self, db: Session, ssh_target: str | None = None):
        self.db = db
        settings = get_settings()
        self.ssh_target = ssh_target or f"{settings.proxmox_ssh_user}@{settings.proxmox_ssh_host}"
        self.ssh_key_path = settings.proxmox_ssh_key_path

    def _run(self, command: str) -> str:
        result = subprocess.run(
            ["ssh", "-i", self.ssh_key_path, self.ssh_target, command],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def _extract_first_ipv4(self, ip_json: str) -> str | None:
        try:
            ip_data = json.loads(ip_json)
        except json.JSONDecodeError:
            return None

        for iface in ip_data:
            for addr in iface.get("addr_info", []):
                local = addr.get("local")
                if local and not local.startswith("127."):
                    return local
        return None

    def refresh(self) -> list[ProxmoxServiceRow]:
        rows: list[ProxmoxServiceRow] = []

        node_name: str | None = None
        try:
            node_name = self._run("hostname -s").strip() or None
            node_ip = self._run("hostname -I | awk '{print $1}'").strip() or None
            rows.append(
                ProxmoxServiceRow(
                    kind="node",
                    vmid=None,
                    service_name=node_name,
                    node_name=node_name,
                    ip_address=node_ip,
                    mac_address=None,
                    manufacturer="Proxmox Node",
                )
            )
        except Exception:
            pass

        try:
            pct_json = self._run("pct list --output-format json")
            containers = json.loads(pct_json)
        except Exception:
            containers = []

        for ct in containers:
            vmid = str(ct.get("vmid"))
            name = ct.get("name")
            row_node_name = ct.get("node") or node_name
            ip_address = None
            try:
                ip_raw = self._run(f"pct exec {vmid} -- sh -lc \"ip -j -4 addr show scope global\"")
                ip_address = self._extract_first_ipv4(ip_raw)
            except Exception:
                pass
            rows.append(
                ProxmoxServiceRow(
                    kind="lxc",
                    vmid=vmid,
                    service_name=name,
                    node_name=row_node_name,
                    ip_address=ip_address,
                    mac_address=None,
                    manufacturer="LXC Container",
                )
            )

        try:
            qm_json = self._run("qm list --full 1 --output-format json")
            vms = json.loads(qm_json)
        except Exception:
            vms = []

        for vm in vms:
            vmid = str(vm.get("vmid"))
            name = vm.get("name")
            row_node_name = vm.get("node") or node_name
            ip_address = None
            try:
                ip_raw = self._run(
                    f"qm guest exec {vmid} -- ip -j -4 addr show scope global | sed -n 's/.*\"out-data\":\"\\(.*\\)\".*/\\1/p'"
                )
                if ip_raw.strip():
                    decoded = ip_raw.encode("utf-8").decode("unicode_escape")
                    ip_address = self._extract_first_ipv4(decoded)
            except Exception:
                pass
            rows.append(
                ProxmoxServiceRow(
                    kind="vm",
                    vmid=vmid,
                    service_name=name,
                    node_name=row_node_name,
                    ip_address=ip_address,
                    mac_address=None,
                    manufacturer="Virtual Machine",
                )
            )

        return rows
