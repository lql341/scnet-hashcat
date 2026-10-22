# First use

`scnet-hashcat` is usable offline for input checks and planning. A real SCNet
job additionally needs account/resource activation, credentials and a prepared
hashcat module.

## 1. Account and resources

- A SCNet account alone is not enough; the target region and queue must be
  enabled. AK/SK does not activate compute resources.
- New users should read the SCNet beginner guide linked from
  `scnet-hpc/references/first-use.md`.
- Obtain HPC OpenAPI AK/SK from **个人中心 → 访问控制**. This is not a
  model-service API key.
- SSH is separate and needed only for deployment or diagnosis. The normal
  OpenAPI workflow does not use SSH.

## 2. Credentials

Use one of:

```text
SCNET_OPENAPI_USER
SCNET_OPENAPI_ACCESS_KEY
SCNET_OPENAPI_SECRET_KEY
```

or the shared `scnet-hpc-openapi` OS credential store. If `scnet-hpc` is
installed, run in your own terminal:

```bash
python3 "<scnet-hpc>/scripts/scnet.py" setup new --mode openapi
python3 "<scnet-hpc>/scripts/scnet.py" setup status
```

Never send AK/SK, private keys or credential files to the agent/chat, and never
write them into `config.json` or a cluster profile.

## 3. Local check

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --dry-run
```

`doctor` is the first authenticated check. `--dry-run` plans locally without
uploading or submitting. If `doctor` reports missing credentials, region or
queue, follow its message and this document; do not retry submission blindly.

## 4. Module and first job

- A compatible hashcat module must already be deployed for the account. The
  module name does not prove deployment or device compatibility.
- Select the actual cluster profile, region, queue, module and input paths.
- Start with the bundled synthetic hashes/dictionary and one node, one DCU and a
  short walltime. Only then use authorized user data.
- The skill embeds a pinned OpenAPI adapter; users load only `scnet-hashcat`.
  `scnet-hpc` remains optional for first-use setup, SSH and deployment.
