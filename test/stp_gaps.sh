#!/bin/sh
# Source-level RSTP gap checks on rtl837x_stp.c. Usage: stp_gaps.sh <RTLPlayground dir>
F="${1:-.}/rtl837x_stp.c"
chk() { # label, grep -E pattern, expect: present|absent-means-gap
  if grep -Eqi "$2" "$F"; then echo "ok:   $1"; else echo "GAP:  $1"; fi
}
chk "BPDU Proposal flag handled"                 'BPDU_FLAG_PROPOSAL|PROPOSAL'
chk "BPDU Agreement flag handled"                'BPDU_FLAG_AGREEMENT|AGREEMENT'
chk "Alternate/Backup port role (flags 0b01)"    'BPDU_ROLE_ALTERNATE|BPDU_ROLE_BACKUP|ROLE_ALT'
chk "TCN BPDU transmitted toward root"           'bpdu_type *= *BPDU_TYPE_TCN|STP_O->bpdu_type *= *BPDU_TYPE_TCN'
chk "TC flag set in own BPDUs"                   'BPDU_FLAG_TC[^A]|BPDU_FLAG_TC\b'
chk "TCN received and acked (regression)"        'BPDU_FLAG_TCACK'
