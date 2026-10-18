# Changelog

## 0.1.0 (2026-10-18)

Initial release.

- Self-contained SCNet OpenAPI client (`scripts/scnet_lite.py`, subset of
  scnet-hpc, MIT): credentials, region/center discovery, submit, job status,
  wait, cancel, log tail, efile list/mkdir/upload (chunked)/download/remove,
  account, queues, limits.
- Local driver `scripts/hc`: `doctor`, `precheck`, `crack`, `status`,
  `collect`, `split`, `version`; `--dry-run` planning, `--wait` blocking mode.
- Remote executor `scripts/remote/hc-node.sh`: srun fan-out across nodes,
  dictionary/rules file splitting (`split -n l/N`), per-rank potfiles and
  cracked outputs, per-rank JSON summaries, merged report.
- CVE precheck `scripts/remote/hc-precheck.py` for hashcat v7.1.2
  unreleased CVEs (krb5 field-length, PKZIP blob bounds, line/control-byte
  limits).
- Verified on-cluster: multi-node dictionary attack, 4 DCU per node, module
  load, result merge; mask attack restricted to single node due to the
  cluster's mask-engine token-dropping defect (see
  `references/parallelization.md`).
