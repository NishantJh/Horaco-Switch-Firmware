# Plan (draft, awaiting owner edits)

1. Prepare: dump both flash chips (SOIC-8 clip), keep stock image, build RTLPlayground (SDCC 4.5 / Docker), flash second chip.
2. Dynamic LACP (802.3ad): LACPDU RX/TX state machine, hardware trunk add/remove on link events. Stock `lacp_fsm.c` is the behavioural reference. First verify the chip can trap slow-protocol frames to the 8051.
3. Remaining gaps: VLAN modes (access/trunk/native), fuller RSTP, config backup/restore.
4. Web UI redesign within 8051 flash/RAM limits.

Open: confirm flash layout (doc says 2MB and also 4Mbit; two chips with front selector?), UART log of stock with a LAG partner.
