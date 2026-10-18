# Runtime diagnosis

English | [中文](pitfalls_CN.md)

- Compute nodes may lack Python 3. The remote executor and summary assembly use
  Bash only; module loads run inside login shells and never in a pipeline.
- Empty Bash arrays with `set -u` behave differently on older CentOS Bash. The
  executor appends extras only when nonempty; regression-test on the target runtime.
- OpenAPI command execution starts on the first node. Explicit `srun` is required
  for fan-out. CPU requests are job totals; DCU requests are per node.
- efile listing uses `start`/`limit`, not `pageNum`/`pageSize`. Fetch all pages;
  a successful first page is not a complete result directory.
- A module loading successfully does not prove DCU visibility. Inspect per-rank
  `devices.<n>.txt` and logs. Record failure without losing healthy siblings.
  Do not embed private node names in public documentation.
- Hashcat session names and outputs must be rank-specific. Disable session logging
  and restore writes for these bounded jobs. The installed binary can still use
  its installation directory for dictionary statistics/cache: deploy a writable
  application prefix and do not point production jobs at a source tree.
- `FINALIZING` is not success. OpenAPI can report realtime `statC` before accounting
  confirms failure or cancellation. Wait for history and check the rank summary.
- Filename guessing is unsafe: hashes and dictionaries can have identical basenames.
  Upload into separate role directories and collect using `run.json`.
- Never infer broken mask generation from `--keyspace` alone. See
  [parallelization](parallelization.md).
- Native Windows: use `python scripts/hc.py`; Git Bash users can set
  `SCNET_HASHCAT_PYTHON` to their native Python executable. Only local path options
  are translated from `/c/...`; remote paths stay POSIX paths.
