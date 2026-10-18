#!/usr/bin/env bash
# hc-common.sh - shared helpers for scnet-hashcat remote scripts.

log() {
  echo "[hc $(date '+%H:%M:%S')] $*"
}

# hashcat exit codes:
#   0 = all hashes cracked, 1 = exhausted (normal end), 2 = aborted,
#   3 = error, 4 = ... treat >=3 as failure, 0/1 as success.
hashcat_rc_ok() {
  [ "$1" -lt 3 ]
}
