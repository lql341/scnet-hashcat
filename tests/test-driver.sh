#!/usr/bin/env bash
# Offline tests for the hc driver - argument parsing and local subcommands.
# No cluster access, no credentials.

set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
HC="$ROOT/scripts/hc"
FAIL=0

check() {
  local label="$1" expected_rc="$2" actual_rc="$3" pattern="$4" output="$5"
  if [ "$actual_rc" != "$expected_rc" ]; then
    echo "FAIL: $label (rc=$actual_rc, want $expected_rc)"; FAIL=1; return
  fi
  if [ -n "$pattern" ] && ! printf '%s' "$output" | grep -q "$pattern"; then
    echo "FAIL: $label (output missing '$pattern')"; FAIL=1; return
  fi
  echo "ok: $label"
}

OUT="$(bash "$HC" version)"; check "version" 0 $? "hc 0.1.0" "$OUT"
OUT="$(bash "$HC" --help)"; check "help" 0 $? "crack" "$OUT"
OUT="$(bash "$HC" crack 2>&1)"; check "crack requires --hashes" 2 $? "hashes is required" "$OUT"
OUT="$(bash "$HC" status 2>&1)"; check "status requires job id" 2 $? "job id required" "$OUT"

TMP="$(pwd)/.test-tmp-$$"
mkdir -p "$TMP"
printf 'a\nb\nc\nd\ne\n' > "$TMP/dict.txt"
OUT="$(bash "$HC" split --input "$TMP/dict.txt" --parts 2 --outdir "$TMP/split")"
check "split" 0 $? "2 parts" "$OUT"
check "split files" 0 $? "" "$(ls "$TMP/split")"
[ "$(ls "$TMP/split" | wc -l)" = "2" ] || { echo "FAIL: split produced $(ls "$TMP/split" | wc -l) parts"; FAIL=1; }
rm -rf "$TMP"

# precheck on a generated hostile file must fail through the driver path
TMP2="$(pwd)/.test-tmp2-$$"
mkdir -p "$TMP2"
printf '$krb5tgs$23$*u$r$%s\n' "$(python3 -c 'print("A"*600)')" > "$TMP2/evil.txt"
OUT="$(bash "$HC" precheck --hashes "$TMP2/evil.txt" 2>&1)"
check "precheck rejects evil krb5" 1 $? "CVE-2026-42483" "$OUT"
rm -rf "$TMP2"

if [ "$FAIL" = "0" ]; then echo "driver tests: all passed"; exit 0; else exit 1; fi
