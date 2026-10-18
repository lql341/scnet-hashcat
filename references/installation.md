# Installation

English | [中文](installation_CN.md)

## What gets installed

The entire repository root is the `scnet-hashcat` skill. Keep `SKILL.md`, `agents/`,
`clusters/`, `scripts/`, `references/`, `tests/`, `VERSION` and the license together.
Installing only `SKILL.md` is insufficient: the driver imports local helpers and
uploads the bundled remote executor. Skill installation does not configure SCNet,
open region access, deploy hashcat, or allocate compute resources.

Local requirements: Python 3.8+ with a working HTTPS certificate store and GitHub
download access. The Python runtime uses only its standard library; no pip package,
local hashcat, GPU driver or SCNet secret is needed for installation/help/dry-run.
Git is optional unless using a clone or the installer's Git fallback.

## Codex: one sentence

> Use `$skill-installer` to install `scnet-hashcat` from the root of GitHub repository `lql341/scnet-hashcat` (path `.`, ref `main`), name it `scnet-hashcat`, do not overwrite an existing destination, then run `scripts/hc.py --help` with the available Python 3 interpreter from the installed directory and report the absolute installation path; do not configure credentials or submit jobs during installation.

The destination is `$CODEX_HOME/skills/scnet-hashcat`, defaulting to
`~/.codex/skills/scnet-hashcat`. Invoke `$scnet-hashcat` on the next turn.
If it is not discovered, check that the host's actual skill directory contains
`scnet-hashcat/SKILL.md` and refresh its skill inventory.

## Equivalent Codex installer commands

These use the bundled system skill-installer, not a script downloaded from this
repository. Run in a terminal where the shown Python command is available.

Linux / macOS:

```bash
python3 --version
codex_root="${CODEX_HOME:-$HOME/.codex}"
python3 "$codex_root/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo lql341/scnet-hashcat --path . --name scnet-hashcat --ref main --method download
cd "$codex_root/skills/scnet-hashcat"
python3 scripts/hc.py version
python3 scripts/hc.py --help
```

Windows PowerShell:

```powershell
python --version
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
python "$codexRoot/skills/.system/skill-installer/scripts/install-skill-from-github.py" `
  --repo lql341/scnet-hashcat --path . --name scnet-hashcat --ref main --method download
Set-Location "$codexRoot/skills/scnet-hashcat"
python scripts/hc.py version
python scripts/hc.py --help
```

If your Windows installation provides `py -3` instead of `python`, use `py -3`
consistently for the installer and driver. If the bundled installer is absent,
use the clone/manual route below. If GitHub download is unavailable, resolve
network/certificate access or use the installer's supported Git method; do not
claim installation succeeded merely because the prompt was accepted.

`--path .` selects this root-level skill; `--name scnet-hashcat` supplies its
folder name explicitly. To pin a release/commit, replace `--ref main` with an
existing tag or commit. To test without installing into your agent's skills,
pass `--dest <absolute-test-directory>`; that location is not automatically discovered.
The installer refuses an existing destination. For updates, first preserve local
changes and move the existing skill to an explicitly chosen backup location, then
install the chosen ref into the now-unused destination. No automatic overwrite
or credential reset is part of this tutorial.

## Clone and other agents

```bash
git clone https://github.com/lql341/scnet-hashcat.git
cd scnet-hashcat
python3 scripts/hc.py --help
```

On Windows use `python` or `py -3` for the last command. Cloning allows CLI usage,
but does not itself register a skill with any agent. For another host that supports
`SKILL.md` skills and shell/Python execution, copy the whole skill root into that
host's documented skill directory, under `scnet-hashcat`, then refresh discovery.
A host-specific installer/discovery mechanism is required; `$skill-installer` is
the Codex route and is not assumed to exist in every agent.

A platform-neutral instruction for a capable host is:

> Install the complete root-level skill from https://github.com/lql341/scnet-hashcat into your documented skill directory as scnet-hashcat, preserve an existing installation, verify SKILL.md and all companion files, run scripts/hc.py --help with Python 3, and report the resolved path; do not configure credentials or submit jobs.

## Verify offline before connecting

From the installed skill directory (Windows: substitute `python`):

```bash
python3 scripts/hc.py version
python3 scripts/hc.py precheck --hashes tests/data/hashes.txt --mode 0
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --mode 0 --region 11250 --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --dry-run
```

The version must match `VERSION`; precheck must accept the bundled text hashes;
the last command prints a local plan without authentication, upload or submission.
This proves local packaging works, not that remote hashcat is deployed.
Continue with [first use and prerequisites](quickstart.md).
