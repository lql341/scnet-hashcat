---
name: scnet-hashcat
description: Run distributed hashcat password-recovery jobs on SCNet HPC clusters (Hygon DCU), single or multi-node, with CVE precheck and automatic result collection.
---

# SCNet hashcat

Distributed hashcat on SCNet. One command runs the whole pipeline: precheck the
hash file, upload inputs, submit a multi-node Slurm job with one hashcat per
node, wait, and collect merged results. The cluster access layer is a
self-contained OpenAPI client vendored from scnet-hpc; this skill does not
require scnet-hpc to be installed.

## Requirements

- `python3` 3.8+ on the machine driving the job (standard library only).
- OpenAPI credentials: `SCNET_OPENAPI_USER` / `SCNET_OPENAPI_ACCESS_KEY` /
  `SCNET_OPENAPI_SECRET_KEY`, or `~/.config/scnet-hashcat/config.json`
  (same JSON shape as scnet-hpc; the scnet-hpc config file is read as a
  fallback, so both skills can share one credential set).
- On the cluster: a hashcat module under a personal modulefiles directory
  (default `hashcat/7.1.2-dtk` in `/public/home/luql/modulefiles`; override
  with `--module` / `--modulefiles` or `SCNET_HASHCAT_MODULEFILES`).

## Route only as needed

- First run / quick start: `references/quickstart.md` (or `quickstart-en.md`)
- Cross-node splitting strategy and the mask-engine defect:
  `references/parallelization.md`
- hashcat CVE guard details: `references/cve-precheck.md`
- Everything that went wrong during development, with the fixes:
  `references/pitfalls.md`

Read only the reference the current operation needs.

## Core workflow

```bash
scripts/hc doctor                                             # credentials + region + account
scripts/hc precheck --hashes hashes.txt --mode 0              # CVE guard, read-only
scripts/hc crack --hashes hashes.txt --dict rockyou.txt \
  --nodes 4 --dcus-per-node 4 --wait                          # full pipeline
scripts/hc status <job-id>                                    # progress + result files
scripts/hc collect <job-id> --out ./results                   # potfiles, cracked, logs
```

`crack` resolves the remote run directory as `<work-dir>/<name>` (default
`<home>/hashcat-runs`), uploads inputs under `inputs/`, writes results under
`results/`, and prints the job id plus the exact `status`/`collect` commands.
Pass `--dry-run` to see the plan without touching the cluster.

## Parallelization rules (verified on-cluster)

- **Never use `--skip/--limit` keyspace splitting across nodes.** The mask
  engine on this cluster drops mask tokens (`?l?l?l` yields keyspace 676, not
  17576), so keyspace arithmetic is unreliable. Split the input *files*
  instead: each rank runs `split -n l/N` on the shared dictionary or rules
  file. This is attack-mode independent and verified working.
- `--cpus` in the submit API is the **job total** (split across nodes);
  `--dcus` is **per node** (max 4). The driver handles both.
- The job `--command` only executes on the **first** node; multi-node fan-out
  must go through `srun` inside the uploaded script (the driver does this,
  with `-K0` so one bad rank cannot kill its siblings).
- One hashcat process per node uses all DCUs allocated to that node
  (4x DCU Z100 per compute node on this cluster; `--dcus-per-node 4`).
- Mask attack (`-a 3`) runs single-node only; multi-node mask splitting is
  skipped per rank with a log line until the mask defect is root-caused.
- Each rank writes its own `pot.<rank>` and `cracked.<rank>`; the driver
  merges potfiles into `pot.merged` and reports cracked/remaining.
- A rank that fails (e.g. a node whose DCUs are not visible) records the
  failure in `rank.<id>.kv` and exits 0, so sibling ranks still finish.
  Check `ranks_failed` in the collected `summary.json`.

## Boundaries and evidence

- **Precheck every hash file before submission.** hashcat v7.1.2 has five
  unreleased CVEs (disclosed 2026-05-01); the worst, CVE-2026-42483 (CVSS 9.8),
  is a krb5 parser heap overflow reachable from a crafted hash file. Only
  bypass with `--skip-precheck` when the input source is fully trusted.
- Jobs consume account balance and scheduler quota. Confirm nodes, DCUs,
  walltime, and queue before a real submit; use `--dry-run` first.
- hashcat writes `hashcat.log` and `hashcat.dictstat2` into the **install
  directory** of the binary, not the working directory. The module layout
  keeps those files inside the module prefix; do not point `--module` at a
  source/build tree you want untouched.
- Report job id, remote run directory, and local output directory for every
  run so the user can re-run `status`/`collect` independently.
- Propagate the job's terminal state; do not claim success from a submit
  response alone.

## Stable entrypoints

- `scripts/hc` - local driver: `doctor`, `precheck`, `crack`, `status`,
  `collect`, `split`, `version`.
- `scripts/scnet_lite.py` - self-contained SCNet OpenAPI client
  (`doctor`, `account`, `queues`, `limits`, `submit`, `job`, `wait`,
  `cancel`, `logs`, `mkdir`, `ls`, `upload`, `download`, `rm`).
- `scripts/remote/hc-node.sh` - per-node executor uploaded with the job
  (srun fan-out, file splitting, per-rank potfiles).
- `scripts/remote/hc-precheck.py` - hash file CVE guard.
- `scripts/remote/hc-common.sh` - shared remote helpers.
