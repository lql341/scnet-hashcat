#!/usr/bin/env python3
"""hc-precheck.py - validate a hash file before hashcat ever reads it.

hashcat v7.1.2 has five unreleased CVEs (disclosed 2026-05-01), three of which
are reachable purely by feeding a crafted hash file:

  CVE-2026-42483 (CVSS 9.8)  krb5* parser heap overflow -> RCE/crash
  CVE-2026-42484             PKZIP (17200/17210/17220/17225/17230) parser
                             heap overflow
  CVE-2026-68768             outfile_write() heap overflow

This precheck rejects the syntactic shapes those bugs need. It is a guard,
not a proof: only feed hash files you generated or trust.

Checks (always on):
  * binary content / NUL or control bytes in lines
  * lines longer than --max-line (default 8192)
  * empty or whitespace-only lines (reported, not fatal)

Checks (shape aware):
  * $krb5tgs$/$krb5pa$/$krb5asrep$ lines: every $-delimited field must be
    <= --max-field (default 511) bytes - the CVE-2026-42483 overflow is
    driven by an over-long account_info field.
  * PKZIP modes (--mode 17200/17210/17220/17225/17230): the $zip2$ payload
    must be base64-ish and bounded; over-long payloads are rejected.
  * restore/outfile option injection (CVE-2026-68766) only applies to
    restore files, not hash files - nothing to check here, noted for docs.

Exit status: 0 clean, 1 rejected lines found, 2 usage/IO error.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import sys

KRB5_PREFIXES = ("$krb5tgs$", "$krb5pa$", "$krb5asrep$", "$krb5preauth$")
PKZIP_MODES = {17200, 17210, 17220, 17225, 17230}


def check_line(line: str, lineno: int, mode: int | None, max_line: int, max_field: int):
    """Return a list of problem strings for one line (empty = ok)."""
    problems: list[str] = []
    if len(line.encode("utf-8", "replace")) > max_line:
        problems.append(f"line {lineno}: longer than {max_line} bytes")
        return problems

    # Control bytes (tab allowed) indicate binary or crafted content.
    for char in line:
        if ord(char) < 32 and char != "\t":
            problems.append(f"line {lineno}: control byte 0x{ord(char):02x}")
            break

    lower = line.lower()
    if any(lower.startswith(prefix) for prefix in KRB5_PREFIXES):
        # hashcat splits on '$'; an over-long field (account_info) is the
        # overflow trigger for CVE-2026-42483.
        fields = line.split("$")
        for index, field in enumerate(fields):
            if len(field.encode("utf-8", "replace")) > max_field:
                problems.append(
                    f"line {lineno}: krb5 field #{index} exceeds {max_field} bytes "
                    "(CVE-2026-42483 shape)"
                )
                break

    if mode in PKZIP_MODES and lower.startswith("$zip2$"):
        # PKZIP lines look like: $zip2$*0*3*...*<base64 blobs>. Bound each blob.
        blobs = [part for part in line.split("*") if len(part) > 64]
        for blob in blobs:
            try:
                decoded = base64.b64decode(blob + "=" * (-len(blob) % 4), validate=False)
            except (binascii.Error, ValueError):
                problems.append(f"line {lineno}: PKZIP blob is not valid base64")
                break
            if len(decoded) > 1024 * 1024:
                problems.append(
                    f"line {lineno}: PKZIP blob decodes to >1 MiB "
                    "(CVE-2026-42484 shape)"
                )
                break

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("hashes", help="hash file to validate")
    parser.add_argument("--mode", type=int, default=None, help="hashcat -m mode")
    parser.add_argument("--max-line", type=int, default=8192)
    parser.add_argument("--max-field", type=int, default=511)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    try:
        with open(args.hashes, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    if b"\x00" in raw:
        print(json.dumps({"error": "file contains NUL bytes; not a text hash file"}))
        return 1

    text = raw.decode("utf-8", "replace")
    lines = text.splitlines()
    problems: list[str] = []
    empty = 0
    prefixes: dict[str, int] = {}

    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            empty += 1
            continue
        stripped = line.strip()
        prefix = stripped.split("$")[1] if stripped.startswith("$") and "$" in stripped[1:] else "(bare)"
        key = prefix.rstrip("0123456789") if prefix != "(bare)" else "(bare)"
        prefixes[key] = prefixes.get(key, 0) + 1
        problems.extend(check_line(stripped, lineno, args.mode, args.max_line, args.max_field))

    report = {
        "file": args.hashes,
        "lines": len(lines),
        "empty_lines": empty,
        "hash_types": prefixes,
        "rejected": len(problems),
        "problems": problems[:50],
        "ok": not problems,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"file          : {args.hashes}")
        print(f"lines         : {len(lines)} (empty: {empty})")
        print(f"hash types    : {', '.join(f'{k} x{v}' for k, v in prefixes.items()) or 'unknown'}")
        if problems:
            print(f"REJECTED      : {len(problems)} problem(s)")
            for problem in problems[:20]:
                print(f"  - {problem}")
            print("Do not feed this file to hashcat without cleaning it.")
        else:
            print("result        : OK - no dangerous shapes detected")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
