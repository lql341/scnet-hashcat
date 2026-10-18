# Relationship to scnet-hpc

English | [中文](architecture_CN.md)

scnet-hpc is the infrastructure skill: credential setup, cluster discovery,
OpenAPI/SSH and general workload lifecycle. scnet-hashcat is an application skill:
input roles, hashcat arguments, splitting, rank execution and recovery artifacts.
Do not duplicate SSH setup or install a second credential store for this application.

scnet-hashcat also serves as the operational reference for
[scnet-app](https://github.com/lql341/scnet-app), which standardizes authoring new
SCNet application skills. New scaffolds call scnet-hpc's CLI; this application's
existing distributed driver and vendored adapter are separate implementations.
See the [reference mapping](https://github.com/lql341/scnet-app/blob/main/references/hashcat-reference.md)
for reusable behavior and current contract differences.

The application adapter currently vendors a focused OpenAPI implementation rather
than importing an independently installed skill at runtime. This keeps installation
self-contained but creates a maintenance obligation: review upstream changes to
authentication, file transfer and job accounting. Do not claim automatic SDK parity.
See `scripts/vendor-manifest.json` for exact source commits and helper checksums.
`scnet_credentials.py` and `scnet_version.py` are unmodified upstream helpers;
`scnet_lite.py` is a maintained derivative, not an unchanged SDK snapshot.

Shared conventions: English default / Chinese translations; root `VERSION` and
`CHANGELOG.md`; `SKILL.md`, `agents/`, `clusters/`, `scripts/`, `references/`,
`tests/`; non-secret XDG configuration; environment or OS credential store;
OpenAPI-first execution; explicit targets; live resource checks; bounded waiting;
compute-node evidence; and failure propagation. Application SemVer is independent
of scnet-hpc's release number.

The bundled application profile carries only account-neutral execution defaults. Other
clusters require an explicitly validated application profile/module. Reusing an
SCNet region selection does not prove that the tested deployment's hashcat module works there.
Future transports should fit behind a backend interface after a concrete need
exists; this release does not advertise an unimplemented SSH fallback.
