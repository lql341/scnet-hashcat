# 快速开始

[English](quickstart.md) | 中文

## 凭证与目标

复用 scnet-hpc 已配置的环境变量或系统凭据库。独立使用时，在自己的终端注入
`SCNET_OPENAPI_USER`、`SCNET_OPENAPI_ACCESS_KEY`、`SCNET_OPENAPI_SECRET_KEY`。
不在聊天中粘贴密钥，不提交到仓库，不读取明文密钥配置文件。
`$XDG_CONFIG_HOME/scnet-hpc/config.json`（或 `~/.config/scnet-hpc/config.json`）
仅记录非敏感默认项，例如：

```json
{"backend":"openapi","openapi":{"default_region_id":"11250"}}
```

区域优先级：`--region`、`SCNET_HASHCAT_REGION`、`SCNET_OPENAPI_REGION_ID`、
scnet-hashcat/scnet-hpc 保存的默认项、所选 profile。应用仅用 OpenAPI，
不静默切换 SSH。凭证配置、module 部署和 shell 排障由 scnet-hpc 处理。

## 检查和运行

```bash
python3 scripts/hc.py doctor --region 11250
python3 scripts/hc.py precheck --hashes tests/data/hashes.txt --mode 0
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --dry-run
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --region 11250 --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
```

`--dry-run` 完全本地执行。真实提交在上传前检查实时队列限制和用户配额。
默认 module 为 `hashcat/7.1.2-dtk`，modulefiles 位于动态解析的远端主目录下，
可用 `--module`、`--modulefiles` 覆盖。静态模块名不证明可用；每个计算 rank
加载模块后检查设备。模块部署是独立的 scnet-hpc 操作。

```bash
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --rules best64.rule --nodes 2 --wait
python3 scripts/hc.py crack --hashes hashes.txt --mask '?d?d' --nodes 1 --wait
python3 scripts/hc.py status <作业号> --region 11250
python3 scripts/hc.py collect <作业号> --region 11250 --out ./results
python3 scripts/hc.py cancel <作业号> --region 11250
```

`--rules` 自动选择规则切分；旧 `--attack 1` 为应用兼容别名，不是 hashcat 的组合攻击。
`--extra-args` 支持 `-O`、`-w N`、`--runtime N`、`--quiet`、`--status`、
`--status-timer N`、`--backend-ignore-opencl`，不允许覆盖流程自己的输出和攻击参数。
达到 runtime 上限或中止仍属未完整执行，即使已找到部分结果。

## 结果和生命周期

每次运行有唯一目录、按角色分开的输入和不含凭证的 `run.json`。
回收按 manifest 定位原始哈希，不猜文件名。产物含 `summary.json`、
`rank.<n>.kv`、`rank.<n>.log`、`devices.<n>.txt`、`pot.<n>`、`pot.merged`、
`cracked.<n>`、`report.json` 和可获得的调度日志。
产物含敏感恢复数据，应私密保存；默认不自动打印明文。

报告记录真实作业号、目标、调度状态和 rank 完整性。计数按唯一输入行与
outfile-format 1 的匹配计算；格式归一化可能导致少计，可查原始 potfile。
正常耗尽候选是执行成功，仍可能有未恢复哈希。

输出目录非空时需显式 `--cover`，替换托管产物并重新合并，避免旧结果混入。
`FINALIZING` 表示等待调度记账；`--wait-timeout` 默认 900 秒，超时不自动取消
远端作业，应使用输出中的 status/cancel 命令。
