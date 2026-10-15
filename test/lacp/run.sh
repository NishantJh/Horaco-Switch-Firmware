#!/bin/sh
# Usage: run.sh <RTLPlayground dir> <test dir>. Copies the unmodified rtl837x_lacp.[ch] next to the
# shim headers (quote-includes search the file's own dir first), builds with host gcc, runs the tests.
SRC=${1:-/workspace}
HERE=${2:-/t}
B=/tmp/lacp_build
rm -rf $B; mkdir -p $B
cp "$HERE"/shim/*.h "$SRC"/rtl837x_lacp.c "$SRC"/rtl837x_lacp.h "$HERE"/lacp_test.c $B/
gcc -std=gnu11 -fpack-struct=1 -Wno-unknown-pragmas -Wno-attributes -I$B \
  -o $B/lacp_test $B/lacp_test.c $B/rtl837x_lacp.c && $B/lacp_test
echo
echo "-- source-level gap checks (no hook to test behaviourally) --"
for w in churn marker speed duplex; do
  n=$(grep -ci "$w" "$SRC/rtl837x_lacp.c")
  if [ "$n" -eq 0 ]; then echo "GAP:  '$w' not referenced in rtl837x_lacp.c"; else echo "ok:   '$w' referenced ($n)"; fi
done
