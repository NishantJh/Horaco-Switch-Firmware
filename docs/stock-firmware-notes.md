# Stock firmware HRRF_V200.2.4_HC-SWTGW218AS_0319 (980,456 bytes)

- 8051 image, header bytes `12 34 56 78`.
- Embedded source paths: `common/src/lwps/lacp_fsm.c`, `rstp.c`, `igmp_snooping.c`, `dal/rtl8373/dal_rtl8373_trunk.c`, `sal/saltrunk.c`, `web_hengrui/*`.
- Web UI: trunk_type selector with LACP option; debug strings `lacp_link_up`, `lacp_port_enable`.
- Trunk rules enforced: 2-4 members; same speed, duplex, negotiation and VLAN; not mirror port; no rate limiting on members.
