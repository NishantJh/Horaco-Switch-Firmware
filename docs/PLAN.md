# Plan (draft, awaiting owner edits)

Base: RTLPlayground (github.com/logicog/RTLPlayground). Audited 2026-10-15 from its public docs on `main`.

Already in RTLPlayground, so not re-planned: VLANs (4096 entries, PVID, ingress modes, management VLAN), dynamic LACP (up to 4 groups), static LAG (hash modes), simplified STP/RSTP (edge/guard/p2p per port, LAG-aware), port mirroring, IGMP, storm control, SFP DDM, serial CLI, web UI, config saved to flash, firmware update via web. HC-SWTGW218AS is in its tested-device list. Feature matrix: docs/ubiquiti-feature-feasibility.md.

Order:
1. Prepare: back up both flash chips (SOIC-8 clip), build RTLPlayground for HC-SWTGW218AS, and verify the build on the bench. No flashing of the switch until a tested build exists (owner rule).
2. LACP hardening: churn detection and Marker protocol, decoupled collect/distribute, partner-key check in Selection, member compatibility check (RTLPlayground #377).
3. VLAN port presets: access, trunk, and hybrid modes as a layer over existing PVID and ingress settings. Apply VLAN settings to LAG members.
4. RSTP gaps: proposal/agreement fast transition, alternate/backup port roles, topology-change notice toward root. Check the existing BPDU/root guard behaviour in code before changing it.
5. LLDP neighbour table, if missing. LLDP TX and per-port permit/block already exist (rtl837x_lldp.c).
6. Config backup/restore. Flash save and web firmware update exist; restore is unverified.
7. Web UI: VLAN matrix, LAG and LACP status, port graphs, dark mode, within flash limits (single gzip'd SPA).

Resolved from the fork (NishantJh/rtlplayground, 2026-10-15):
- Flash: 2MB W25Q16JVSIQ (16 Mbit) per doc/devices/SWTG018AS_A_V2_0.md. The "4M-bit" line in that doc is a stale note. Machine profile uses MAC offset 0x1FC000, which fits 2MB.
- Register map: machine/PCB_SWTG018AS_V2_1_0.c sets isRTL8373=1, so the RTL837x code path is used. Not checked against an 8273N datasheet; confirm on the bench.

Open:
- UART log of stock with a LAG partner.
