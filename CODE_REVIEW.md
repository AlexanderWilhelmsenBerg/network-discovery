# Homelab Control Service – Code Review and Recommendations

This review focuses on the issues reported during iterative testing and the highest-value changes to stabilize the service.

## What is working well

- The app already has a sensible split between Discovery, Homelab, and Devices.
- Using UniFi as the primary source for client names is the right direction because UniFi exposes client activity and device data through the local Network API. citeturn575880view2
- Pulling DNS overrides through OPNsense Unbound is also the right long-term integration path because OPNsense documents host-override search, add, update, and reconfigure endpoints. citeturn575880view0

## Main issues found

### 1. Effective name is computed too late or rendered from the wrong field
The biggest UX issue is that `proxmox_service_name` can be detected but never becomes the actual display value. The fix is to centralize name precedence in one helper and recompute `effective_name` after **every** source merge.

Recommended precedence:
1. `hostname_override`
2. `proxmox_service_name`
3. `proxmox_node_name`
4. `unifi_hostname`
5. `unifi_display_name`
6. `dns_override`
7. `opnsense_hostname`
8. `ip_address`

### 2. Discovery runs overlap
The `Record has changed since last read in table 'proxmox_services'` error is classic overlapping discovery execution. The likely causes are:
- a manual discovery request running while a background discovery task is active, or
- nested commits inside sub-services.

Fixes included in this update:
- remove inner commits from `ProxmoxInventoryService.refresh()`
- commit once from the top-level discovery service
- add a process-level lock around discovery
- recommend disabling background polling until the write paths are stable

### 3. Manufacturer is wrong for containers
The Proxmox NIC vendor string is not meaningful for a service/container row. It should not overwrite container rows. This update changes matched container rows to show `LXC Container` or `Virtual Machine`, while the node itself keeps the network-detected manufacturer.

### 4. UI layout needs width-aware forms
The override input and save button need to stay inside the same cell. The fix is:
- `table-layout: auto`
- horizontal table wrapper
- a grid layout inside the override cell
- `white-space: nowrap` on most cells

### 5. Move/delete flows should be state-based, not copy/delete hacks
The cleanest model is to keep a single discovered row and set `managed_in` to:
- `NULL` for Discovery
- `homelab`
- `devices`

That keeps history, observations, and matching intact.

## Architectural recommendations

### A. Keep all source fields separate
Do **not** overwrite source-specific values.

Keep:
- `unifi_hostname`
- `unifi_display_name`
- `opnsense_hostname`
- `dns_override`
- `hostname_override`
- `proxmox_service_name`
- `proxmox_node_name`
- `effective_name`

### B. Commit once per discovery cycle
Every sub-service should update the SQLAlchemy session but not call `commit()` on its own. Top-level orchestration should commit once or roll back once.

### C. Treat OPNsense write-backs as adapters
The app should treat OPNsense integrations as adapters:
- Unbound adapter for DNS overrides
- Kea adapter for reservations where available. OPNsense documents Kea reservation search/add/set and reconfigure endpoints. citeturn575880view1

That lets you swap implementations later without rewriting Homelab/Devices logic.

### D. Add a dedicated status/flash system
The UI should show success/warning/error notices clearly after write operations, especially for OPNsense and future Traefik/Uptime Kuma actions.

### E. Add migration discipline soon
Right now lightweight startup migrations are okay, but the project is large enough that Alembic would be a worthwhile next step.

## Highest-priority next steps after these files

1. Verify effective-name recomputation on every discovery run
2. Confirm OPNsense DNS override matching by IP and hostname
3. Finish Traefik detection from `/mnt/config/traefik/dynamic/services/`
4. Add Uptime Kuma adapter and UI state
5. Move startup migrations to Alembic

