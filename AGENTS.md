# Agent guide: Horaco-Switch-Firmware

Docs, plans, host-side tests and stock-firmware analysis for the HC-SWTGW218AS firmware project.

## Read first

`docs/CONTEXT.md` (one page: hardware, repos, plan status, open PRs). Open other docs only when the task needs them.

## Where things live

- `docs/`: `PLAN.md` (plan order), `backup-and-rollback.md` (SPI dump and rollback), `stock-firmware-notes.md`, `stock-feature-baseline.md`, `test-loop.md`, `ubiquiti-feature-feasibility.md`, `webui/` (mock screenshots).
- `test/lacp/`, `test/stp/`, `test/stp_gaps.sh`: host-side tests against the RTLPlayground code.
- `test/webui-mock/`: mock switch and Playwright screenshot script.
- `scripts/`: dump checker (`check-dump.py`).
- `.github/workflows/host-tests.yml`: CI for this repo.
- `stock/`: local vendor images, git-ignored.

## Do not read

- `stock/` and any `*.bin`, `*.img` or flash dump. They are large vendor binaries.
- `docs/webui/*.png` unless the task is UI work.
- Do not read the whole RTLPlayground fork. Open the specific file you need by path, or search for a symbol.

## Build and test

- Host tests: `test/lacp/run.sh` and `test/stp_gaps.sh`. `run.sh` exits 0 even on failure, so CI checks its output for `^ALL PASSED` and no `^FAIL`. `GAP:` lines are informational, not failures.
- Firmware builds happen in the RTLPlayground fork (see its `AGENTS.md`).
- Builds and tests run on Nishant's Windows PC or in CI.

## Rules

- All changes go through a PR. No direct pushes to `main`, which is protected.
- Merge the fork PR before its matching test PR here, or CI tests the wrong code.
- Never commit stock vendor firmware.
- Never flash the switch. Nishant flashes only after tests pass and a full SPI backup exists (`docs/backup-and-rollback.md`).
- Firmware code goes to the RTLPlayground fork. Keep it upstreamable.
