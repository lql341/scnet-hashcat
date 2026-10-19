# scnet-hashcat

English | [中文](README_CN.md)

Current release: 0.2.1

Run [hashcat](https://hashcat.net/hashcat/) offline password-recovery workloads on
[SCNet](https://www.scnet.cn) cluster environments. This application skill follows
[scnet-hpc](https://github.com/lql341/scnet-hpc) conventions: profiles, OpenAPI,
shared credential discovery, bounded jobs and evidence-based status reporting.

This is the reference application for
[scnet-app](https://github.com/lql341/scnet-app), the meta-skill for SCNet resource
binding, Slurm scheduling and cluster packaging. See its
[benchmark mapping](https://github.com/lql341/scnet-app/blob/main/references/hashcat-reference.md)
before applying these patterns to another scientific application.

## One-sentence agent installation

Paste this into Codex:

> Use `$skill-installer` to install `scnet-hashcat` from the root of GitHub repository `lql341/scnet-hashcat` (path `.`, ref `main`), name it `scnet-hashcat`, do not overwrite an existing destination, then run `scripts/hc.py --help` with the available Python 3 interpreter from the installed directory and report the absolute installation path; do not configure credentials or submit jobs during installation.

The skill is available on the next turn. This installs the **local skill**, not a
remote hashcat binary. No SCNet credentials, local GPU or local hashcat installation
are needed to install or produce an offline plan. Codex installer commands for
Linux/macOS and Windows, manual installation for other agents, verification and
update behavior are in [installation](references/installation.md).

## Prerequisites

| Stage | Required |
| --- | --- |
| Install, help, input checks, offline dry-run | Local Python 3.8+, standard library; GitHub download access for installation. Git is only needed for the clone route. |
| Read live resources with doctor | An SCNet account enabled for the selected region, platform username + HPC OpenAPI AK/SK, and access to SCNet API services. |
| Run a recovery job | Queue permission, sufficient balance/quota, a compatible hashcat module already deployed for the account, an existing modulefiles directory, and shared writable remote storage. Compute nodes need Bash, Slurm/srun, GNU split and the correct DCU/DTK runtime. |
| Supply a workload | Authorized offline hashes in the selected hashcat format, an explicit hash mode (`--mode`, default 0/MD5), and a dictionary or a single-node mask; rules are optional. |

Local Linux/macOS can also use `scripts/hc`; Windows can call `python scripts/hc.py`
without Bash/WSL. Remote Python 3 and compute-node Internet access are not required.
`scnet-hpc` is recommended for first-time credential setup or software deployment,
but is not a runtime dependency when credentials and the module already exist.
AK/SK does not activate region resources by itself. See the
[first-run walkthrough](references/quickstart.md) for where to obtain credentials,
module readiness, exact commands and troubleshooting.

## Ask the agent to use it

First, check readiness without submitting:

> Use `$scnet-hashcat` to check the installed version and resources of my configured SCNet cluster environment, list any missing prerequisites, and prepare an offline plan with the bundled synthetic hashes and dictionary; do not submit a job, and if credentials are missing give me the command to enter them in my own terminal.

Once credentials and the remote module are ready, explicitly authorize a small test:

> Use `$scnet-hashcat` to run the bundled synthetic MD5 dictionary test in my selected SCNet cluster environment and queue, using one node, one DCU and a three-minute walltime; wait up to 15 minutes, collect the results and check that 5 of 7 hashes are recovered, reporting scheduler state and rank completeness.

For your data, specify local input paths, hash mode, region, queue, node/DCU budget
and walltime. More prompts and the complete CLI lifecycle are in
[quickstart](references/quickstart.md).

## Configure and run

Reuse credentials configured by scnet-hpc: environment variables or its supported
OS credential store (`scnet-hpc-openapi`). No secrets belong in `config.json`.
The application works independently when the three OpenAPI environment variables
are injected. See the [quickstart](references/quickstart.md). Run relative commands
from the installed skill directory or clone; the agent should resolve its absolute
path. Replace `<region-id>` with your configured target region.

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --dry-run
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --region "<region-id>" --wait
python3 scripts/hc.py status <job-id> --region "<region-id>"
python3 scripts/hc.py collect <job-id> --region "<region-id>" --out ./results
```

Resource defaults: 1 node, 1 DCU, 8 total CPUs and 10 minutes. Select the actual
cluster profile, region and queue for your SCNet environment.
Explicit options override defaults. Queue/quotas are queried before upload and
submission. Static profile capacity is not current free capacity. An installed
hashcat module is an account prerequisite, not installed by this skill.
Read [runtime prerequisites](references/prerequisites.md) for the validated
six-axis stack and failure diagnosis before a real submission.

Dictionary/rules workloads support multiple nodes. Files are split once before
fan-out; rank logs and potfiles stay separate. Masks require one node. Only
accounting-confirmed completion plus all expected successful ranks returns success.
`--wait-timeout` bounds local waiting; timing out leaves the remote job running.
Use `cancel` to stop it explicitly.

Input checks are conservative and may reject legitimate long fields. They do not
establish CVE immunity. PKZIP structural validation is unsupported and rejected;
see [input-check limits](references/cve-precheck.md). Small `--keyspace` values
are normal base-loop semantics, not evidence of dropped mask tokens.

## Structure and validation

```text
VERSION / CHANGELOG.md   Application version and history
SKILL.md / agents/      Agent instructions and UI metadata
clusters/               Account-neutral application profiles
scripts/hc.py           Portable local application driver
scripts/scnet_lite.py   Focused SCNet OpenAPI adapter
scripts/remote/         Compute-node execution and input checks
references/             English instructions and *_CN.md translations
tests/                  Offline behavioral regressions and synthetic fixtures
```

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/test-precheck.py
bash tests/test-driver.sh
bash tests/test-remote.sh
```

SCNet cluster environment validation and its limits are recorded in
[the test report](references/validation.md). Architecture and pinned vendored
sources are described in [architecture](references/architecture.md).

MIT. The OpenAPI adapter and shared credential/version helpers derive from
[lql341/scnet-hpc](https://github.com/lql341/scnet-hpc), also MIT.
