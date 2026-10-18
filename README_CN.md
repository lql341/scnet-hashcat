# scnet-hashcat

[English](README.md) | 中文

当前版本：0.2.0

在 [SCNet](https://www.scnet.cn) 计算节点运行 [hashcat](https://hashcat.net/hashcat/)
离线密码恢复任务。应用 skill 与 [scnet-hpc](https://github.com/lql341/scnet-hpc)
统一 profile、OpenAPI、凭证读取、有限资源作业和结果状态约定。

## 安装

向 agent 发送：

> 从 GitHub 仓库 `lql341/scnet-hashcat` 根目录（path `.`）安装 `scnet-hashcat` skill，不覆盖已有目录；安装后在该目录运行 `python3 scripts/hc.py --help`，并报告安装路径。

也可克隆后直接运行：

```bash
git clone https://github.com/lql341/scnet-hashcat.git
cd scnet-hashcat
python3 scripts/hc.py --help
```

本地只需 Python 3.8+ 标准库。Linux/macOS 也可使用 `scripts/hc` 包装器；
Windows 可直接运行 `python scripts/hc.py`，无需 Bash/WSL。远端需要 Linux Bash、
Slurm、GNU split 和可用于所分配 DCU 的 hashcat module。

## 配置和使用

复用 scnet-hpc 的环境变量或系统凭据库（服务名 `scnet-hpc-openapi`）。
`config.json` 只保存非敏感选项。独立使用时注入三项 OpenAPI 环境变量即可，
详见[中文快速开始](references/quickstart_CN.md)。

```bash
python3 scripts/hc.py doctor --region 11250
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --dry-run
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --region 11250 --wait
python3 scripts/hc.py status <作业号> --region 11250
python3 scripts/hc.py collect <作业号> --region 11250 --out ./results
```

默认使用昆山 `kseshell` profile：1 节点、1 张 DCU、共 8 核、10 分钟。
显式参数覆盖默认值；上传和提交前查询实时队列及配额。profile 的静态容量不代表
当前空闲资源。用户须已部署适用的 hashcat module，本 skill 不自动安装集群软件。

字典/规则支持多节点：协调进程只切分一次，每个 rank 单独记录日志和 potfile。
掩码限定单节点。只有历史记账确认完成且所有预期 rank 正常结束，才返回成功。
`--wait-timeout` 限制本地等待时长，超时不自动停止远端作业；可显式 `cancel`。

输入检查是保守启发式，可能拒绝合法长字段，不能保证 CVE 免疫。PKZIP 结构校验
尚未实现，因此默认拒绝；详见[预检边界](references/cve-precheck_CN.md)。
`--keyspace` 较小是正常的 base-loop 语义，不能据此认定掩码丢令牌。

## 结构和验证

仓库采用 `VERSION`、`CHANGELOG.md`、`SKILL.md`、`agents/`、`clusters/`、
`scripts/`、`references/`、`tests/` 分层。默认文档为英文，`*_CN.md` 为中文。

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/test-precheck.py
bash tests/test-driver.sh
bash tests/test-remote.sh
```

[昆山验证与限制](references/validation_CN.md)；
[架构及固定版本来源](references/architecture_CN.md)。

MIT 许可证。OpenAPI 适配层和共享凭证/版本辅助模块派生自 MIT 许可的 scnet-hpc。
