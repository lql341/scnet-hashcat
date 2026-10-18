# 跨节点并行策略

## 结论先行

**跨节点只能用「文件切分」，不能用 `--skip/--limit` keyspace 切分。**

## 为什么不能用 keyspace 切分

本集群的 hashcat 二进制掩码解析存在缺陷（2026-10-18 复现 8+ 组数据）：
掩码中的 `?X` 令牌会被成组丢弃，keyspace 只保留约 2/3 的令牌数。

| 掩码 | 实测 keyspace | 理论值 |
|---|---|---|
| `?l?l?l` | 676 = 26² | 17576 = 26³ |
| `?d?d?d?d` | 1000 | 10000 |
| `?l`×6 | 26⁴ | 26⁶ |
| `?l`×8 | 26⁵ | 26⁸ |
| `?l?l?d?d` | 2600 | 67600 |
| `?l?d?l?d` | 2600 | 67600（丢了一个 `?l`） |
| `?u?l?u?l` | 17576 = 26⁴ | 456976 = 26⁴…（见下） |

且 `--skip/--limit` 在 `--stdout` 掩码模式下被忽略。二进制是真 ELF，不是
脚本包装。**因此按 keyspace 切分会导致各节点覆盖面错误、漏破解。**

> 规律：保留 `n - floor((n+1)/3)` 个令牌。根因未定位（疑似 DTK HIP ABI
> 适配补丁或编译选项问题），修复前掩码攻击只单节点使用。

## 文件切分（本技能采用）

对共享文件系统上的输入文件做行数均分，每节点一份，与攻击模式无关：

```bash
# 每节点独立执行（hc-node.sh 内部逻辑）
split -n l/$SLURM_JOB_NUM_NODES --numeric-suffixes --suffix-length=3 \
  dict.txt results/dict.part.
# 本 rank 用 results/dict.part.$(printf '%03d' $SLURM_PROCID)
```

- 字典攻击（`-a 0`）：切 `--dict`
- 规则攻击（`-a 1`）：切 `--rules`（字典全员共用，规则各节点一段）
- 组合攻击同理可切其中一侧
- 掩码攻击（`-a 3`）：**不切**，只在 rank 0 单节点全量跑

## 合并

每 rank 独立 potfile（`pot.<rank>`），互不冲突；全部结束后：

```bash
cat pot.* | sort -u > pot.merged
```

`hc collect` 自动完成下载与合并，并输出 `report.json`：

```json
{"job_id": "...", "cracked": 5, "total_hashes": 7, "remaining": 2}
```

## 尾部长尾

文件切分按行数均分，但各节点速度相同（同构 4×DCU 节点）时负载天然均衡；
若集群混构，快的节点会空转。对超大规模任务可在 `hc-node.sh` 里改按
字节数加权切分（`split -n r/N` 近似），本技能暂未实现。

## 单节点就够用的判断

单计算节点 4 张 DCU（Z100，16 GB，64 MCU）。先确认单节点 4 卡跑满
（约 4× 单卡速度）再考虑多节点——多节点有排队和传输成本。
