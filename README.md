# scnet-hashcat

Run distributed [hashcat](https://hashcat.net) password-recovery jobs on
[SCNet](https://www.scnet.cn) HPC clusters (Hygon DCU / DTK), single or
multi-node, with an automatic CVE precheck and result collection.

A general-purpose agent skill: the driver is plain bash + Python 3 standard
library, the cluster layer is a self-contained OpenAPI client, and there is
no dependency on any specific agent platform.

## Features

- **One command, full pipeline**: precheck hash file → upload inputs →
  submit a multi-node Slurm job (one hashcat per node, all DCUs) → wait →
  merge potfiles → report.
- **Cross-node parallelism by file splitting**, immune to this cluster's
  mask-engine defect (see `references/parallelization.md`).
- **CVE guard**: rejects crafted krb5/PKZIP hash-file shapes before hashcat
  ever reads them (CVE-2026-42483, CVSS 9.8; CVE-2026-42484;
  CVE-2026-68768).
- **Self-contained**: `scripts/scnet_lite.py` is a trimmed SCNet OpenAPI
  client (subset of [scnet-hpc](https://github.com/lql341/scnet-hpc), MIT);
  credentials are shared with scnet-hpc when present.

## Install

Copy the repo anywhere and add it to your agent's skill directory, or just
run it directly:

```bash
git clone https://github.com/lql341/scnet-hashcat
cd scnet-hashcat
```

Works with Claude Code, Codex, WorkBuddy, or any agent that can execute
shell commands.

## Usage

```bash
scripts/hc doctor
scripts/hc crack --hashes hashes.txt --dict rockyou.txt --nodes 4 --wait
scripts/hc status <job-id>
scripts/hc collect <job-id> --out ./results
```

See [references/quickstart-en.md](references/quickstart-en.md) for the full
walkthrough and
[references/quickstart.md](references/quickstart.md) for the Chinese version.

## Requirements

- Python 3.8+ (driver machine), standard library only.
- SCNet OpenAPI credentials (env vars or `~/.config/scnet-hashcat/config.json`).
- On-cluster: a hashcat DCU build exposed as a module (default
  `hashcat/7.1.2-dtk` in a personal modulefiles directory).

## Layout

```
scripts/
  hc                     local driver (doctor/precheck/crack/status/collect/split)
  scnet_lite.py          self-contained SCNet OpenAPI client
  remote/
    hc-node.sh           per-node executor (srun fan-out, file splitting)
    hc-precheck.py       hash-file CVE guard
    hc-common.sh         shared remote helpers
references/              quickstart (en/zh), parallelization, cve-precheck, pitfalls
agents/openai.yaml       OpenAI/Codex interface metadata
```

## License

MIT. The OpenAPI client subset is derived from
[lql341/scnet-hpc](https://github.com/lql341/scnet-hpc) (MIT).
