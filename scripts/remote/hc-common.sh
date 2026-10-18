#!/usr/bin/env bash
log() { echo "[hc $(date '+%H:%M:%S')] $*"; }
# 0 = recovered, 1 = exhausted. Abort, runtime limit, and negative error fail.
hashcat_rc_ok() { [ "$1" = 0 ] || [ "$1" = 1 ]; }
