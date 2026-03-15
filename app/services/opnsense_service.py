from __future__ import annotations

import base64
from typing import Any

import requests


class OPNsenseService:
    def __init__(self, base_url: str, api_key: str, api_secret: str, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        token = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}"}

    def _get(self, path: str) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}{path}", headers=self.headers, timeout=self.timeout, verify=False)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        response = requests.post(f"{self.base_url}{path}", headers=self.headers, json=payload or {}, timeout=self.timeout, verify=False)
        response.raise_for_status()
        return response.json()

    def search_dns_overrides(self) -> list[dict[str, Any]]:
        data = self._post("/api/unbound/settings/search_host_override")
        rows = data.get("rows") or data.get("row") or []
        return rows if isinstance(rows, list) else []

    def ensure_dns_override(self, hostname: str, domain: str, ip_address: str) -> dict[str, Any]:
        existing = self.search_dns_overrides()
        match = next((r for r in existing if r.get("hostname") == hostname and r.get("domain") == domain), None)
        payload = {
            "host": {
                "enabled": "1",
                "hostname": hostname,
                "domain": domain,
                "server": ip_address,
                "description": "Managed by Homelab Control Service",
            }
        }
        if match and match.get("uuid"):
            result = self._post(f"/api/unbound/settings/set_host_override/{match['uuid']}", payload)
        else:
            result = self._post("/api/unbound/settings/add_host_override", payload)
        self._post("/api/unbound/service/reconfigure")
        return result
