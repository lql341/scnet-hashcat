# Quickstart

English | [中文](quickstart_CN.md)

Replace `<region-id>` and `<queue>` in commands with the actual configured target; these are execution choices, not part of the application name.

## First-run prerequisites

Start with [installation](installation.md) if the skill is not installed. Run the
commands here from the installed skill root; Windows uses `python` or `py -3` in
place of `python3`. An agent should resolve this directory to an absolute path.

1. Local Python 3.8+ and the complete skill suffice for help, input checks and
   dry-run. No local GPU, hashcat or SCNet credential is needed for those operations.
2. Real operations need an SCNet account with the target region enabled, queue
   permission, sufficient balance and quota. Select the actual region ID, cluster
   profile and queue for your SCNet cluster environment; validate their compatibility.
3. Prepare the platform username and HPC OpenAPI AK/SK. These are not a model API
   key, account password or SSH key. OpenAPI handles jobs/files; separate deployment
   or remote shell diagnosis may need SSH through scnet-hpc.
4. The remote account must already have a compatible hashcat module, an existing
   readable modulefiles directory, and writable shared run storage visible to all
   nodes. Compute nodes need Bash, Slurm/srun, GNU split and the appropriate DCU/DTK
   runtime. Remote Python 3 and compute-node Internet access are not required.
5. Supply authorized offline hash input in the selected hashcat format, an explicit
   mode and a dictionary or single-node mask. `--mode 0` is MD5, not auto-detection.
   This driver does not extract hashes from source files or support arbitrary
   hashcat options such as `--username`.

## Get credentials and configure them locally

In SCNet **Personal Center → Access Control**, generate/download the HPC
authorization file. Use the platform username and its `Accesskey`/`Secretkey`
values; see [official AK/SK instructions](https://www.scnet.cn/ac/openapi/doc/2.0/api/safecertification/get-user-tokens-aksk.html).
A key alone does not activate region resources. Account/resource onboarding is in
the [SCNet beginner guide](https://www.scnet.cn/help/docs/mainsite/hpc/beginner-guide/).

Prefer reusing an existing scnet-hpc configuration. For first-time setup, install
[scnet-hpc](https://github.com/lql341/scnet-hpc#installation) if needed and run the
following in **your own visible terminal**, replacing the placeholder with its
actual absolute installation directory:

```bash
python3 "<absolute-scnet-hpc-directory>/scripts/scnet.py" setup new --mode openapi
python3 "<absolute-scnet-hpc-directory>/scripts/scnet.py" setup status
```

Use `python` on Windows. To change existing configuration, use
`setup modify --mode openapi`. The shared store service is `scnet-hpc-openapi`:
Windows Credential Manager, macOS Keychain or Linux Secret Service. Linux needs
`secret-tool` and an unlocked session keyring (Ubuntu/Debian: `libsecret-tools`).
Check the actual credential source in setup status: saving region choices alone
does not mean credentials were stored. This hashcat skill has no separate setup UI.

For standalone use, provide all three environment variables listed below using
your host's secret injection or in your own terminal. They are process secrets,
not a persistent credential store. Variables set in another terminal are not
inherited by an already-running agent: run the CLI in that terminal, launch the
agent from it, or use the shared OS store. A partial set fails instead of mixing
with stored credentials. Never paste secret values into chat or JSON files.

Enter values interactively in your own terminal, from the installed skill root.
These examples do not save a credential file. Linux/macOS Bash:

```bash
read -r -p 'SCNet platform username: ' SCNET_OPENAPI_USER
read -r -s -p 'AccessKey: ' SCNET_OPENAPI_ACCESS_KEY
printf '\n'
read -r -s -p 'SecretKey: ' SCNET_OPENAPI_SECRET_KEY
printf '\n'
export SCNET_OPENAPI_USER SCNET_OPENAPI_ACCESS_KEY SCNET_OPENAPI_SECRET_KEY
python3 scripts/hc.py doctor --region "<region-id>"
```

Windows PowerShell:

```powershell
$env:SCNET_OPENAPI_USER = Read-Host 'SCNet platform username'
$env:SCNET_OPENAPI_ACCESS_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'AccessKey' -AsSecureString)).Password
$env:SCNET_OPENAPI_SECRET_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'SecretKey' -AsSecureString)).Password
python scripts/hc.py doctor --region "<region-id>"
```

## Check the remote module, then run a small job

Installing the skill does not deploy hashcat. Default deployment values are
`hashcat/7.1.2-dtk26.04-z100` and `<resolved-remote-home>/modulefiles`; neither is guaranteed
to exist for a new account. If the site supplies another module/directory, pass
`--module <real-module-name> --modulefiles <absolute-remote-directory>` to crack.
The directory must exist; module names alone do not establish patch status.

For diagnosis in an **already allocated compute-node login shell**, load the
site's module directory and module, then run `hashcat --version` and `hashcat -I`.
Login-node GPU checks do not prove compute-node readiness. If no module is deployed,
prepare it through the cluster administrator or a separate scnet-hpc deployment
task. `doctor` checks API resources, not the remote binary or module.

After credentials and the module are ready:

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --mode 0 --region "<region-id>" --queue "<queue>" --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --dry-run
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --mode 0 --region "<region-id>" --queue "<queue>" --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --wait --wait-timeout 900
```

The last command consumes compute resources. Expected recovery is **5 of 7**;
two hashes deliberately have no dictionary match. Check accounting completion and
the single expected rank. Without `--wait`, submission returns immediately; keep
the printed job ID, region and run directory for status/collect. If waiting times
out while queued/running, check status before resubmitting; cancel explicitly if
you want to stop the job.

## Agent prompts for your own data

Replace paths/mode and specify target, resource budget and walltime. On Windows
use native absolute local paths. Hashes/dictionary/rules are **local** files;
`--work-dir` and `--modulefiles` are **remote POSIX** paths.

> Use `$scnet-hashcat` to process my authorized MD5 input `/absolute/local/hashes.txt` with dictionary `/absolute/local/dict.txt` in my selected SCNet cluster environment and queue, one node and one DCU for at most ten minutes; validate inputs/resources, submit once, wait up to 15 minutes and collect, reporting scheduler state and every expected rank without printing recovered plaintext.

> Use `$scnet-hashcat` to check job `<job-id>` in my selected SCNet region and collect its results into a new local directory; report missing/failed ranks and keep partial artifacts.

> Use `$scnet-hashcat` to cancel job `<job-id>` in my selected SCNet region, then query and report its actual state.

Replace job placeholders with real IDs. Cancellation acknowledgment alone does not
prove that the scheduler has finished cleanup.

## Credentials and target

If scnet-hpc is already configured, reuse its environment variables or OS
credential store. Otherwise inject `SCNET_OPENAPI_USER`,
`SCNET_OPENAPI_ACCESS_KEY`, `SCNET_OPENAPI_SECRET_KEY` in your own terminal.
Never paste secrets into agent chat or commit them. No plaintext credential
configuration is read. `$XDG_CONFIG_HOME/scnet-hpc/config.json` (or
`~/.config/scnet-hpc/config.json`) can hold:

```json
{"backend":"openapi","openapi":{"default_region_id":"<region-id>"}}
```

Region precedence: `--region`, `SCNET_HASHCAT_REGION`,
`SCNET_OPENAPI_REGION_ID`, saved scnet-hashcat/scnet-hpc selection, then selected
profile. This application supports OpenAPI only and never silently switches to SSH.
Use scnet-hpc for credential setup, module deployment or shell diagnosis.

## Preflight and run

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py precheck --hashes tests/data/hashes.txt --mode 0
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --dry-run
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --region "<region-id>" --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
```

`--dry-run` is entirely local. Real submission queries live queue limits/quotas
before upload. Default module: `hashcat/7.1.2-dtk26.04-z100`, modulefiles:
`<resolved-remote-home>/modulefiles`. Override these when your deployment differs.
A static module name does not verify the executable; each compute rank loads it
and checks device visibility. Module installation is a separate scnet-hpc operation.

```bash
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --rules best64.rule --nodes 2 --wait
python3 scripts/hc.py crack --hashes hashes.txt --mask '?d?d' --nodes 1 --wait
python3 scripts/hc.py status <job-id> --region "<region-id>"
python3 scripts/hc.py collect <job-id> --region "<region-id>" --out ./results
python3 scripts/hc.py cancel <job-id> --region "<region-id>"
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
