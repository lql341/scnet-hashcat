# scnet-hashcat

English | [中文](README_CN.md)

Current release: 0.2.0

Run [hashcat](https://hashcat.net/hashcat/) offline password-recovery workloads on
[SCNet](https://www.scnet.cn) compute nodes. This application skill follows
[scnet-hpc](https://github.com/lql341/scnet-hpc) conventions: profiles, OpenAPI,
shared credential discovery, bounded jobs and evidence-based status reporting.

## Install

Paste into your agent:

> Install the `scnet-hashcat` skill from the root of GitHub repository `lql341/scnet-hashcat` (path `.`), name it `scnet-hashcat`, do not overwrite an existing destination, then run `python3 scripts/hc.py --help` from the installed directory and report the installation path.

Or run from a clone:

```bash
git clone https://github.com/lql341/scnet-hashcat.git
cd scnet-hashcat
python3 scripts/hc.py --help
```

Local runtime: Python 3.8+, standard library only. Linux/macOS can use `scripts/hc`;
Windows can call `python scripts/hc.py` without Bash/WSL. Remote execution requires
Linux Bash, Slurm, GNU split and a hashcat module for the allocated DCUs.

## Configure and run

Reuse credentials configured by scnet-hpc: environment variables or its supported
OS credential store (`scnet-hpc-openapi`). No secrets belong in `config.json`.
The application works independently when the three OpenAPI environment variables
are injected. See the [quickstart](references/quickstart.md).

```bash
python3 scripts/hc.py doctor --region 11250
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --dry-run
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --region 11250 --wait
python3 scripts/hc.py status <job-id> --region 11250
python3 scripts/hc.py collect <job-id> --region 11250 --out ./results
```

Defaults: Kunshan profile `kseshell`, 1 node, 1 DCU, 8 total CPUs and 10 minutes.
Explicit options override defaults. Queue/quotas are queried before upload and
submission. Static profile capacity is not current free capacity. An installed
hashcat module is an account prerequisite, not installed by this skill.

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

Kunshan validation and its limits are recorded in
[the test report](references/validation.md). Architecture and pinned vendored
sources are described in [architecture](references/architecture.md).

MIT. The OpenAPI adapter and shared credential/version helpers derive from
[lql341/scnet-hpc](https://github.com/lql341/scnet-hpc), also MIT.
