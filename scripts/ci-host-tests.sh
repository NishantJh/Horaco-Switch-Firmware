#!/bin/sh
# Host-side tests, run inside a Linux container by .github/workflows/host-tests.yml.
# Usage: ci-host-tests.sh <workspace>   (expects <workspace>/rtlplayground checked out)
set -eu
cd "${1:-.}"
apt-get update -qq && apt-get install -y -qq gcc make python3 >/dev/null

# run.sh always exits 0 after the test binary, so check the output.
# "GAP:" lines are known missing features, not failures.
echo "== LACP state machine tests"
sh test/lacp/run.sh "$PWD/rtlplayground" "$PWD/test/lacp" | tee lacp.log
grep -q '^ALL PASSED' lacp.log
! grep -q '^FAIL' lacp.log

echo "== RSTP gap checks (GAP lines are informational)"
sh test/stp_gaps.sh "$PWD/rtlplayground"

echo "== check-dump.py self-test (synthetic dump)"
python3 - <<'PY'
import os
pay = os.urandom(980436)
d = bytearray(b'\xff' * 0x200000); d[:len(pay)] = pay
for n in ('d1.bin', 'd2.bin'): open(n, 'wb').write(d)
open('v.bin', 'wb').write(bytes.fromhex('12345678') + bytes(16) + pay)
open('bad.bin', 'wb').write(b'\xff' * 0x200000)
PY
python3 scripts/check-dump.py d1.bin d2.bin --vendor v.bin
! python3 scripts/check-dump.py d1.bin bad.bin