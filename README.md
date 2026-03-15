# Homelab Control Service

A modular FastAPI-based service designed to run as a Linux service on your `opstools` host.

## Phase 1 goals

- Discover network devices from UniFi and OPNsense
- Show a discovery table in the web UI
- Track first seen, last seen, and connection duration
- Move selected devices into a Homelab inventory table
- Keep the code structured so you can later add:
  - VLAN management
  - Traefik routes
  - Uptime Kuma entries
  - DNS overrides
  - Static IP planning
  - Container inventory from Proxmox / host SSH

## Design principles

- **Modular**: each domain has its own model, service, and router
- **Linux service first**: includes a `systemd` unit file
- **Single config source**: one `.env` file for secrets and endpoints
- **Separation of concerns**:
  - `models/` = database tables
  - `services/` = business logic and sync jobs
  - `routers/` = web/API endpoints
  - `templates/` = UI pages
- **Extensible DB**: separate tables for discovery, homelab assets, VLANs, routes, checks

## Planned modules

### Implemented now
- Discovery
- Homelab inventory shell
- Dashboard navigation
- Move-to-homelab workflow
- Linux service deployment files

### Planned next
- VLAN assignment logic
- Static IP planning / reservation state
- DNS overrides
- Uptime Kuma integration
- Traefik route generation
- Proxmox container sync over SSH

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

## Linux service deployment

1. Copy the project to `/mnt/config/opstools/discovery-tool/`
2. Create a venv in that folder
3. Copy `.env.example` to `.env` and fill it in
4. Install the systemd unit from `deploy/systemd/discovery-tool.service`
5. Adjust paths if needed
6. Enable and start:

```bash
sudo cp deploy/systemd/discovery-tool.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now discovery-tool.service
sudo systemctl status discovery-tool.service
```

## Database layout

The database is intentionally split by function.

- `discovered_devices`
- `device_observations`
- `homelab_devices`
- `vlans`
- `dns_overrides`
- `traefik_routes`
- `uptime_kuma_checks`

Only discovery and homelab workflows are wired up in this version.
