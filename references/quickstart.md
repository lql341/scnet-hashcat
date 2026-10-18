# 快速开始（中文）

## 1. 配置凭证（一次性）

```bash
export SCNET_OPENAPI_USER="luql"
export SCNET_OPENAPI_ACCESS_KEY="<你的 AK>"
export SCNET_OPENAPI_SECRET_KEY="<你的 SK>"
```

或写入 `~/.config/scnet-hashcat/config.json`：

```json
{
  "user": "luql",
  "access_key": "<AK>",
  "secret_key": "<SK>"
}
```

> 该文件与 scnet-hpc 技能的配置文件格式一致；如果本机已有
> `~/.config/scnet-hpc/config.json`，本技能会自动读取，无需重复配置。
> Windows 下注意：命令涉及远程绝对路径时先
> `export MSYS2_ARG_CONV_EXCL="*"`，否则 Git Bash 会把 `/public/...`
> 改写成 Windows 路径。

## 2. 自检

```bash
scripts/hc doctor
```

应看到区域、用户名、家目录、账户余额。

## 3. 跑一个任务

```bash
scripts/hc crack --hashes hashes.txt --dict dict.txt --nodes 2 --wait
```

- `--nodes 2`：申请 2 个计算节点，每节点一份词表切片
- `--wait`：阻塞到作业结束并自动回收结果
- 结果落在本地 `./hc-out-<作业号>/`：`pot.merged`（合并后的破解结果）、
  `cracked.<rank>`、`rank.<n>.json`、`report.json`、`std.out`

不带 `--wait` 时先记下作业号，随后：

```bash
scripts/hc status <作业号>
scripts/hc collect <作业号> --out ./results
```

## 4. 常用变体

```bash
# 规则攻击（跨节点切规则文件）
scripts/hc crack --hashes h.txt --dict rockyou.txt --rules best64.rule \
  --attack 1 --nodes 4 --wait

# 掩码攻击（单节点；本环境掩码 keyspace 不可靠，勿跨节点切）
scripts/hc crack --hashes h.txt --mask '?u?l?l?l?l?d?d?d?d' --attack 3 --nodes 1

# 只预览不提交
scripts/hc crack --hashes h.txt --dict d.txt --nodes 4 --dry-run

# 非 MD5 哈希
scripts/hc crack --hashes h.txt --dict d.txt --mode 1000 --wait
```
