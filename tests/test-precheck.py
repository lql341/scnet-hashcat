#!/usr/bin/env python3
"""Offline tests for hc-precheck.py - no cluster, no credentials needed."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

PRECHECK = Path(__file__).resolve().parent.parent / "scripts" / "remote" / "hc-precheck.py"


def run_precheck(path: Path, mode: int | None = None) -> tuple[int, str]:
    cmd = [sys.executable, str(PRECHECK), str(path)]
    if mode is not None:
        cmd += ["--mode", str(mode)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        clean = root / "clean.txt"
        clean.write_text(
            "8743b52063cd84097a65d1633f5c74f5\n"
            "5f4dcc3b5aa765d61d8327deb882cf99\n",
            encoding="utf-8",
        )
        rc, out = run_precheck(clean, 0)
        if rc != 0 or "OK" not in out:
            failures.append(f"clean MD5 file should pass, got rc={rc}")

        krb_ok = root / "krb-ok.txt"
        krb_ok.write_text(
            "$krb5tgs$23$*user$realm$" + "B" * 200 + "\n", encoding="utf-8"
        )
        rc, _ = run_precheck(krb_ok, 0)
        if rc != 0:
            failures.append(f"krb5 with bounded fields should pass, got rc={rc}")

        krb_evil = root / "krb-evil.txt"
        krb_evil.write_text(
            "$krb5tgs$23$*user$realm$" + "A" * 600 + "\n", encoding="utf-8"
        )
        rc, out = run_precheck(krb_evil, 0)
        if rc != 1 or "CVE-2026-42483" not in out:
            failures.append(f"over-long krb5 field must be rejected, got rc={rc}")

        long_line = root / "long.txt"
        long_line.write_text("x" * 9000 + "\n", encoding="utf-8")
        rc, out = run_precheck(long_line, 0)
        if rc != 1 or "longer than" not in out:
            failures.append(f"over-long line must be rejected, got rc={rc}")

        binary = root / "binary.txt"
        binary.write_bytes(b"hash\x00with-nul\n")
        rc, out = run_precheck(binary, 0)
        if rc != 1 or "NUL" not in out:
            failures.append(f"NUL bytes must be rejected, got rc={rc}")

        zip_ok = root / "zip-ok.txt"
        zip_ok.write_text("$zip2$*0*3*2*binary*" + "A" * 100 + "*" + "C" * 100 + "\n", encoding="utf-8")
        rc, _ = run_precheck(zip_ok, 17200)
        if rc != 0:
            failures.append(f"bounded PKZIP line should pass, got rc={rc}")

    if failures:
        print("FAILED:")
        for item in failures:
            print("  -", item)
        return 1
    print("precheck tests: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
