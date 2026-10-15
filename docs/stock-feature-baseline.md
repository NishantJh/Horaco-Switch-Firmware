# Stock feature baseline (from the HC-SWTGW218AS user manual, 33 pages)

Defaults: http://192.168.2.1, admin/admin. Menus: System (info, IP, user account, port setting),
Configuration (802.1Q VLAN + PVID, QoS port-to-queue and queue weight, Loop, IGMP snooping, Trunk,
port mirroring, port isolation, bandwidth control, jumbo frame, MAC constraint, EEE),
Security (MAC table, static MAC, storm control), Monitoring (port stats), Tools (firmware upgrade, config backup/restore).

Notable limits to beat or match:
- Trunks: 2 groups, up to 4 ports each. Manual describes aggregation generally; the UI offers a LACP type in the stock image.
- Loop menu: modes are off, loop detection, loop prevention, spanning tree (RSTP global + per-port).
- VLAN IDs 1-4094; VLAN 1 cannot be deleted.
- Port speeds: 10/100/1000/2500 forced or auto, flow control, per-port jumbo MTU.
