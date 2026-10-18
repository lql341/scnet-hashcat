#!/usr/bin/env python3
"""Conservative hash-input hygiene checks, not a vulnerability scanner.

Checks line/field bounds and raw control bytes. Kerberos bounds may reject
legitimate long ticket fields. PKZIP parser safety is not implemented: reject
those inputs rather than treating ZIP2/base64 as PKZIP validation. Use a patched
build and trusted inputs; --skip-precheck bypasses this entire heuristic.
Exit status: 0 accepted, 1 rejected, 2 usage/IO error.
"""

from __future__ import annotations

import argparse
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
        if (ord(char) < 32 and char != "\t") or ord(char) == 127:
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

    if mode in PKZIP_MODES or lower.startswith(("$pkzip$", "$pkzip2$")):
        problems.append(f"line {lineno}: PKZIP structural safety is unsupported (CVE-2026-42484); use a patched build with trusted input")

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

    if any(byte < 32 and byte not in (9, 10, 13) or byte == 127 for byte in raw):
        print(json.dumps({"error": "file contains control bytes"}))
        return 1
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print(json.dumps({"error": "hash file must be UTF-8 text"}))
        return 1
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    problems: list[str] = []
    empty = 0
    prefixes: dict[str, int] = {}

    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            empty += 1
            continue
        stripped = line[:-1] if line.endswith("\r") else line
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
        "ok": not problems and bool(prefixes),
    }
    if not prefixes:
        problems.append("hash file has no non-empty hashes")
        report["rejected"] = len(problems)
        report["problems"] = problems[:50]
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
