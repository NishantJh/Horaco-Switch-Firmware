# Stock LACP analysis (HRRF_V200.2.4_HC-SWTGW218AS_0319)

> Superseded for planning: RTLPlayground already ships LACP (doc/lacp.md), so the unknown registers below no longer block us. Kept as a reference for the stock behaviour (Marker responder, 3 s short timeout, validity rules).

Behaviour notes only; no vendor code is reproduced. Confidence: **H** verified in the image, **M** inferred from strings/data, **L** guess.

## Image layout (H)
- 20-byte header: magic `12 34 56 78`, payload length `0x000EF5D4`, then two words not yet decoded (`0x000006A5`, `0x0489BDC7`; probably checksum/flags). Code address 0 = file offset `0x14`.
- Reset `LJMP` at addr 0; interrupt vectors at 0x03/0x0B/0x13 are `LJMP`s (first seen at file 0x14/0x17/0x1F/0x27).
- Banked 8051: common area 0x0000-0x7FFF is file chunk 0; each later 32 KB chunk k is mapped at 0x8000-0xFFFF. Bank select is SFR `0x96` (29 trampolines write bank numbers 3..31 once each). Cross-bank calls go through stubs in the common area (`MOV DPTR,#target; LJMP dispatcher`, around 0x2200-0x4000). Chunk-to-bank-number mapping is not yet confirmed.
- Window address of a banked byte = `0x8000 + (file_offset - 0x14) % 0x8000`.
- Data in the image is not all code: the common area is mixed with tables, so linear disassembly of it produces garbage in places.

## Where things are
| item | file offset | note |
|---|---|---|
| `lacp_fsm.c` code | chunk 28, from `0xE0014` | confirmed code (partner/actor field compares, long runs of xdata struct accesses) |
| LACP debug/dump strings | `0xE11C0` (922048-923125) | see FSM below |
| `lacp_fsm.c` path string | 930550 | end of the module's constants |
| init data after path | `0xE3317` | dest MAC `01:80:C2:00:00:02`, then six 16-bit values 1, 30, 3, 90, 60, 2 (M) |
| `saltrunk.c` path | 286809 (chunk 8) | SAL trunk layer |
| `dal_rtl8373_trunk.c` path | 810551 (chunk 24) | DAL trunk layer (RTL8373 core) |
| web UI trunk page | 99000-100200 | `trunk_type` select with LACP option, `/trunk.cgi?page=group` |

## LACP state machines (M, from dump strings)
Per-port variables printed: receive machine, mux machine, periodic machine, oper key, partner key, current_while timer, actor_port_agg_id, an "mosm" value, aggid. Per-aggregator: `PortList` 32-bit bitmask and an `AVS_USING` flag.
- Receive: INITIALIZE, PORT_DISABLED, EXPIRED, LACP_DISABLED, DEFAULTED, CURRENT.
- Mux: DETACHED, WAITING, ATTACHED, COLLECTING, DISTRIBUTING (the five-state 802.3ad-2000 form, collecting and distributing as separate steps).
- Periodic: NO_PERIODIC, FAST_PERIODIC, SLOW_PERIODIC, PERIODIC_TX.
- Timer defaults in the init data match the standard values: fast period 1 s, slow period 30 s, short timeout 3 s, long timeout 90 s, churn detection 60 s, aggregate wait 2 s.
- Packet handling messages: unknown subtype prints "Error LACP Packet Format, subtype=0x%02X"; a Marker PDU that is not a Request is rejected, so the stock switch answers Marker Requests (Marker responder). After a state change it programs the trunk and logs "LACP: set trunk fail, fail number:%d" on error.
- The web status page prints `lacp_link_up` and `lacp_port_enable` as 32-bit port masks, so the FSM is fed by a link-up mask and a per-port LACP-enable mask.

## Trunk rules in stock (H, strings)
2-4 member ports (UI), same speed, duplex, negotiation and VLAN; not a mirror port; no rate limiting; CPU port cannot be a member; a port in one trunk cannot join another. DAL layer errors add: valid hash mask required; two modes, "802.1ad dumb mode" (max 4 ports) and "normal mode" (max 8); the aggregation group is identified by its lowest physical member port ("not the lowest physical port of its aggregation group"). Stock exposes 2 groups.

## RX trap of LACPDUs (L/M)
DAL strings "invalid rma mac address" and "invalid rma action" show the Realtek reserved-multicast (RMA) trap API exists, which is how 01:80:C2:00:00:02 would reach the CPU. The RMA register addresses and the CPU rx hook have **not** been located. The only occurrence of the slow-protocols MAC in the image is the init-data copy above (no direct code reference found; the image uses 3-byte generic pointers and a copy of the data in xdata).

## Not yet known
1. RMA trap register(s) and action value for 01:80:C2:00:00:02.
2. Trunk member mask, trunk group and hash registers (addresses, bit layout).
3. Switch-core register access primitive and the bank number for each chunk.
4. TX path (how a LACPDU is injected: CPU tag format, port selection).
5. xdata addresses of the FSM variables (not needed for our own implementation).

## Suggested next step
Blind disassembly of a 1 MB banked image is expensive. Cheaper route for items 1-3: use RTLPlayground's register read on a unit running the stock image, dump the register space before and after (a) enabling a static trunk and (b) enabling LACP on two ports, and diff. Alternatively load the image in Ghidra with the chunk map above (needs a small script). `tools/stock-re/d51.py` is a minimal 8051 disassembler written for this analysis.
