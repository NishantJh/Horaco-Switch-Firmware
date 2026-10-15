# No-hardware test loop (Windows)

Never flash the switch from this loop. Never commit `stock/*.bin` or built images.

## Toolchain (installed 2026-10-15)
- Docker Desktop (must be running) for the SDCC 4.5 build.
- JDK 21 (Temurin, winget `EclipseAdoptium.Temurin.21.JDK`), set `JAVA_HOME` to `C:\Program Files\Eclipse Adoptium\jdk-21*` before running Ghidra headless.
- Ghidra 12.1.4 unzipped to `D:\Claude projects\tools\ghidra_12.1.4_PUBLIC`.
- RTLPlayground cloned to `D:\Claude projects\RTLPlayground`. Board: `MACHINE=SWTG018AS_A_V_2_0`.

## Steps
1. `scripts/build.ps1` -> `output/SWTG018AS_A_V_2_0/rtlplayground-*.bin` (512 KB, builds OK).
2. `scripts/ghidra_import.ps1 -Bin <that .bin>` -> project `D:\Claude projects\ghidra-proj`, program `rtlp_code.bin`
   (skips 2-byte header, 0x10000 bytes at 0x0000, `8051:BE:16:default`, per RTLPlayground doc/ghidra.md).

## Limits
Ghidra is static analysis only: it cannot execute the image. Only bank 0/1 are loaded.
LACP source: `rtl837x_lacp.c` (state machine: `lacp_in`, `lacp_send`, `lacp_step`, `lacp_timers`, `lacp_lag_set`).
Feature testing without hardware needs an 8051 emulator with faked registers, or a host build of the LACP logic fed with crafted LACPDUs. Not built yet.

## Host-side LACP test (works, 2026-10-15)
`test/lacp/` compiles the unmodified `rtl837x_lacp.c` with host gcc (inside the Docker image) against shim headers
and drives it with crafted LACPDUs and a fake clock. Run:

    docker run --rm -v 'D:\Claude projects\RTLPlayground:/workspace' -v 'D:\Claude projects\repo\test\lacp:/t' rtlplayground-dev sh -c "tr -d '\r' </t/run.sh >/tmp/r.sh; sh /tmp/r.sh /workspace /t"

Covers: engine on/off + RMA trap, TX LACPDU format, partner learning, SYNC/COLLECTING/DISTRIBUTING handshake, hardware LAG member mask,
partner timeout, mismatched partner system, loopback and non-LAG port frames. All 21 checks pass against the current RTLPlayground main.
Not covered: real chip behaviour (trap registers, tag format), only the state machine logic.
