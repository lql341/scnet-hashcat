# Distributed execution

English | [中文](parallelization_CN.md)

The coordinator splits one shared input once with GNU `split -n l/N`, preserving
line boundaries. This balances approximate bytes, not necessarily line counts or
compute time. Dictionary mode splits the dictionary; rules mode splits the rule
file and shares the dictionary. One rank runs per node through `srun -K0`.
No rank rewrites another rank's slice. Empty slices are recorded as exhausted.

Rules are hashcat `-a 0 -r`, not the combinator `-a 1`; the latter is not implemented.
The legacy application `--attack 1` retains its older rules-mode meaning.
Masks require one node. Distributed mask scheduling is not implemented.

## Correct keyspace interpretation

The previous documentation inferred dropped mask tokens from `--keyspace` being
smaller than the Cartesian candidate count. That conclusion was unsupported.
Hashcat partitions work into base and modifier loops; `--keyspace` describes base
work positions. The official FAQ explicitly uses four decimal positions returning
1000 as an example. See the
[hashcat FAQ](https://hashcat.net/wiki/doku.php?id=frequently_asked_questions#what_is_a_keyspace).

A future skip/limit scheduler must use the installed version's work-position units
and verify full coverage with synthetic recovery tests. Do not divide a theoretical
candidate total and assume that it matches skip/limit units. No such scheduler is
implemented here, and no claim of a DTK ABI defect is supported by the old measurements.

## Failure and merge behavior

Each rank writes isolated output and an atomic rank record. Failed ranks do not
kill siblings; after all ranks stop, the coordinator enumerates every expected rank.
Missing records, negative hashcat errors, aborts and runtime limits fail the job.
Hashcat 0 (recovered) and 1 (exhausted) are normal. Collection additionally requires
accounting-confirmed completion, and ignores old `pot.merged` during merging.
CPU count in OpenAPI is a job total; multiplying `--cpus-per-node` expresses a
request, but does not prove an even per-node Slurm allocation. DCUs are requested
per node. Each rank checks at least the requested number of visible devices.
