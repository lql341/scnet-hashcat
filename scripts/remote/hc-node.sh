#!/usr/bin/env bash
# hc-node.sh - per-node hashcat executor for scnet-hashcat.
#
# Runs as the Slurm job command. Fans out one hashcat process per allocated
# node via srun; every rank gets its own potfile and cracked-output file.
#
# Cross-node parallelism uses FILE splitting (split -n l/N), never
# --skip/--limit keyspace splitting: the mask engine on this cluster drops
# mask tokens (see references/parallelization.md), and dictionary attacks are
# unaffected by that defect.
#
# Fault tolerance: a rank that fails (no DCU, hashcat error) records the
# failure in rank.<id>.kv and exits 0, so sibling ranks still finish. The
# driver reports rank failures from summary.json.
#
# NOTE 1: `module` is a shell function. Never put it in a pipeline.
# NOTE 2: compute nodes have no python3 - summaries are plain key=value
#         files, and summary.json is assembled with shell only.

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$HERE/hc-common.sh"

usage() {
  cat <<'EOF'
Usage: hc-node.sh --hashes FILE --attack 0|1|3 [--dict FILE] [--rules FILE]
                  [--mask MASK] [--nodes N] [--module NAME] [--modulefiles DIR]
                  [--outdir DIR] [--extra-args "..."]
EOF
}

HASHES=""
DICT=""
RULES=""
MASK=""
ATTACK=""
MODE="0"
NODES="${SLURM_JOB_NUM_NODES:-1}"
MODULE="hashcat/7.1.2-dtk"
MODULEFILES="${SCNET_HASHCAT_MODULEFILES:-/public/home/luql/modulefiles}"
OUTDIR="results"
EXTRA_ARGS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --hashes) HASHES="$2"; shift 2 ;;
    --dict) DICT="$2"; shift 2 ;;
    --rules) RULES="$2"; shift 2 ;;
    --mask) MASK="$2"; shift 2 ;;
    --attack) ATTACK="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --nodes) NODES="$2"; shift 2 ;;
    --module) MODULE="$2"; shift 2 ;;
    --modulefiles) MODULEFILES="$2"; shift 2 ;;
    --outdir) OUTDIR="$2"; shift 2 ;;
    --extra-args) EXTRA_ARGS="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$HASHES" ] || { echo "missing --hashes" >&2; exit 2; }
if [ -z "$ATTACK" ]; then
  if [ -n "$MASK" ]; then ATTACK=3; else ATTACK=0; fi
fi
if [ "$ATTACK" = "0" ] && [ -z "$DICT" ]; then
  echo "dictionary attack requires --dict" >&2; exit 2
fi
if [ "$ATTACK" = "3" ] && [ -z "$MASK" ]; then
  echo "mask attack requires --mask" >&2; exit 2
fi

LOG="$OUTDIR/hc-node.log"
mkdir -p "$OUTDIR"
exec > "$LOG" 2>&1

log "hc-node start: attack=$ATTACK mode=$MODE nodes=$NODES module=$MODULE outdir=$OUTDIR"
log "slurm: job=${SLURM_JOB_ID:-none} nodes=${SLURM_JOB_NUM_NODES:-1} procid=${SLURM_PROCID:-0} host=$(hostname)"

# ---------------------------------------------------------------------------
# rank script: everything a single node does
# ---------------------------------------------------------------------------
RANK_SCRIPT="$OUTDIR/rank.sh"
cat > "$RANK_SCRIPT" <<EOF
#!/usr/bin/env bash
set -u
RANK="\${SLURM_PROCID:-\$\$}"
PARTS=$NODES
OUTDIR_R="$OUTDIR"
HASHES_R="$HASHES"
DICT_R="$DICT"
RULES_R="$RULES"
MASK_R="$MASK"
ATTACK_R=$ATTACK
MODE_R=$MODE
EXTRA_R="$EXTRA_ARGS"

KV="\$OUTDIR_R/rank.\$RANK.kv"
T0=\$(date +%s)

write_kv() {
  # write_kv hashcat_rc cracked elapsed error
  cat > "\$KV" <<KVEOF
rank=\$RANK
host=\$(hostname)
attack=\$ATTACK_R
hashcat_rc=\$1
cracked=\$2
elapsed_s=\$3
error=\$4
KVEOF
}

fail() {
  echo "FATAL: \$1" >&2
  write_kv -1 0 0 "\$1"
  exit 0
}

echo "== rank \$RANK on \$(hostname) =="

module use "$MODULEFILES"
module load "$MODULE"

HC="\$(command -v hashcat)"
[ -n "\$HC" ] || fail "hashcat not found after module load"
echo "hashcat=\$HC"
DEVICES=\$(\$HC -I 2>/dev/null | grep -c 'Backend Device ID')
echo "dcu_devices=\$DEVICES"
[ "\$DEVICES" -ge 1 ] || fail "no DCU device visible (HIP_VISIBLE_DEVICES=\$HIP_VISIBLE_DEVICES)"

POTFILE="\$OUTDIR_R/pot.\$RANK"
CRACKED="\$OUTDIR_R/cracked.\$RANK"
RC=0

case "\$ATTACK_R" in
  0)
    if [ "\$PARTS" -gt 1 ]; then
      split -n l/\$PARTS --numeric-suffixes --suffix-length=3 \\
        "\$DICT_R" "\$OUTDIR_R/dict.part."
      MYDICT="\$OUTDIR_R/dict.part.\$(printf '%03d' \$RANK)"
      echo "dict slice=\$MYDICT lines=\$(wc -l < "\$MYDICT")"
    else
      MYDICT="\$DICT_R"
    fi
    \$HC -a 0 -m "\$MODE_R" "\$HASHES_R" "\$MYDICT" \\
      --potfile-path "\$POTFILE" -o "\$CRACKED" --outfile-format 1 \\
      \$EXTRA_R
    RC=\$?
    ;;
  1)
    if [ "\$PARTS" -gt 1 ]; then
      split -n l/\$PARTS --numeric-suffixes --suffix-length=3 \\
        "\$RULES_R" "\$OUTDIR_R/rules.part."
      MYRULES="\$OUTDIR_R/rules.part.\$(printf '%03d' \$RANK)"
    else
      MYRULES="\$RULES_R"
    fi
    \$HC -a 0 -m "\$MODE_R" "\$HASHES_R" "\$DICT_R" -r "\$MYRULES" \\
      --potfile-path "\$POTFILE" -o "\$CRACKED" --outfile-format 1 \\
      \$EXTRA_R
    RC=\$?
    ;;
  3)
    if [ "\$RANK" != "0" ]; then
      echo "mask attack on multi-node: rank \$RANK skips (mask keyspace splitting is unreliable on this cluster)"
      write_kv 0 0 0 ""
      exit 0
    fi
    \$HC -a 3 -m "\$MODE_R" "\$HASHES_R" "\$MASK_R" \\
      --potfile-path "\$POTFILE" -o "\$CRACKED" --outfile-format 1 \\
      \$EXTRA_R
    RC=\$?
    ;;
esac

CRACKED_N=0
[ -f "\$POTFILE" ] && CRACKED_N=\$(grep -c . "\$POTFILE" || true)
ERR=""
# hashcat exit codes: 0 all cracked, 1 exhausted (normal), 2 aborted, >=3 error
[ \$RC -ge 3 ] && ERR="hashcat exited \$RC"
[ \$RC -eq 2 ] && ERR="hashcat aborted (rc=2)"
write_kv "\$RC" "\$CRACKED_N" "\$((\$(date +%s) - T0))" "\$ERR"
echo "rank \$RANK done rc=\$RC cracked=\$CRACKED_N elapsed=\$((\$(date +%s) - T0))s err=\$ERR"
exit 0
EOF
chmod +x "$RANK_SCRIPT"

if [ "$NODES" -gt 1 ]; then
  log "fanning out $NODES ranks via srun"
  # -K0: do not terminate sibling ranks when one rank exits non-zero
  srun -K0 -N "$NODES" -n "$NODES" --ntasks-per-node=1 bash "$RANK_SCRIPT"
  FAN_RC=$?
else
  bash "$RANK_SCRIPT"
  FAN_RC=$?
fi

log "fan-out rc=$FAN_RC"

# ---------------------------------------------------------------------------
# assemble summary.json with shell only (no python3 on compute nodes)
# ---------------------------------------------------------------------------
TOTAL_CRACKED=0
MAX_ELAPSED=0
RANKS_FAILED=0
RANKS_JSON=""
for kv in "$OUTDIR"/rank.*.kv; do
  [ -f "$kv" ] || continue
  rank=""; host=""; attack=""; hc_rc=""; cracked=""; elapsed=""; error=""
  while IFS='=' read -r key value; do
    case "$key" in
      rank) rank="$value" ;;
      host) host="$value" ;;
      attack) attack="$value" ;;
      hashcat_rc) hc_rc="$value" ;;
      cracked) cracked="$value" ;;
      elapsed_s) elapsed="$value" ;;
      error) error="$value" ;;
    esac
  done < "$kv"
  [ -n "$cracked" ] || cracked=0
  [ -n "$elapsed" ] || elapsed=0
  TOTAL_CRACKED=$((TOTAL_CRACKED + cracked))
  [ "$elapsed" -gt "$MAX_ELAPSED" ] && MAX_ELAPSED="$elapsed"
  [ -n "$error" ] && RANKS_FAILED=$((RANKS_FAILED + 1))
  # minimal JSON string escaping for the error field
  error="${error//\\/\\\\}"
  error="${error//\"/\\\"}"
  entry="{\"rank\": ${rank:-0}, \"host\": \"$host\", \"attack\": ${attack:-0}, \"hashcat_rc\": ${hc_rc:--1}, \"cracked\": $cracked, \"elapsed_s\": $elapsed, \"error\": \"$error\"}"
  if [ -n "$RANKS_JSON" ]; then RANKS_JSON="$RANKS_JSON, $entry"; else RANKS_JSON="$entry"; fi
done

cat > "$OUTDIR/summary.json" <<JSON
{
  "ranks": [$RANKS_JSON],
  "total_cracked": $TOTAL_CRACKED,
  "max_elapsed_s": $MAX_ELAPSED,
  "ranks_total": $(ls "$OUTDIR"/rank.*.kv 2>/dev/null | wc -l),
  "ranks_failed": $RANKS_FAILED
}
JSON

log "summary: total_cracked=$TOTAL_CRACKED max_elapsed_s=$MAX_ELAPSED ranks_failed=$RANKS_FAILED"
cat "$OUTDIR/summary.json"

# Fan-out itself failed (srun could not start)? Surface it, but rank-level
# failures are already recorded above and are not fatal here.
if [ "$FAN_RC" -ne 0 ] && [ "$RANKS_FAILED" -eq 0 ]; then
  log "WARNING: srun returned $FAN_RC but no rank recorded a failure"
fi

exit 0
