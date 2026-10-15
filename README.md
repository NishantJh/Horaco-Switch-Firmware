# Horaco HC-SWTGW218AS custom firmware

Goal: managed-switch firmware for the HC-SWTGW218AS (8x2.5G + 1 SFP+, RTL8273N/RTL8224N family) with
dynamic LACP, VLANs, spanning tree and a modern web UI.

Base: [RTLPlayground](https://github.com/logicog/RTLPlayground) (MIT, 8051 + SDCC 4.5), which already
supports this board family (see its `doc/devices/SWTG018AS_A_V2_0.md`).

See [docs/PLAN.md](docs/PLAN.md) for the plan and [docs/stock-firmware-notes.md](docs/stock-firmware-notes.md)
for findings from the stock image.
Before installing anything on the switch, follow [docs/backup-and-rollback.md](docs/backup-and-rollback.md).

Vendor firmware images are NOT committed (redistribution); keep them under `stock/` locally (git-ignored).
