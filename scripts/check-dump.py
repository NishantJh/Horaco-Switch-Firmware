#!/usr/bin/env python3
"""Sanity-check SPI flash dumps of the HC-SWTGW218AS before trusting them as a rollback image.

Usage:
  python scripts/check-dump.py dump1.bin [dump2.bin dump3.bin] [--vendor stock/HRRF_xxx.bin]

Checks (see docs/backup-and-rollback.md):
  - every read has the expected size (2 MiB for the W25Q16) and all reads are identical
  - the dump is not blank (all 0xFF) or stuck (all 0x00)
  - with --vendor: the vendor update image payload (after its 20-byte header) matches flash from 0
  - prints the 6 bytes at 0x1FC000, where RTLPlayground's managed-board profiles read the MAC
  - prints which 64 KiB blocks hold data, so the flash layout is on record

Exit code 0 = all checks passed, 1 = something needs a look. Standard library only.
"""
import argparse
import hashlib
import sys

FLASH_SIZE = 2 * 1024 * 1024
VENDOR_HEADER_LEN = 0x14
VENDOR_MAGIC = bytes.fromhex("12345678")
MAC_OFFSET = 0x1FC000
BLOCK = 0x10000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dumps", nargs="+", help="one or more reads of the same chip")
    ap.add_argument("--vendor", help="vendor update image (.bin) to compare against")
    ap.add_argument("--size", type=lambda s: int(s, 0), default=FLASH_SIZE, help="expected size (default 2 MiB)")
    args = ap.parse_args(argv)

    ok = True
    reads = []
    for path in args.dumps:
        with open(path, "rb") as f:
            reads.append(f.read())
        print(f"{path}: {len(reads[-1])} bytes, sha256 {sha256(reads[-1])}")

    dump = reads[0]
    if any(len(r) != args.size for r in reads):
        print(f"FAIL: expected {args.size} bytes per read")
        ok = False
    if len(reads) < 2:
        print("WARN: only one read; take at least two and compare before trusting the dump")
    elif any(r != dump for r in reads[1:]):
        print("FAIL: reads differ; reseat the clip and read again")
        ok = False
    else:
        print(f"OK: {len(reads)} reads identical")

    if dump.count(0xFF) == len(dump) or dump.count(0x00) == len(dump):
        print("FAIL: dump is blank (all 0xFF or all 0x00); the programmer did not read the chip")
        ok = False

    if args.vendor:
        with open(args.vendor, "rb") as f:
            vendor = f.read()
        if vendor[:4] != VENDOR_MAGIC:
            print(f"WARN: vendor image does not start with {VENDOR_MAGIC.hex()}")
        payload = vendor[VENDOR_HEADER_LEN:]
        region = dump[:len(payload)]
        same = sum(1 for a, b in zip(payload, region) if a == b)
        print(f"vendor payload {len(payload)} bytes vs flash 0x0-0x{len(payload):x}: "
              f"{same * 100.0 / max(len(payload), 1):.2f}% identical")
        if region == payload:
            print("OK: flash holds the same stock build as the vendor image")
        else:
            first = next((i for i, (a, b) in enumerate(zip(payload, region)) if a != b), len(region))
            print(f"WARN: first difference at 0x{first:x}; the unit may run another stock build, "
                  "keep the dump as the reference either way")

    if len(dump) >= MAC_OFFSET + 6:
        mac = dump[MAC_OFFSET:MAC_OFFSET + 6]
        valid = mac[0] != 0xFF and not (mac[0] & 0x03) and any(mac[:3])
        print(f"bytes at 0x{MAC_OFFSET:X}: {':'.join(f'{b:02x}' for b in mac)} "
              f"({'looks like a MAC, compare with the label' if valid else 'no MAC here'})")

    used = [i for i in range(0, len(dump), BLOCK) if dump[i:i + BLOCK].count(0xFF) != len(dump[i:i + BLOCK])]
    print("64 KiB blocks with data: " + (", ".join(f"0x{i:06x}" for i in used) or "none"))

    print("RESULT: " + ("PASS" if ok else "CHECK FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
