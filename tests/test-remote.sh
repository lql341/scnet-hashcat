#!/usr/bin/env bash
# Behavioral remote tests with fake hashcat/srun; no scheduler or credentials.
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/scnet-hashcat-test-remote.XXXXXX")"
mkdir -p "$TMP/bin"
cleanup() {
  case "$TMP" in "${TMPDIR:-/tmp}"/scnet-hashcat-test-remote.*|/tmp/scnet-hashcat-test-remote.*) rm -rf -- "$TMP" ;; *) exit 1 ;; esac
}
trap cleanup EXIT
export HC_TEST_BIN="$TMP/bin"
cat > "$TMP/bin/hashcat" <<'HC'
#!/usr/bin/env bash
if [ "$1" = -I ]; then echo 'Backend Device ID #1'; exit 0; fi
input= pot= cracked=
while [ $# -gt 0 ]; do
  case "$1" in
    --potfile-path) pot="$2"; shift 2 ;;
    -o) cracked="$2"; shift 2 ;;
    *) shift ;;
  esac
done
printf 'hash:plain\n' > "$pot"
printf 'hash\n' > "$cracked"
exit "${HC_TEST_RC:-1}"
HC
cat > "$TMP/bin/srun" <<'SRUN'
#!/usr/bin/env bash
while [ "$1" != bash ]; do shift; done
pids=()
for rank in 0 1; do
  if [ "${HC_TEST_MISSING:-0}" = 1 ] && [ "$rank" = 1 ]; then continue; fi
  SLURM_PROCID="$rank" "$@" & pids+=("$!")
done
rc=0
for pid in "${pids[@]}"; do wait "$pid" || rc=1; done
exit "$rc"
SRUN
chmod +x "$TMP/bin/"*
module() { export PATH="$HC_TEST_BIN:$PATH"; }
export -f module
export PATH="$HC_TEST_BIN:$PATH"
printf 'hash\n' > "$TMP/hash"
printf 'a\nb\nc\nd\n' > "$TMP/dict"
run() {
  env -u BASH_ENV -u ENV -u MODULESHOME bash "$ROOT/scripts/remote/hc-node.sh" --hashes "$TMP/hash" --dict "$TMP/dict" \
    --module fake --outdir "$TMP/$1" --nodes "$2"
}
run success 2
[ -f "$TMP/success/rank.0.kv" ] && [ -f "$TMP/success/rank.1.kv" ]
# Splitting preserves every candidate and happens once in the coordinator.
cat "$TMP/success/part."* > "$TMP/rejoined"
cmp "$TMP/dict" "$TMP/rejoined"
export HC_TEST_RC=2
if run aborted 1; then echo 'aborted hashcat incorrectly succeeded'; exit 1; fi
export HC_TEST_RC=255
if run negative 1; then echo 'negative hashcat error incorrectly succeeded'; exit 1; fi
unset HC_TEST_RC
export HC_TEST_MISSING=1
if run missing 2; then echo 'missing rank incorrectly succeeded'; exit 1; fi
grep -q 'missing rank record' "$TMP/missing/summary.json"
echo 'remote tests: all passed'
