---
name: scnet-hashcat
description: Run authorized offline hashcat password-recovery jobs on SCNet HPC DCU resources, with input checks, bounded scheduling, distributed execution, and result collection.
---

# SCNet hashcat

Use this application skill for hashcat workloads on SCNet. Prefer OpenAPI for
resource discovery, file transfer, submission and status. Use scnet-hpc for
first-use setup, SSH, software deployment and broader cluster diagnosis when
available; this skill also runs independently with environment credentials.

## First use and selection

- Installation requests: read [references/installation.md](references/installation.md)
  or [references/installation_CN.md](references/installation_CN.md); distinguish local
  skill installation, credential setup, and remote module deployment.
- Default repository instructions are English; respond in the user's language.
  Start with [references/quickstart.md](references/quickstart.md), or
  [references/quickstart_CN.md](references/quickstart_CN.md) for Chinese.
- Read `clusters/<cluster>.conf` before using static defaults. Select one region
  and queue; query live queues/quotas before a real submission. Profile defaults
  do not prove availability, module deployment or device visibility.
- Reuse scnet-hpc environment credentials or its OS credential store. Configuration
  under `$XDG_CONFIG_HOME` or `~/.config` holds non-secret choices only. Never ask
  for secrets in chat. See [references/architecture.md](references/architecture.md).
- Local Python 3.8+ and standard library suffice. Linux/macOS can also use the
  Bash wrapper; Windows can call `python scripts/hc.py` directly.
- `hashcat/7.1.2-dtk` is a deployment example. Set `--module`/`--modulefiles` for the
  selected account. The module directory defaults to the resolved remote home,
  never a maintainer's personal path. Heavy work must run on compute nodes.

## Workflow

```bash
python3 scripts/hc.py doctor --region 11250
python3 scripts/hc.py precheck --hashes hashes.txt --mode 0
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --dry-run
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --region 11250 --wait
python3 scripts/hc.py status <job-id> --region 11250
python3 scripts/hc.py collect <job-id> --region 11250 --out ./results
python3 scripts/hc.py cancel <job-id> --region 11250
```

Match nodes, DCUs, walltime, queue and input scope to the user's authorization.
A pure local dry-run does not authenticate, upload or submit. Resolve live limits
before uploading. Never silently retry submission. If waiting times out, report
that the job may still be active and provide status/cancel commands.

Every submission gets a unique remote directory and `run.json` recording input
roles and target. Keep the job ID, region, remote directory and collection command
in the private run record. Do not publish hashes, recovered plaintexts, job IDs,
personal paths or node names in public reports.

## Distributed execution and evidence

- One coordinator splits the dictionary or rules file **once**, before `srun`.
  One rank runs per node; each writes separate potfile, output and logs.
- With `--rules`, split rules; the dictionary stays shared. The old `--attack 1`
  is a compatibility alias for this skill's rules mode, **not** hashcat's
  combinator attack. Actual hashcat invocation is `-a 0 -r`.
- Mask mode currently requires exactly one node; do not allocate idle nodes.
  This is an implementation limit. `--keyspace` is a base-loop work counter,
  not total candidates; a smaller value alone is not a mask defect.
- Treat only hashcat exit 0/1 as normal. Keep sibling ranks running after a
  rank fails, but propagate failure/missing ranks to the scheduler and collector.
- Require accounting-confirmed completion **and** all expected successful rank
  records. `FINALIZING`, missing summaries, timeout and partial results are not
  success. A completed search can still have unrecovered hashes.
- Input precheck is a conservative heuristic, not proof of parser safety.
  PKZIP is rejected because structural validation is unsupported. Use patched
  software and trusted inputs. A deliberate `--skip-precheck` bypasses all checks.

Read only the relevant reference:

- Splitting and mask semantics: [references/parallelization.md](references/parallelization.md)
- Input-check limits and sources: [references/cve-precheck.md](references/cve-precheck.md)
- Runtime diagnosis: [references/pitfalls.md](references/pitfalls.md)
- SCNet relationship and vendor provenance: [references/architecture.md](references/architecture.md)

## Stable entrypoints

- `python3 scripts/hc.py`: doctor, precheck, crack, status, collect, cancel, split, version.
- `scripts/hc`: Bash compatibility wrapper; `SCNET_HASHCAT_PYTHON` selects Python.
- `scripts/scnet_lite.py`: OpenAPI adapter, derived from scnet-hpc; no SSH fallback.
- `scripts/remote/hc-node.sh`: coordinator and rank executor; no remote Python dependency.
