# scnet-hashcat

[English](README.md) | 中文

当前版本：0.2.0

在[超算互联网（SCNet）](https://www.scnet.cn)集群环境运行 [hashcat](https://hashcat.net/hashcat/)
离线密码恢复任务。应用 skill 与 [scnet-hpc](https://github.com/lql341/scnet-hpc)
统一 profile、OpenAPI、凭证读取、有限资源作业和结果状态约定。

## 一句话让 agent 安装

将这句话发给 Codex：

> 使用 `$skill-installer` 从 GitHub 仓库 `lql341/scnet-hashcat` 的根目录（path `.`、ref `main`）安装 `scnet-hashcat`，保留名称且不覆盖已有目录；在安装目录用可用的 Python 3 运行 `scripts/hc.py --help`，报告绝对安装路径；安装阶段不配置凭证、不提交作业。

安装后下一轮即可调用。这安装的是**本地 skill**，不会安装远端 hashcat 二进制。
安装和离线规划无需 SCNet 凭证、本地 GPU 或本地 hashcat。
Linux/macOS、Windows 的官方安装器命令、其他 agent 的手动安装、校验和更新方式见
[安装教程](references/installation_CN.md)。

## 前置条件

| 阶段 | 需要准备 |
| --- | --- |
| 安装、查看帮助、输入预检、离线 dry-run | 本地 Python 3.8+，仅标准库；安装时能从 GitHub 下载。只有克隆路线需要 Git。 |
| doctor 查询实时资源 | 已开通目标区域的 SCNet 账号、平台用户名及 HPC OpenAPI AK/SK、本机能访问 SCNet API。 |
| 提交恢复作业 | 队列使用权限、足够余额/配额、账户已部署兼容 hashcat module、已存在的 modulefiles 目录、共享可写远端存储；计算节点具备 Bash、Slurm/srun、GNU split 和适配的 DCU/DTK 环境。 |
| 提供任务输入 | 有权处理的离线哈希、与文件格式匹配的 hashcat 模式（`--mode`，默认 0/MD5），以及字典或单节点掩码；规则文件可选。 |

本地 Linux/macOS 也可使用 `scripts/hc`；Windows 可直接运行 `python scripts/hc.py`，
无需 Bash/WSL。远端不要求 Python 3，也不要求计算节点联网。
首次配置凭证或部署软件推荐配合 `scnet-hpc`；已有凭证和 module 时无需安装它。
只有 AK/SK 并不等于已开通算力资源。
凭证获取、module 就绪要求、逐步命令和排障见[首次运行教程](references/quickstart_CN.md)。

## 如何让 agent 使用

先检查，不提交作业：

> 使用 `$scnet-hashcat` 检查安装版本和我已配置的超算互联网集群环境资源，列出缺少的前置条件，并用自带合成哈希与字典生成离线计划；不要提交作业，缺少凭证时给我在本人终端填写的命令。

凭证及远端 module 就绪后，明确授权小测试：

> 使用 `$scnet-hashcat` 在我选定的超算互联网集群环境和队列运行自带的合成 MD5 字典测试，只用 1 节点、1 张 DCU、3 分钟时限；最多等待 15 分钟，回收结果并核对预期恢复 7 条中的 5 条，报告调度状态和 rank 完整性。

处理自己的数据时，应说明本地输入路径、哈希模式、区域、队列、节点/DCU 预算和时限。
更多提示语及完整 CLI 生命周期见[快速开始](references/quickstart_CN.md)。

## 配置和使用

复用 scnet-hpc 的环境变量或系统凭据库（服务名 `scnet-hpc-openapi`）。
`config.json` 只保存非敏感选项。独立使用时注入三项 OpenAPI 环境变量即可，
详见[中文快速开始](references/quickstart_CN.md)。以下相对路径命令均在安装后的 skill
目录或克隆目录运行；agent 应先解析该目录的绝对路径。将 `<region-id>` 替换为已配置
的目标区域。

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --dry-run
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --region "<region-id>" --wait
python3 scripts/hc.py status <作业号> --region "<region-id>"
python3 scripts/hc.py collect <作业号> --region "<region-id>" --out ./results
```

默认资源：1 节点、1 张 DCU、共 8 核、10 分钟。按实际超算互联网集群环境选择
profile、区域和队列。
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

[超算互联网集群环境验证与限制](references/validation_CN.md)；
[架构及固定版本来源](references/architecture_CN.md)。

MIT 许可证。OpenAPI 适配层和共享凭证/版本辅助模块派生自 MIT 许可的 scnet-hpc。
