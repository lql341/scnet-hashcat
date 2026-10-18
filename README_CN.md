# scnet-hashcat

在 SCNet 超算（海光 DCU / DTK）上跑分布式 [hashcat](https://hashcat.net)
密码破解任务，支持单节点与多节点，自带 CVE 预检与结果自动回收。

通用 agent 技能：驱动是 bash + Python 3 标准库，集群访问层是自包含的
OpenAPI 客户端，不依赖任何特定 agent 平台。

## 特性

- **一条命令跑全流程**：预检 hash 文件 → 上传输入 → 提交多节点 Slurm 作业
  （每节点一个 hashcat、用满 DCU）→ 等待 → 合并 potfile → 汇报。
- **跨节点按文件切分**，不受本集群掩码引擎缺陷影响
  （见 `references/parallelization.md`）。
- **CVE 防护栏**：在 hashcat 读取前拦截构造过的 krb5/PKZIP hash 文件形状
  （CVE-2026-42483，CVSS 9.8；CVE-2026-42484；CVE-2026-68768）。
- **自包含**：`scripts/scnet_lite.py` 是裁剪自
  [scnet-hpc](https://github.com/lql341/scnet-hpc)（MIT）的 OpenAPI
  客户端；凭证与 scnet-hpc 共用。

## 安装

克隆到任意位置，加入 agent 的 skill 目录，或直接运行：

```bash
git clone https://github.com/lql341/scnet-hashcat
cd scnet-hashcat
```

适用于 Claude Code、Codex、WorkBuddy 等任何能执行 shell 命令的 agent。

## 使用

```bash
scripts/hc doctor
scripts/hc crack --hashes hashes.txt --dict rockyou.txt --nodes 4 --wait
scripts/hc status <作业号>
scripts/hc collect <作业号> --out ./results
```

完整说明见 [references/quickstart.md](references/quickstart.md)，
英文版见 [references/quickstart-en.md](references/quickstart-en.md)。

## 环境要求

- 驱动机器 Python 3.8+（仅标准库）。
- SCNet OpenAPI 凭证（环境变量或 `~/.config/scnet-hashcat/config.json`）。
- 集群侧：以 module 形式暴露的 hashcat DCU 版（默认
  `hashcat/7.1.2-dtk`，位于个人 modulefiles 目录）。

## 许可证

MIT。OpenAPI 客户端子集派生自
[lql341/scnet-hpc](https://github.com/lql341/scnet-hpc)（MIT）。
