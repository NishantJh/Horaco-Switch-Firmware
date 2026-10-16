# Review: Gemini "Realtek LACP Implementation Guide"

Verdict: nothing in it changes the plan. Its premise is wrong for this device, and its code is not usable. Two of its ideas are already in our plan.

## Claims vs. what we know

| Guide claim | Reality | Impact |
|---|---|---|
| Chip is RTL838x/RTL839x | Device is RTL8373-class (RTL8273N + RTL8224N), 8051 core (see PLAN.md, stock-firmware-notes.md). RTL838x/9x are MIPS switches with a Linux/OpenWrt DSA driver. | Register layout, drivers and files it names do not apply |
| Look in `rtl838x_switch.c` / `rtl83xx_api.c` | Those are OpenWrt Linux kernel files. RTLPlayground has no Realtek SDK and no such files. | Searches would find nothing |
| `rtl838x_mgmt_macTrap_set`, `rtk_trunk_port_set`, `rtk_portmask_t`, `RTK_PORTMASK_PORT_SET` | SDK-style names (rtk_*) exist only in Realtek's closed SDK. Not in the repo, and the 8051 build is SDCC with direct XDATA register writes. `macTrap_set` and `RTL838X_TRAP_LACP 2` look invented. | Cannot be called. The "avoid registers" shortcut does not exist for us |
| "Native SDK abstractions already reside in the driver base" | The stock image does contain the SDK-derived code (`dal_rtl8373_trunk.c`, `saltrunk.c`, `lacp_fsm.c`), but only as a closed binary. | This is the reason for our stock-analysis route, not an alternative to it |
| LACPDU trap to CPU at 01:80:C2:00:00:02 | Correct goal and already step 2 of PLAN.md ("verify the chip can trap slow-protocol frames"). Needs the real RTL8373 register, still unknown. | Already planned |
| 3-state state machine, BSS arrays, no malloc | Static arrays are right for 8051. But 802.3ad needs actor and partner state, sync/collecting/distributing, churn handling, periodic Tx (fast 1 s, slow 30 s) and a real LACPDU transmit path. The guide has no Tx at all, so the partner never forms a LAG. | Use only the "static memory" principle |
| Marks Collecting/Distributing on first LACPDU received | Wrong: that skips partner sync handshake and can flap or loop. Also uses `uint32_t` ms timers and `int i` loops that are costly on 8051. | Reject |
| Timeout purge: strip link from trunk when LACPDUs stop | Correct (3x interval). Standard behaviour. | Keep, in our own FSM |
| "16Mbit storage" | Matches 2MB flash. | n/a |

## What to keep

- Trap LACPDU, keep per-port state in static XDATA, expire on timeout: already the plan.
- Nothing new on the blocker. The missing piece is still the RTL8373 register map for trap-to-CPU and trunk member/hash config. Candidates are unchanged: offline analysis of `dal_rtl8373_trunk.c` code in the stock image (Ghidra), and RTLPlayground's existing static trunk setup.

## Risk

Handing this guide to a coding agent would produce code calling functions that do not exist, plausibly written. Do not use it as a brief.
