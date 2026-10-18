#!/usr/bin/env bash
# One coordinator splits once, then launches one rank per allocated node.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/hc-common.sh"
ORIGINAL=("$@")
HASHES= DICT= RULES= MASK= MODULE= MODULEFILES= OUTDIR= ATTACK=0 MODE=0 NODES=1 EXPECTED=1 RANK_MODE=0
EXTRA=()
while [ $# -gt 0 ]; do
  case "$1" in
    --rank) RANK_MODE=1; shift ;;
    --hashes|--dict|--rules|--mask|--module|--modulefiles|--outdir|--attack|--mode|--nodes|--expected-devices|--extra)
      [ $# -ge 2 ] || { echo "missing value: $1" >&2; exit 2; }
      case "$1" in
        --hashes) HASHES="$2" ;; --dict) DICT="$2" ;; --rules) RULES="$2" ;;
        --mask) MASK="$2" ;; --module) MODULE="$2" ;; --modulefiles) MODULEFILES="$2" ;;
        --outdir) OUTDIR="$2" ;; --attack) ATTACK="$2" ;; --mode) MODE="$2" ;;
        --nodes) NODES="$2" ;; --expected-devices) EXPECTED="$2" ;; --extra) EXTRA+=("$2") ;;
      esac
      shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[[ "$NODES" =~ ^[1-9][0-9]*$ && "$MODE" =~ ^[0-9]+$ && "$EXPECTED" =~ ^[1-9][0-9]*$ ]] || exit 2
[ -n "$OUTDIR" ] && [ -f "$HASHES" ] && [ -n "$MODULE" ] || exit 2
case "$ATTACK" in
  0) [ -f "$DICT" ] || exit 2 ;;
  1) [ -f "$DICT" ] && [ -f "$RULES" ] || exit 2 ;;
  3) [ -n "$MASK" ] && [ "$NODES" = 1 ] || exit 2 ;;
  *) exit 2 ;;
esac
mkdir -p "$OUTDIR" || exit 1

if [ "$RANK_MODE" = 1 ]; then
  RANK="${SLURM_PROCID:-0}"
  exec > "$OUTDIR/rank.$RANK.log" 2>&1
  T0=$(date +%s)
  RC=-1 ERROR= CRACKED=0
  finish() {
    if [ "$RC" = -1 ] && [ -z "$ERROR" ]; then ERROR='rank interrupted before hashcat finished'; fi
    local tmp="$OUTDIR/rank.$RANK.kv.tmp"
    printf 'rank=%s\nhost=%s\nattack=%s\nhashcat_rc=%s\ncracked=%s\nelapsed_s=%s\nerror=%s\n' \
      "$RANK" "$(hostname)" "$ATTACK" "$RC" "$CRACKED" "$(( $(date +%s) - T0 ))" "$ERROR" > "$tmp"
    mv "$tmp" "$OUTDIR/rank.$RANK.kv"
  }
  trap finish EXIT
  fail() { ERROR="$1"; echo "$ERROR" >&2; exit 1; }
  log "rank=$RANK allocated_devices=${HIP_VISIBLE_DEVICES:-unset}"
  MYDICT="$DICT" MYRULES="$RULES"
  if [ "$NODES" -gt 1 ]; then
    PART="$OUTDIR/part.$(printf '%05d' "$RANK")"
    if [ "$ATTACK" = 1 ]; then MYRULES="$PART"; else MYDICT="$PART"; fi
    [ -f "$PART" ] || fail 'slice missing'
    if [ ! -s "$PART" ]; then RC=1; log 'empty slice: no work'; exit 0; fi
  fi
  type module >/dev/null 2>&1 || fail 'module function unavailable; use a login shell'
  if [ -n "$MODULEFILES" ]; then module use "$MODULEFILES" || fail 'module use failed'; fi
  module load "$MODULE" || fail 'module load failed'
  HC=$(command -v hashcat) || fail 'hashcat not found after module load'
  "$HC" -I > "$OUTDIR/devices.$RANK.txt" 2>&1 || fail 'device enumeration failed'
  DEVICES=$(grep -c 'Backend Device ID' "$OUTDIR/devices.$RANK.txt" || true)
  [ "$DEVICES" -ge "$EXPECTED" ] || fail 'fewer devices visible than requested'
  ARGS=(-a 0 -m "$MODE" "$HASHES")
  if [ "$ATTACK" = 3 ]; then ARGS=(-a 3 -m "$MODE" "$HASHES" "$MASK"); else ARGS+=("$MYDICT"); fi
  [ -z "$MYRULES" ] || ARGS+=(-r "$MYRULES")
  # Bash 4.2 on CentOS treats an empty array expansion as unbound with set -u.
  if [ "${#EXTRA[@]}" -gt 0 ]; then ARGS+=("${EXTRA[@]}"); fi
  "$HC" "${ARGS[@]}" --potfile-path "$OUTDIR/pot.$RANK" -o "$OUTDIR/cracked.$RANK" \
    --outfile-format 1 --session "hc-${SLURM_JOB_ID:-local}-$RANK" --restore-disable --logfile-disable
  RC=$?
  [ ! -f "$OUTDIR/pot.$RANK" ] || CRACKED=$(grep -c . "$OUTDIR/pot.$RANK" || true)
  hashcat_rc_ok "$RC" || fail "hashcat exited $RC"
  exit 0
fi

exec > "$OUTDIR/hc-node.log" 2>&1
# Require fresh result paths so old rank records cannot masquerade as this run.
if compgen -G "$OUTDIR/rank.*.kv" >/dev/null; then log 'existing rank records; refusing reuse'; exit 1; fi
if [ "$NODES" -gt 1 ]; then
  INPUT="$DICT"
  [ "$ATTACK" != 1 ] || INPUT="$RULES"
  split -n "l/$NODES" --numeric-suffixes --suffix-length=5 "$INPUT" "$OUTDIR/part." || exit 1
  srun -K0 -N "$NODES" -n "$NODES" --ntasks-per-node=1 bash -l "$HERE/hc-node.sh" --rank "${ORIGINAL[@]}"
  FAN_RC=$?
else
  bash -l "$HERE/hc-node.sh" --rank "${ORIGINAL[@]}"
  FAN_RC=$?
fi

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"; value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"; value="${value//$'\r'/\\r}"; value="${value//$'\t'/\\t}"
  printf '%s' "$value"
}
FAILED=0 TOTAL=0 MAX=0 SEP=
printf '{"ranks":[' > "$OUTDIR/summary.json.tmp"
for ((i=0; i<NODES; i++)); do
  rc=-1 cracked=0 elapsed=0 host= error='missing rank record'
  kv="$OUTDIR/rank.$i.kv"
  if [ -f "$kv" ]; then
    error=
    while IFS='=' read -r key value; do
      case "$key" in
        host) host="$value" ;; hashcat_rc) rc="$value" ;; cracked) cracked="$value" ;;
        elapsed_s) elapsed="$value" ;; error) error="$value" ;;
      esac
    done < "$kv"
  fi
  if ! hashcat_rc_ok "$rc" || [ -n "$error" ]; then FAILED=$((FAILED+1)); fi
  TOTAL=$((TOTAL+cracked)); [ "$elapsed" -le "$MAX" ] || MAX="$elapsed"
  printf '%s{"rank":%s,"host":"%s","hashcat_rc":%s,"cracked":%s,"elapsed_s":%s,"error":"%s"}' \
    "$SEP" "$i" "$(json_escape "$host")" "$rc" "$cracked" "$elapsed" "$(json_escape "$error")" >> "$OUTDIR/summary.json.tmp"
  SEP=,
done
printf '],"ranks_total":%s,"ranks_failed":%s,"total_cracked":%s,"max_elapsed_s":%s,"fanout_rc":%s}\n' \
  "$NODES" "$FAILED" "$TOTAL" "$MAX" "$FAN_RC" >> "$OUTDIR/summary.json.tmp"
mv "$OUTDIR/summary.json.tmp" "$OUTDIR/summary.json"
cat "$OUTDIR/summary.json"
[ "$FAN_RC" = 0 ] && [ "$FAILED" = 0 ]
