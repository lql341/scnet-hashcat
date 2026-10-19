# Runtime prerequisites

English | [中文](prerequisites_CN.md)

The R1 reference deployment is an account-provided module on Hygon Z100
compute nodes. This skill does not install or bundle the cluster runtime.

## Required environment

- Module: `hashcat/7.1.2-dtk26.04-z100`
- Modulefiles: the account's existing remote modulefiles directory, normally
  `<resolved-remote-home>/modulefiles`
- Queue: `kshdnormal`, with at least one DCU per job
- Compute-node tools: Bash login shell, Slurm `srun`, GNU `split`, and the DTK
  runtime exposed by the selected module

The module is loaded after `module use` (when `--modulefiles` is supplied).
Each rank runs `hashcat -I` and requires at least the requested number of
visible `Backend Device ID` entries before starting a recovery.

## Validated stack

The complete R1 signature is kept in
[`stacks/r1-dtk2604-z100.json`](../stacks/r1-dtk2604-z100.json) and is copied
into each run manifest:

```json
{
  "system": {"name": "centos7.6", "glibc": "2.17"},
  "toolchain": {"gcc": "16.2.0", "cmake": "4.4.3"},
  "backend": {"kind": "dcu", "runtime": "dtk", "version": "26.04", "target": "hygon-z100", "arch": "gfx906"},
  "mpi": {"vendor": "openmpi", "version": "5.0.11"},
  "framework": {"name": "none"},
  "platform": {"adapter": "scnet-openapi", "region": "11250", "cluster": "keshell", "queue": "kshdnormal"}
}
```

## Conflicts and failure diagnosis

No application-level MPI conflict is required because hashcat is launched
directly per rank. Do not mix this module with another hashcat module in the
same job. A missing modulefiles directory, failed `module load`, missing
`hashcat`, or insufficient visible devices is a prerequisite/runtime failure;
the rank log names the failing check and the process exits nonzero. A successful
module load alone is not device evidence.

Validated evidence is limited to the R1 signature, synthetic inputs and the
cases listed in `validation.md`. Other DTK versions, targets, queues and
toolchains require a new probe and validation record.
