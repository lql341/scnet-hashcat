# 安装教程

[English](installation.md) | 中文

离线示例中的 `<region-id>` 请换成选定区域 ID。

## 安装的是什么

本仓库根目录整体就是 `scnet-hashcat` skill，应一起保留 `SKILL.md`、`agents/`、
`clusters/`、`scripts/`、`references/`、`tests/`、`VERSION` 和许可证。
只复制 `SKILL.md` 不够：驱动要导入辅助模块并上传自带的远端执行脚本。
安装 skill 不会配置 SCNet、开通区域资源、部署 hashcat 或申请算力。

本地需要 Python 3.8+、正常的 HTTPS 证书和 GitHub 下载网络。
运行只用 Python 标准库，不需 pip 包、本地 hashcat、GPU 驱动或 SCNet 密钥。
只有克隆或安装器 Git 后备路线需要 Git。

## Codex：一句话安装

> 使用 `$skill-installer` 从 GitHub 仓库 `lql341/scnet-hashcat` 的根目录（path `.`、ref `main`）安装 `scnet-hashcat`，保留名称且不覆盖已有目录；在安装目录用可用的 Python 3 运行 `scripts/hc.py --help`，报告绝对安装路径；安装阶段不配置凭证、不提交作业。

默认安装到 `$CODEX_HOME/skills/scnet-hashcat`，未设置 `CODEX_HOME` 时为
`~/.codex/skills/scnet-hashcat`。下一轮用 `$scnet-hashcat` 调用。
若未发现，先确认当前宿主实际使用的 skill 目录中有 `scnet-hashcat/SKILL.md`，
再刷新 skill 列表。

## 等价的 Codex 安装器命令

使用本机自带的 system skill-installer，不执行本仓库下载的安装脚本。
在对应 Python 命令可用的终端执行。

Linux / macOS：

```bash
python3 --version
codex_root="${CODEX_HOME:-$HOME/.codex}"
python3 "$codex_root/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo lql341/scnet-hashcat --path . --name scnet-hashcat --ref main --method download
cd "$codex_root/skills/scnet-hashcat"
python3 scripts/hc.py version
python3 scripts/hc.py --help
```

Windows PowerShell：

```powershell
python --version
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
python "$codexRoot/skills/.system/skill-installer/scripts/install-skill-from-github.py" `
  --repo lql341/scnet-hashcat --path . --name scnet-hashcat --ref main --method download
Set-Location "$codexRoot/skills/scnet-hashcat"
python scripts/hc.py version
python scripts/hc.py --help
```

若 Windows 只有 `py -3`，则安装器和驱动都改用 `py -3`。
若没有自带安装器，使用下方克隆/手动路线。下载失败时先解决网络/证书问题，
或使用安装器支持的 Git 方法，不能仅凭 agent 接受提示语就宣称安装完成。

`--path .` 表示 skill 位于仓库根目录，`--name scnet-hashcat` 显式给出安装目录名。
需要固定版本时，把 `--ref main` 改成已存在的 tag 或 commit。
仅测试安装可加 `--dest <绝对测试目录>`，该目录不会被 agent 自动发现。
安装器遇到已有目录会拒绝覆盖。更新前先保留本地修改、把旧安装移至明确的备份位置，
再向空出的目标位置安装指定 ref；本教程不自动覆盖目录或重置凭证。

## 克隆和其他 agent

```bash
git clone https://github.com/lql341/scnet-hashcat.git
cd scnet-hashcat
python3 scripts/hc.py --help
```

Windows 最后一条改用 `python` 或 `py -3`。
克隆后可直接用 CLI，但不会自动向 agent 注册 skill。
其他支持 `SKILL.md` 和 shell/Python 执行的宿主，应按其文档把完整目录放进该宿主
的 skill 目录，子目录名为 `scnet-hashcat`，再刷新发现列表。
`$skill-installer` 是 Codex 路线，不能假定每种 agent 都内置它。

适合具备对应能力宿主的通用提示语：

> 从 https://github.com/lql341/scnet-hashcat 安装根目录的完整 skill 到你文档规定的技能目录，名称为 scnet-hashcat，保留已有安装；核验 SKILL.md 及配套文件，用 Python 3 运行 scripts/hc.py --help 并报告绝对路径；不要配置凭证或提交作业。

## 连接前离线核验

在安装后的 skill 目录运行，Windows 将 `python3` 换成 `python`：

```bash
python3 scripts/hc.py version
python3 scripts/hc.py precheck --hashes tests/data/hashes.txt --mode 0
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --mode 0 --region "<region-id>" --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --dry-run
```

版本应与 `VERSION` 一致；自带哈希应通过预检；最后一条只打印本地计划，不认证、
不上传、不提交。这证明本地包完整，不证明远端已部署 hashcat。
随后按[首次使用与前置条件](quickstart_CN.md)继续。
