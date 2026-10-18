# Quickstart (English)

## 1. Credentials (once)

```bash
export SCNET_OPENAPI_USER="luql"
export SCNET_OPENAPI_ACCESS_KEY="<AK>"
export SCNET_OPENAPI_SECRET_KEY="<SK>"
```

or `~/.config/scnet-hashcat/config.json`:

```json
{"user": "luql", "access_key": "<AK>", "secret_key": "<SK>"}
```

The scnet-hpc config file is read as a fallback, so one credential set serves
both skills. On Windows/Git Bash, export `MSYS2_ARG_CONV_EXCL="*"` before
commands that carry remote absolute paths.

## 2. Preflight

```bash
scripts/hc doctor
```

## 3. Run

```bash
scripts/hc crack --hashes hashes.txt --dict dict.txt --nodes 2 --wait
```

Results land in `./hc-out-<job-id>/`: `pot.merged`, `cracked.<rank>`,
`rank.<n>.json`, `report.json`, `std.out`. Without `--wait`, keep the job id
and use `scripts/hc status <job-id>` / `scripts/hc collect <job-id>`.

## 4. Variants

```bash
scripts/hc crack --hashes h.txt --dict rockyou.txt --rules best64.rule --attack 1 --nodes 4 --wait
scripts/hc crack --hashes h.txt --mask '?u?l?l?l?l?d?d?d?d' --attack 3 --nodes 1
scripts/hc crack --hashes h.txt --dict d.txt --nodes 4 --dry-run
scripts/hc crack --hashes h.txt --dict d.txt --mode 1000 --wait
```
