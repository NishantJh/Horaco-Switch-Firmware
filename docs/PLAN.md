# Plan (draft, awaiting owner edits)

1. Prepare (nothing is flashed until a working build exists): dump both flash chips (SOIC-8 clip), keep stock image, build RTLPlayground (SDCC 4.5 / Docker), flash second chip.
2. LACP: RTLPlayground already implements dynamic 802.3ad (`doc/lacp.md`: software Receive/Selection/Mux machines on the 8051, RMA trap of 01:80:C2:00:00:02, up to 4 LACP groups, `lag <n> lacp <ports>`, web page, tested against a Linux bond). Nothing to build from scratch; stock disassembly is no longer needed (see docs/stock-lacp-analysis.md for what was found). Work: build and validate it on this board, then close its known limits: no churn detection, no Marker responder (stock has one), coupled mux, selection compares partner system but not key, member compatibility unchecked (RTLPlayground issue #377), timeout 4 s instead of 3 s.
3. Remaining gaps: VLAN modes (access/trunk/native), fuller RSTP, config backup/restore.
4. Web UI redesign within 8051 flash/RAM limits.

Open: confirm flash layout (doc says 2MB and also 4Mbit; two chips with front selector?), UART log of stock with a LAG partner.
