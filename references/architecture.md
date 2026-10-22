# Relationship to scnet-hpc

English | [中文](architecture_CN.md)

`scnet-hashcat` is the single skill the user installs and loads. `scnet-hpc` is
the upstream infrastructure capability: credential setup, cluster discovery,
OpenAPI/SSH and general workload lifecycle. It is optional for normal
OpenAPI-only hashcat runs when credentials and the remote module already exist;
use it for first-use setup, SSH, software deployment or broader diagnosis.

The application remains self-contained through a minimal embedded OpenAPI
adapter rather than requiring a second skill at runtime. This is the preferred
single-skill pattern for application skills and is codified in
[scnet-app](https://github.com/lql341/scnet-app). The adapter reuses the
`scnet-hpc-openapi` credential store and config conventions, has no SSH fallback,
and does not create a second credential store.

This creates a maintenance obligation rather than automatic SDK parity. Review
upstream changes to authentication, file transfer and job accounting;
`scripts/vendor-manifest.json` records the upstream repository, commit, license,
helper checksums and the derived adapter. `scnet_credentials.py` and
`scnet_version.py` are unmodified upstream helpers; `scnet_lite.py` is a
maintained derivative, not an unchanged SDK snapshot.

The application owns input roles, hashcat arguments, splitting, rank execution
and recovery artifacts. `scnet-hpc` owns infrastructure concerns. Application
SemVer is independent of the `scnet-hpc` release number.
