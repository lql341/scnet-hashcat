# Quickstart

English | [中文](quickstart_CN.md)

## Credentials and target

If scnet-hpc is already configured, reuse its environment variables or OS
credential store. Otherwise inject `SCNET_OPENAPI_USER`,
`SCNET_OPENAPI_ACCESS_KEY`, `SCNET_OPENAPI_SECRET_KEY` in your own terminal.
Never paste secrets into agent chat or commit them. No plaintext credential
configuration is read. `$XDG_CONFIG_HOME/scnet-hpc/config.json` (or
`~/.config/scnet-hpc/config.json`) can hold:

```json
{"backend":"openapi","openapi":{"default_region_id":"11250"}}
```

Region precedence: `--region`, `SCNET_HASHCAT_REGION`,
`SCNET_OPENAPI_REGION_ID`, saved scnet-hashcat/scnet-hpc selection, then selected
profile. This application supports OpenAPI only and never silently switches to SSH.
Use scnet-hpc for credential setup, module deployment or shell diagnosis.

## Preflight and run

```bash
python3 scripts/hc.py doctor --region 11250
python3 scripts/hc.py precheck --hashes tests/data/hashes.txt --mode 0
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --dry-run
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --region 11250 --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
```

`--dry-run` is entirely local. Real submission queries live queue limits/quotas
before upload. Default module: `hashcat/7.1.2-dtk`, modulefiles:
`<resolved-remote-home>/modulefiles`. Override these when your deployment differs.
A static module name does not verify the executable; each compute rank loads it
and checks device visibility. Module installation is a separate scnet-hpc operation.

```bash
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --rules best64.rule --nodes 2 --wait
python3 scripts/hc.py crack --hashes hashes.txt --mask '?d?d' --nodes 1 --wait
python3 scripts/hc.py status <job-id> --region 11250
python3 scripts/hc.py collect <job-id> --region 11250 --out ./results
python3 scripts/hc.py cancel <job-id> --region 11250
```

`--rules` selects rules splitting automatically; the old `--attack 1` is an
application compatibility alias, not hashcat `-a 1`. `--extra-args` supports
`-O`, `-w N`, `--runtime N`, `--quiet`, `--status`, `--status-timer N`, and
`--backend-ignore-opencl`. Workflow-owned output/attack options cannot be overridden.
A runtime-limited or aborted search reports incomplete/failure even if it found hashes.

## Results and lifecycle

Each run has a unique directory, role-separated inputs and `run.json`. Credentials
are never included. Collect uses that manifest, not filename guessing. Outputs:
`summary.json`, `rank.<n>.kv`, `rank.<n>.log`, `devices.<n>.txt`, `pot.<n>`,
`pot.merged`, `cracked.<n>`, `report.json`, and available scheduler logs.
Outputs contain sensitive recovery data; keep them private. Plaintexts are not
printed automatically.

`report.json` records the actual job ID, target, scheduler state and rank completeness.
Recovery counts use unique input lines matched to outfile-format 1; format
normalization can undercount. Raw potfiles remain available for verification.
An exhausted search is successful execution, even with remaining hashes.

An existing nonempty output directory requires `--cover`; this replaces managed
artifacts and rebuilds the merge so stale results do not inflate it.
`FINALIZING` waits for scheduler accounting. `--wait-timeout` defaults to 900 seconds;
if it expires, use the printed status/cancel commands. It does not cancel the job.
