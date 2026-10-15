# Ubiquiti-style features: what fits this switch

Hardware limits that decide scope: 8051 MCU (tiny RAM/flash), RTL8373-class switch core with hardware L2 tables.
Everything below is a first-pass estimate to be checked against the RTLPlayground register map and free flash after the LACP work.
Rating: HW = mostly a chip register setting, SW = needs 8051 code/RAM, UI = web only, NO = unrealistic on this MCU.
Status column reflects the RTLPlayground audit of 2026-10-15 (public docs on `main`).

| Feature (UniFi / EdgeSwitch) | Rating | Status in RTLPlayground | Notes |
|---|---|---|---|
| 802.1Q VLANs, access/trunk/native, PVID | HW | Present: 4096 VLANs, PVID, ingress modes | Gap: access/trunk/hybrid presets, LAG member sync |
| Dynamic LACP (802.3ad) + static LAG | SW | Present: dynamic LACP (4 groups), static LAG | Gap: churn/Marker, coupled Mux, partner key, member check (#377) |
| RSTP (802.1w) with BPDU guard, root guard, edge ports | SW | Partial: simplified RSTP, edge/guard/p2p per port | Gap: proposal/agreement, alternate/backup roles, TC notice to root. Verify guard semantics |
| Port mirroring, port isolation (protected ports) | HW | Present: mirroring | Isolation not yet verified |
| Storm control, per-port rate limiting | HW | Present: storm control | None |
| Jumbo frames, flow control, EEE | HW | Present: per-port MTU, EEE | Flow control not yet verified |
| IGMP snooping + querier | SW | Present: IGMP | Querier not yet verified |
| Static MAC, MAC limit per port | HW | Not verified | Stock has it; check RTLPlayground |
| 802.1p QoS, queue weights, DSCP trust | HW | Not verified | Stock UI has queue mapping and weights |
| Loop protection (loop detect packets) | SW | Not verified | Stock has it |
| Management VLAN | SW | Present: `vlan <id> mgmt`, restricts web UI and syslog | Drop from plan |
| LLDP (+ neighbor table) | SW | Not in feature list; source files reportedly exist, unverified | Confirm in source before planning |
| SFP DDM readout | SW | Present: temperature, RX/TX power | Drop from plan |
| Config backup/restore, firmware upgrade via web | SW | Partial: flash save and web firmware update | Restore unverified |
| Syslog, NTP, DHCP client, DNS | SW | Syslog, NTP, DNS present; DHCP server is a stated goal, not present | DHCP client unverified |
| Authentication: hashed password, HTTPS/TLS | NO/SW | Not verified | TLS on an 8051 is a stretch; plan simple hashed login first |
| 802.1X port auth, RADIUS | NO | Not present | Too heavy for the MCU |
| SNMP read-only | SW | Not verified | Possible if flash allows |
| Port security / DHCP snooping / ARP inspection | NO | Not present | Needs CPU-assisted inspection; skip |
| L3 routing, ACL-heavy rules | NO | Not present | Not an 8051 job; chip ACLs possible later |
| PoE control | N/A | N/A | No PoE on this model |
| Cable diagnostics | HW | Not verified | PHY test, if RTL8224 exposes it |
| Modern web UI (VLAN matrix, port graph, dark mode) | UI | Present base web UI | Redesign; limited by flash, design as small gzip'd SPA |

Suggested order: VLAN port presets, LACP hardening, RSTP gaps, LLDP, then UI. Management VLAN and the LACP base are already in RTLPlayground.
