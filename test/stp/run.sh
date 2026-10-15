#!/bin/sh
# Usage: run.sh <RTLPlayground dir> <test/stp dir>. Builds the unmodified rtl837x_stp.c on host gcc with shim headers.
SRC=${1:-/workspace}
HERE=${2:-/t}
B=/tmp/stp_build
rm -rf $B; mkdir -p $B
cp "$HERE"/shim/*.h "$SRC"/rtl837x_stp.c "$SRC"/rtl837x_stp.h "$HERE"/stp_test.c $B/
gcc -std=gnu11 -fpack-struct=1 -Wno-unknown-pragmas -Wno-attributes -I$B \
  -o $B/stp_test $B/stp_test.c $B/rtl837x_stp.c && $B/stp_test
