# Project context

One-page summary. Details live in docs/PLAN.md and the other docs.

## Hardware

- Device: HC-SWTGW218AS (same board as SWTG018AS-A V2.0).
- Chips: RTL8273N switch controller, RTL8224N PHY, 8051 core.
- Ports: 8x 2.5G copper plus SFP+.
- Flash: 2 MB W25Q16JVSIQ (16 Mbit). The "4M-bit" note in the device doc is stale.
- Code path: RTL837x (`isRTL8373=1` in the machine profile). Not yet confirmed on the bench.

## Repositories

- `NishantJh/RTLPlayground` (fork): firmware code. Keep changes upstreamable.
- `NishantJh/Horaco-Switch-Firmware`: plans, docs, host-side tests, and the stock-firmware analysis. Never commits stock vendor firmware.

## Plan order (docs/PLAN.md)

1. Back up both flash chips, build for HC-SWTGW218AS, verify on the bench.
2. LACP hardening: churn detection and Marker, decoupled collect/distribute, partner-key check, member compatibility check.
3. VLAN port presets (access, trunk, hybrid) and VLAN sync to LAG members.
4. RSTP gaps: proposal/agreement, alternate and backup roles, topology-change notice.
5. LLDP neighbour table, if missing.
6. Config backup and restore.
7. Web UI: VLAN matrix, LAG/LACP status, port graphs, dark mode.

## Already in RTLPlayground

- VLANs: 4096 entries, PVID, ingress modes, management VLAN.
- LAG: dynamic LACP (up to 4 groups) and static LAG (hash modes).
- STP/RSTP: simplified, with edge, guard and p2p per port, LAG-aware.
- Port mirroring, IGMP, storm control, SFP DDM, LLDP TX with per-port permit/block.
- Serial CLI, web UI, config saved to flash, firmware update via web.

## Rules

- All changes go through PRs. `main` is protected on both repos.
- Merge the fork PR before its matching test PR here, or CI shows a gap.
- Never flash the switch until a build passes tests. Nishant flashes.
- Take a full SPI dump before the first install.

## Open PRs

Horaco-Switch-Firmware:
- #1: 8051 disassembler and stock LACP analysis docs.
- #4: CI on a self-hosted Windows runner.
- #5: Backup and rollback procedure for stock firmware.
- #6: Web UI mock switch and screenshots.

RTLPlayground:
- #2: CI on a self-hosted Windows runner.
- #3: Web UI front-panel dashboard, port drawer with VLAN profile (draft).
- #4: STP alternate-port blocking and failover.
