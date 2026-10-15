# Ubiquiti-style features: what fits this switch

Hardware limits that decide scope: 8051 MCU (tiny RAM/flash), RTL8373-class switch core with hardware L2 tables.
Everything below is a first-pass estimate to be checked against the RTLPlayground register map and free flash after the LACP work.
Rating: HW = mostly a chip register setting, SW = needs 8051 code/RAM, UI = web only, NO = unrealistic on this MCU.

| Feature (UniFi / EdgeSwitch) | Rating | Notes |
|---|---|---|
| 802.1Q VLANs, access/trunk/native, PVID | HW | Largely in RTLPlayground (doc/vlan.md): 4096-entry VLAN table, per-port PVID, tagged/untagged membership, ingress filter `t`/`u`/`a`. Missing: access/trunk/hybrid presets built on these, persistence, LAG member sync |
| Dynamic LACP (802.3ad) + static LAG | SW | Priority 1; stock has lacp_fsm.c as reference. Stock trunks: 2 groups x 4 ports |
| RSTP (802.1w) with BPDU guard, root guard, edge ports | SW | Stock has rstp.c; RTLPlayground's is simplified |
| Port mirroring, port isolation (protected ports) | HW | Already in stock and RTLPlayground |
| Storm control, per-port rate limiting | HW | Present in both |
| Jumbo frames, flow control, EEE | HW | Present in both |
| IGMP snooping + querier | SW | In both; querier is the extra |
| Static MAC, MAC limit per port | HW | Present in stock |
| 802.1p QoS, queue weights, DSCP trust | HW | Stock UI has queue mapping and weights |
| Loop protection (loop detect packets) | SW | Stock has it |
| Management VLAN | HW | Done in RTLPlayground: `vlan <id> mgmt` (default VLAN 1). Missing: web UI binding, lockout guard for a bad VLAN ID |
| LLDP (+ neighbor table) | SW | Small enough; useful for UniFi-like topology view |
| SFP DDM readout | SW | RTLPlayground has it |
| Config backup/restore, firmware upgrade via web | SW | Both have it |
| Syslog, NTP, DHCP client, DNS | SW | RTLPlayground has them (uip stack) |
| Authentication: hashed password, HTTPS/TLS | NO/SW | TLS on an 8051 is a stretch; plan simple hashed login first |
| 802.1X port auth, RADIUS | NO | Too heavy for the MCU |
| SNMP read-only | SW | Possible if flash allows |
| Port security / DHCP snooping / ARP inspection | NO | Needs CPU-assisted inspection; skip |
| L3 routing, ACL-heavy rules | NO | Not an 8051 job; chip ACLs possible later |
| PoE control | N/A | No PoE on this model |
| Cable diagnostics | HW | PHY test, if RTL8224 exposes it |
| Modern web UI (VLAN matrix, port graph, dark mode) | UI | Limited by flash; design as small gzip'd SPA |

Suggested order after LACP: VLAN port modes + config persistence (small, builds on vlan.md), RSTP with guards, LLDP, then UI. Management VLAN is no longer a separate step.

Note: vlan.md is written for the RTL837x register map. The SWTG018AS doc lists the same 8273N + 8224N core, but register addresses are not yet verified on this exact chip.
