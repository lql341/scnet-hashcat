# SCNet cluster environment validation

English | [中文](validation_CN.md)

The recorded results apply only to the tested deployment, not all SCNet environments. Replace `<region-id>` with an authorized target when reproducing them.

Validated 2026-10-18 in a selected SCNet cluster environment, using the account's
existing `hashcat/7.1.2-dtk` module. Device evidence: HIP runtime, Device 66a1,
16368 MB per DCU. All recovery inputs were synthetic; walltime was bounded to
three minutes per job. No account hashes or external target data were used.

| Case | Allocation | Expected recovery | Observed | Evidence |
| --- | --- | --- | --- | --- |
| Dictionary split | 2 nodes x 1 DCU | 5/7 | 5/7 | Both ranks exhausted normally; accounting completed |
| Rules split | 2 nodes x 1 DCU | 3/4 | 3/4 | Both ranks exhausted normally; accounting completed |
| Short decimal mask | 1 node x 1 DCU | 3/3 | 3/3 | Hashcat recovered all; accounting completed |
| Full-node DCU visibility | 1 node x 4 DCUs | 5/7 | 5/7 | Four backend devices visible; rank exhausted normally |

The initial single-node run exposed a CentOS Bash empty-array/nounset error.
It was recorded as failed rather than successful; the executor was corrected,
and subsequent runs passed. Collection also exposed incorrect efile pagination:
using `start/limit` retrieved all rank logs and the summary beyond the first page.
A separate dictionary-split run with shared rules recovered the expected 3/4.

These are correctness smoke tests, not scaling benchmarks or a certification of
all hash modes. Multi-node masks, other regions/toolchains, large transfers, module
installation, resume, cancellation lifecycle and account billing were not validated.
A successful short mask does not prove coverage of every possible mask.
The vendor name/version alone does not establish CVE patch status.

## Reproduce within an authorized allocation

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --region "<region-id>" --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
python3 scripts/hc.py crack --hashes tests/data/rules-hashes.txt --dict tests/data/rules-dict.txt --rules tests/data/rules.txt --region "<region-id>" --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
python3 scripts/hc.py crack --hashes tests/data/mask-hashes.txt --mask '?d?d' --region "<region-id>" --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --wait
```

The rule fixtures cover `hello`, `HELLO`, `admin1`, and one intentionally absent
candidate. The mask fixtures cover `00`, `42`, `99`. Test outputs are kept outside
the public repository; no job IDs, personal paths, node names or recovered data
are included in this report.

Local validation: Python 3.12 on Windows, 13 offline Python behavior tests,
input-precheck tests, Bash-wrapper tests and mocked remote execution tests.
CI additionally declares Ubuntu Python 3.8/3.12 and Windows Python 3.12; its
outcome must be checked independently from these local results.
