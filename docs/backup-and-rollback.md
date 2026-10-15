# Backup and rollback (HC-SWTGW218AS)

How to keep a way back to the stock firmware before RTLPlayground goes on the switch.
Nothing here is done by Claude: every hardware step is done by hand.

**Rule: do not install RTLPlayground until a full SPI flash dump exists and
`scripts/check-dump.py` says PASS on it.**

## What each route can and cannot do

| Route | Backs up | Restores | Notes |
|---|---|---|---|
| Stock web UI, Tools > config backup/restore | Settings only (VLANs, trunks, IP, ...) | Settings into stock firmware only | Not a flash image. Useless once RTLPlayground is installed. |
| Stock web UI, Tools > firmware upgrade | nothing | A vendor update `.bin` (stock to stock), or RTLPlayground's `rtlplayground_oem_upgrade.bin` | This is how RTLPlayground gets installed the first time. |
| Vendor `.bin` on the PC (`HRRF_V200.2.4_HC-SWTGW218AS_0319`, 980,456 bytes) | n/a | Stock to stock only | 20-byte header (`12 34 56 78`) plus a 980,436-byte payload that maps to flash from 0. It holds no per-unit data (MAC, saved config), so it is not a backup of *this* switch. |
| RTLPlayground web UI, firmware update | Its own config (download) | A newer or older RTLPlayground image | CRC-checked upload; a bad CRC is rejected and the old image keeps running. Cannot take the stock image (see below). |
| UART (`J1`) | nothing | nothing | Console for watching boot and the installer. No serial image loader is documented, so it is a diagnostic tool, not a recovery route. |
| **SPI programmer + SOIC-8 clip** on the W25Q16 | **Full 2 MiB image** | **Anything, including a bricked unit** | The only real backup and the only way back to stock. |

### Why there is no software way back to stock

RTLPlayground's updater (`httpd/httpd.c`, `check_and_flash_update_image()` in `rtlplayground.c`)
stages an upload at `0x80000`, refuses anything past `0x100000`, and on reboot copies only
`0x0`-`0x6FFFF` to the start of flash (its config lives at `0x70000`). The stock payload is
about 957 KB, so it neither fits the slot nor gets copied in full, and it is not in the format
RTLPlayground's updater expects. Going back to stock therefore means writing the dump with the
programmer. (A reverse "stock restorer" image, like the installer in reverse, is possible in
principle but does not exist and would be untested; it is not part of this plan.)

### What the first install overwrites

`installer/installer.c` (shipped inside `rtlplayground_oem_upgrade.bin`) copies 120 sectors of
4 KiB, i.e. `0x00000`-`0x77FFF`, over the start of flash and resets. The rest of the stock image
and the top of flash are left as they were. There is no fallback during that copy: a power cut
while it runs leaves a unit that only the programmer can fix.

## What to buy

| Item | Why | Notes |
|---|---|---|
| CH341A USB SPI programmer **that runs at 3.3 V** | Read and write the flash chip | The common black CH341A board drives its data lines at 5 V; the W25Q16JV is rated 3.6 V max. Buy a 3.3 V variant (often sold as "v1.7" with a 3.3/5 V switch) or a CH347-based one. A Raspberry Pi Pico running `pico-serprog` with `flashrom` also works. |
| SOIC-8 test clip with ribbon cable | Connect to the chip without desoldering | Pomona 5250 or the usual clone. Check the chip body width (150 or 208 mil) when the case is open; most clones fit both. |
| 3.3 V USB-to-UART adapter (CP2102, CH340 or FT232) and jumper wires | Watch stock boot, the installer and RTLPlayground | Optional for the backup, strongly recommended for the first install. A 4-pin 2.54 mm header if `J1` is unpopulated. |

Windows software: NeoProgrammer or AsProgrammer for the CH341A, or `flashrom`
(`flashrom -p ch341a_spi -r dump1.bin`). IMSProg, which RTLPlayground's README mentions, is Linux-only.

## Procedure

### A. On stock, without opening the case

1. Open `http://192.168.2.1` (admin/admin). Screenshot every page you have changed, plus
   System > info (firmware version, hardware version, MAC).
2. Tools > config backup: save the file next to the vendor `.bin`. It restores settings into
   stock firmware only.
3. Keep the vendor `.bin` under `stock/` in this repo (git-ignored) and one more copy off the PC.
   Never commit it.

### B. Full flash dump (case open, power unplugged)

1. Unplug power and every network cable. Open the case.
2. Photograph both sides of the PCB. Write down:
   - the silkscreen (for example `SWTG018AS-A-V2.0.1_...` or `SWTG118AS-V2.x`); this picks the
     RTLPlayground machine profile (see "Open questions");
   - the flash chip marking (expected `25Q16JVSIQ`, Winbond W25Q16JV) and pin 1 (dot);
   - whether there is a **second flash chip or a selector switch**. RTLPlayground's
     SWTG018AS-A page mentions one; if this board has it, it is the easiest rollback there is
     (stock on one chip, RTLPlayground on the other);
   - where `J1` (UART) is and whether it has pins.
3. Set the programmer to 3.3 V. Clip onto the chip with the red wire on pin 1, then plug the
   programmer into USB. The switch's power LED may light: the programmer is powering the board,
   which is expected.
4. Detect the chip. Expect Winbond W25Q16 (JEDEC ID `EF 40 15`), 2 MiB. If it is not detected,
   unplug, reseat the clip and retry. Do not erase or write anything.
5. Read the chip **three times** to `dump1.bin`, `dump2.bin`, `dump3.bin`.
6. Check the reads from the repo root:

   ```
   python scripts/check-dump.py dump1.bin dump2.bin dump3.bin --vendor stock/<vendor>.bin
   ```

   It needs `RESULT: PASS` (2 MiB each, all three identical, not blank). It also reports:
   - whether flash from 0 matches the vendor payload (expected if the unit runs that build;
     a mismatch is a note, not a failure, since the unit may run a different stock build);
   - the 6 bytes at `0x1FC000`, where RTLPlayground's managed-board profiles read the MAC.
     Compare them with the label and the System info screenshot;
   - which 64 KiB blocks hold data, to keep the stock flash layout on record.
7. Rename the good read to something like `hc-swtgw218as-stock-full-YYYYMMDD-<first 8 of sha256>.bin`
   and keep three copies (PC, cloud, USB stick). Never commit it.
8. Use the programmer's **verify** (compare chip to file) once against the saved dump. This
   proves the clip and software can talk to the chip the same way a restore will, without writing.
9. Unclip, close the case, power up, and confirm stock still boots and the web UI answers.

### C. First RTLPlayground install (only after a build passes the tests)

Nishant does this; see `docs/test-loop.md` for the build.

1. Build for the machine profile chosen from the silkscreen, then `cd installer && make`.
   Upload `installer/output/rtlplayground_oem_upgrade.bin` through stock Tools > firmware upgrade.
2. If UART is wired, watch it: the installer prints at 57600 baud, RTLPlayground at 115200 8N1.
   Do not cut power until RTLPlayground's web UI answers (default `192.168.10.247`, password
   `1234`, unless `config.txt` sets otherwise).
3. Check the MAC it reports, every RJ45 port, the SFP+ port and the LEDs.

### D. Rolling back

| Situation | What to do |
|---|---|
| A newer RTLPlayground build misbehaves but boots | Upload the previous good `output/rtlplayground-*.bin` through RTLPlayground's firmware update page. |
| No web UI, no boot, or you want stock back | Unplug, clip on, **erase, write the full dump, verify**, unclip, power up. Stock comes back with its MAC and the settings it had on the day of the dump. Restore a newer stock config file through Tools if needed. |
| The dump is lost (should not happen) | Last resort, untested: erase and write only `0x000000`-`0x0EFFFF` with the vendor payload (the `.bin` minus its first 20 bytes) so the `0x1FC000` area survives; most programmer tools erase the whole chip unless told to use a range. Expect the stock settings to be reset. |

## Open questions (answer them during step B)

- **Which machine profile.** RTLPlayground has `SWTG018AS_A_V_2_0` (no MAC offset, so it makes up
  a locally administered MAC), `SWTGW218AS` and `PCB_SWTG018AS_V2_1_0` (both read the MAC at
  `0x1FC000`). The silkscreen and the dump's bytes at `0x1FC000` decide it.
- **One chip or two.** See B2.
- **Stock UART speed.** RTLPlayground's notes say 9600 on the unmanaged SWTG018AS-A; unverified on
  this unit. The `J1` pinout there (1 3V3, 2 GND, 3 RX, 4 TX) also needs checking on this board;
  never connect the 3V3 pin from the adapter.
- **Where stock keeps its settings.** The block list from `check-dump.py` shows which areas outside
  the image hold data; a second dump after changing one stock setting would pinpoint it (optional).
