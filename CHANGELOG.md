# Changelog

## 0.2.2 (2026-10-21)

- State the single-skill entry model explicitly: users install/load only
  scnet-hashcat; scnet-hpc is optional for setup, SSH and deployment.
- Add vendor-manifest integrity tests for the embedded OpenAPI adapter.
- Align the architecture reference with the single-skill embedded-adapter pattern.

## 0.2.1 (2026-10-19)

- Align the R1 cluster profile and operational documentation with the
  `hashcat/7.1.2-dtk26.04-z100` module identity.
- Record the complete DTK 26.04 / Z100 stack signature in the validation report.

## 0.2.0 (2026-10-18)

- Identify this application as scnet-app's operational benchmark, with bilingual
  links explaining reusable patterns and infrastructure/contract differences.
- Generalize public titles, prompts and examples to SCNet cluster environments.
- Document one-sentence agent installation, platform-specific installer commands,
  staged prerequisites, credential setup, module readiness and first-run usage.
- Align application layout, English/Chinese docs, XDG region selection and secure
  credential discovery with scnet-hpc; record pinned vendor provenance.
- Add a portable Python driver, retaining `scripts/hc` as a Bash wrapper.
- Make dry-run fully offline; validate queue/quota before upload, use unique runs,
  role-separated inputs, quoted argument vectors and a persistent run manifest.
- Split once before fan-out; isolate logs/sessions, detect missing/failed ranks,
  handle negative/abort exit codes and old Bash empty-array behavior.
- Fix efile pagination with start/limit and preserve region through collection.
- Confirm completion through accounting; propagate wait/collection failure, keep
  recovery artifacts private, exclude stale merged potfiles and count unique hashes.
- Correct mask keyspace interpretation and unsupported CVE protection claims;
  reject unsupported PKZIP validation rather than checking the wrong format.
- Add offline behavioral tests and bounded SCNet cluster-environment synthetic-workload validation.

## 0.1.0 (2026-10-18)

Initial distributed hashcat skill with an OpenAPI adapter, input precheck, Bash
orchestration, multi-node execution and result collection. Earlier mask-defect
and CVE coverage claims are superseded by the corrected 0.2.0 documentation.
