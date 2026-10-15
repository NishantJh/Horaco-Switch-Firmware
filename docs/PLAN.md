# Plan (draft, awaiting owner edits)

Base: RTLPlayground (github.com/logicog/RTLPlayground). Audited 2026-10-15 from its public docs on `main`.

Already in RTLPlayground, so not re-planned: VLANs (4096 entries, PVID, ingress modes, management VLAN), dynamic LACP (up to 4 groups), static LAG (hash modes), simplified STP/RSTP (edge/guard/p2p per port, LAG-aware), port mirroring, IGMP, storm control, SFP DDM, serial CLI, web UI, config saved to flash, firmware update via web. HC-SWTGW218AS is in its tested-device list. Feature matrix: docs/ubiquiti-feature-feasibility.md.

Order:
1. Prepare: back up both flash chips (SOIC-8 clip), build RTLPlayground for HC-SWTGW218AS, and verify the build on the bench. No flashing of the switch until a tested build exists (owner rule).
2. LACP hardening: churn detection and Marker protocol, decoupled collect/distribute, partner-key check in Selection, member compatibility check (RTLPlayground #377).
3. VLAN port presets: access, trunk, and hybrid modes as a layer over existing PVID and ingress settings. Apply VLAN settings to LAG members.
4. RSTP gaps: proposal/agreement fast transition, alternate/backup port roles, topology-change notice toward root. Check the existing BPDU/root guard behaviour in code before changing it.
5. LLDP with neighbour table. Not in RTLPlayground's feature list; confirm in source first.
6. Config backup/restore. Flash save and web firmware update exist; restore is unverified.
7. Web UI: VLAN matrix, LAG and LACP status, port graphs, dark mode, within flash limits (single gzip'd SPA).

Open:
- Flash layout: doc says 2MB, and an older note says 4Mbit with two chips. Still unresolved.
- RTLPlayground's device docs cite the RTL8372/8373 family. Confirm the register map matches the RTL8273N/RTL8224N on this board.
- UART log of stock with a LAG partner.
