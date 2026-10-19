# 运行前置条件

[English](prerequisites.md) | 中文

R1 参考部署使用 Hygon Z100 计算节点上由账户提供的 module。本 skill 不安装、
不随包携带集群运行时。

## 必需环境

- module：`hashcat/7.1.2-dtk26.04-z100`
- modulefiles：账户已有的远端 modulefiles 目录，通常为
  `<动态解析的远端主目录>/modulefiles`
- 队列：`kshdnormal`，每个作业至少申请 1 张 DCU
- 计算节点工具：Bash 登录 shell、Slurm `srun`、GNU `split`，以及所选
  module 提供的 DTK 运行时

指定 `--modulefiles` 时先执行 `module use`，再加载 module。每个 rank 会执行
`hashcat -I`，只有可见的 `Backend Device ID` 数量达到请求值才开始恢复。

## 已验证栈

完整 R1 签名保存在
[`stacks/r1-dtk2604-z100.json`](../stacks/r1-dtk2604-z100.json)，并复制到每次
运行的 manifest：

```json
{
  "system": {"name": "centos7.6", "glibc": "2.17"},
  "toolchain": {"gcc": "16.2.0", "cmake": "4.4.3"},
  "backend": {"kind": "dcu", "runtime": "dtk", "version": "26.04", "target": "hygon-z100", "arch": "gfx906"},
  "mpi": {"vendor": "openmpi", "version": "5.0.11"},
  "framework": {"name": "none"},
  "platform": {"adapter": "scnet-openapi", "region": "11250", "cluster": "keshell", "queue": "kshdnormal"}
}
```

## 冲突与故障诊断

hashcat 按 rank 直接启动，不要求应用级 MPI；同一作业不要混用其他 hashcat
module。modulefiles 目录不存在、module 加载失败、找不到 `hashcat` 或可见设备
不足，均属于前置条件/运行时失败；rank 日志会写明检查项并返回非零。module
加载成功本身不等于设备证据。

当前证据仅覆盖 R1 签名、合成输入及 `validation.md` 中的场景。其他 DTK 版本、
机型、队列或工具链都必须重新探测和验证。
