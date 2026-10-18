#!/usr/bin/env bash
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HC="$ROOT/scripts/hc"
[ "$(bash "$HC" version)" = "hc $(tr -d '\r\n' < "$ROOT/VERSION")" ]
bash "$HC" --help >/dev/null
if bash "$HC" crack >/dev/null 2>&1; then exit 1; fi
if bash "$HC" status >/dev/null 2>&1; then exit 1; fi
bash "$HC" crack --hashes "$ROOT/tests/data/hashes.txt" --dict "$ROOT/tests/data/dict.txt" --dry-run >/dev/null
if bash "$HC" crack --nodes >/dev/null 2>&1; then exit 1; fi
echo 'driver wrapper tests: all passed'
