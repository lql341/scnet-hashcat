# 快速开始

[English](quickstart.md) | 中文

命令中的 `<region-id>`、`<queue>` 须换成实际已配置目标；它们属于执行选择，不属于应用名称或定位。

## 首次使用的前置条件

未安装时先看[安装教程](installation_CN.md)。下文命令在安装后的 skill 根目录执行，
Windows 把 `python3` 换成 `python` 或 `py -3`。agent 应先解析实际安装目录的绝对路径。

1. 本地 Python 3.8+ 和完整 skill 即可查看帮助、预检和 dry-run；这些操作不要求
   本地 GPU、hashcat 或 SCNet 凭证。
2. 真实操作需已开通目标区域的 SCNet 账号、队列权限、足够余额和配额。
   按实际超算互联网集群环境选择区域 ID、profile 和队列，并验证兼容性。
3. 准备平台用户名及 HPC OpenAPI AK/SK，不是模型 API Key、账号密码或 SSH 私钥。
   作业/文件操作走 OpenAPI，单独部署软件或远端 shell 排障才可能需要 scnet-hpc 的 SSH。
4. 远端账户已有兼容 hashcat module、已存在且可读的 modulefiles 目录，以及所有
   计算节点可访问的共享可写运行目录。计算节点需 Bash、Slurm/srun、GNU split 和
   适配的 DCU/DTK 环境，不要求 Python 3 或计算节点互联网访问。
5. 准备有权处理、符合所选模式的离线哈希，以及字典或单节点掩码。
   `--mode 0` 是 MD5，不是自动识别。驱动不从原始文件提取哈希，
   也不支持任意 hashcat 选项，例如当前不能直接加 `--username`。

## 获取凭证并在本机配置

在 SCNet **个人中心 → 访问控制**生成并下载 HPC 授权码文件，填写平台用户名及
文件中的 `Accesskey`、`Secretkey` 值，见
[官方 AK/SK 说明](https://www.scnet.cn/ac/openapi/doc/2.0/api/safecertification/get-user-tokens-aksk.html)。
只有密钥不自动开通区域资源；账号/资源准备见
[SCNet 新手指南](https://www.scnet.cn/help/docs/mainsite/hpc/beginner-guide/)。

优先复用已有 scnet-hpc 配置。首次配置可先
[安装 scnet-hpc](https://github.com/lql341/scnet-hpc#installation)，把下方占位符
换成其实际绝对安装目录，在**本人可见的终端**运行：

```bash
python3 "<scnet-hpc绝对安装目录>/scripts/scnet.py" setup new --mode openapi
python3 "<scnet-hpc绝对安装目录>/scripts/scnet.py" setup status
```

Windows 改用 `python`；修改已有配置使用 `setup modify --mode openapi`。
共享服务名为 `scnet-hpc-openapi`，支持 Windows 凭据管理器、macOS Keychain、
Linux Secret Service。Linux 需要 `secret-tool` 和已解锁的会话密钥环，
Ubuntu/Debian 包名为 `libsecret-tools`。以 setup status 的实际来源为准：
保存区域不等于保存了凭据。本 hashcat skill 没有另一套 setup 界面。

独立使用时，通过宿主的秘密注入或本人终端成套设置下文三个环境变量。
它们是进程秘密，不是持久凭据库。在另一个终端设置不会传给已经运行的 agent；
应在该终端运行 CLI、从该终端启动 agent，或使用共享系统凭据库。
只设置一部分变量会报错，不与存储中的值混合。不要把实际密钥发到聊天或写进 JSON。

在本人终端交互输入，工作目录为安装后的 skill 根目录；下例不保存凭据文件。
Linux/macOS Bash：

```bash
read -r -p 'SCNet platform username: ' SCNET_OPENAPI_USER
read -r -s -p 'AccessKey: ' SCNET_OPENAPI_ACCESS_KEY
printf '\n'
read -r -s -p 'SecretKey: ' SCNET_OPENAPI_SECRET_KEY
printf '\n'
export SCNET_OPENAPI_USER SCNET_OPENAPI_ACCESS_KEY SCNET_OPENAPI_SECRET_KEY
python3 scripts/hc.py doctor --region "<region-id>"
```

Windows PowerShell：

```powershell
$env:SCNET_OPENAPI_USER = Read-Host 'SCNet platform username'
$env:SCNET_OPENAPI_ACCESS_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'AccessKey' -AsSecureString)).Password
$env:SCNET_OPENAPI_SECRET_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'SecretKey' -AsSecureString)).Password
python scripts/hc.py doctor --region "<region-id>"
```

## 先核对远端 module，再跑小作业

安装 skill 不会部署 hashcat。默认使用 `hashcat/7.1.2-dtk` 和
`<动态解析的远端主目录>/modulefiles`，不保证新账户已有。
站点使用其他模块/目录时，给 crack 显式传入
`--module <真实模块名> --modulefiles <远端绝对目录>`。
目录必须已存在，模块名本身也不能证明已打补丁。

单独诊断应在**已分配资源的计算节点 login shell** 中加载站点模块目录和模块，
再运行 `hashcat --version`、`hashcat -I`。登录节点 GPU 检查不证明计算节点可用。
没有 module 时先由集群管理员或独立的 scnet-hpc 软件部署任务准备环境。
`doctor` 只查 API 资源，不检查远端二进制或 module。

凭证和 module 就绪后：

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --mode 0 --region "<region-id>" --queue "<queue>" --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --dry-run
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --mode 0 --region "<region-id>" --queue "<queue>" --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --wait --wait-timeout 900
```

最后一条会消耗算力。预期恢复 **7 条中的 5 条**，另外两条故意不在字典覆盖范围。
应核对历史记账完成及预期的一个 rank。不加 `--wait` 时提交后立即返回，保留输出的
作业号、区域和运行目录，用 status/collect 继续。排队或运行超过等待时长时，
先查状态再决定，不直接重复提交；需要停止时显式 cancel。

## 处理自己数据的 agent 提示语

替换路径/模式，说明目标和资源/时间预算。Windows 使用原生本地绝对路径。
哈希、字典、规则参数是**本地**文件；`--work-dir`、`--modulefiles` 是**远端 POSIX** 路径。

> 使用 `$scnet-hashcat` 在我选定的超算互联网集群环境和队列处理我有权恢复的 MD5 文件 `/absolute/local/hashes.txt`，字典为 `/absolute/local/dict.txt`，只用 1 节点 1 DCU、10 分钟时限；检查输入和资源后只提交一次，最多等待 15 分钟并回收结果，报告调度状态和每个预期 rank，不在聊天中打印恢复明文。

> 使用 `$scnet-hashcat` 检查所选超算互联网区域的作业 `<作业号>`，回收到一个新的本地目录，报告缺失或失败的 rank 并保留部分产物。

> 使用 `$scnet-hashcat` 取消所选超算互联网区域的作业 `<作业号>`，随后查询并报告实际状态。

作业号需替换成真实值。取消请求被接受不等于调度器已完成清理。

## 凭证与目标

复用 scnet-hpc 已配置的环境变量或系统凭据库。独立使用时，在自己的终端注入
`SCNET_OPENAPI_USER`、`SCNET_OPENAPI_ACCESS_KEY`、`SCNET_OPENAPI_SECRET_KEY`。
不在聊天中粘贴密钥，不提交到仓库，不读取明文密钥配置文件。
`$XDG_CONFIG_HOME/scnet-hpc/config.json`（或 `~/.config/scnet-hpc/config.json`）
仅记录非敏感默认项，例如：

```json
{"backend":"openapi","openapi":{"default_region_id":"<region-id>"}}
```

区域优先级：`--region`、`SCNET_HASHCAT_REGION`、`SCNET_OPENAPI_REGION_ID`、
scnet-hashcat/scnet-hpc 保存的默认项、所选 profile。应用仅用 OpenAPI，
不静默切换 SSH。凭证配置、module 部署和 shell 排障由 scnet-hpc 处理。

## 检查和运行

```bash
python3 scripts/hc.py doctor --region "<region-id>"
python3 scripts/hc.py precheck --hashes tests/data/hashes.txt --mode 0
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --dry-run
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --region "<region-id>" --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
```

`--dry-run` 完全本地执行。真实提交在上传前检查实时队列限制和用户配额。
默认 module 为 `hashcat/7.1.2-dtk`，modulefiles 位于动态解析的远端主目录下，
可用 `--module`、`--modulefiles` 覆盖。静态模块名不证明可用；每个计算 rank
加载模块后检查设备。模块部署是独立的 scnet-hpc 操作。

```bash
python3 scripts/hc.py crack --hashes hashes.txt --dict dict.txt --rules best64.rule --nodes 2 --wait
python3 scripts/hc.py crack --hashes hashes.txt --mask '?d?d' --nodes 1 --wait
python3 scripts/hc.py status <作业号> --region "<region-id>"
python3 scripts/hc.py collect <作业号> --region "<region-id>" --out ./results
python3 scripts/hc.py cancel <作业号> --region "<region-id>"
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
