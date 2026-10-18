# 昆山验证

[English](validation.md) | 中文

2026-10-18 在昆山 SCNet 区域、`kshdnormal` 队列验证，使用账户已部署的
`hashcat/7.1.2-dtk` module。设备证据为 HIP、Device 66a1、每卡 16368 MB。
输入全部为合成测试数据，每个作业时限 3 分钟，没有使用账户哈希或外部目标数据。

| 场景 | 资源 | 预期恢复 | 实际恢复 | 证据 |
| --- | --- | --- | --- | --- |
| 字典切分 | 2 节点，每节点 1 DCU | 5/7 | 5/7 | 两个 rank 正常耗尽，历史记账完成 |
| 规则切分 | 2 节点，每节点 1 DCU | 3/4 | 3/4 | 两个 rank 正常耗尽，历史记账完成 |
| 短数字掩码 | 1 节点、1 DCU | 3/3 | 3/3 | 全部找回，历史记账完成 |
| 整节点设备可见性 | 1 节点、4 DCU | 5/7 | 5/7 | 4 个 backend 设备可见，rank 正常耗尽 |

首次单节点运行暴露 CentOS Bash 空数组与 nounset 的兼容问题，正确记录为失败。
修复后后续作业通过。实测也发现 efile 分页错误；改用 `start/limit` 后才能取回
第一页以外的 rank 日志和汇总。另有一轮“字典切分、共享规则”的测试也按预期恢复 3/4。

这些是正确性冒烟测试，不是扩展性基准，也不证明全部哈希模式可用。
尚未验证多节点掩码、其他区域/工具链、大文件传输、module 部署、断点恢复、
取消生命周期和账户计费。短掩码成功不能外推所有掩码；版本名也不能证明 CVE 补丁状态。

## 在授权资源范围内复现

```bash
python3 scripts/hc.py doctor --region 11250
python3 scripts/hc.py crack --hashes tests/data/hashes.txt --dict tests/data/dict.txt --region 11250 --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
python3 scripts/hc.py crack --hashes tests/data/rules-hashes.txt --dict tests/data/rules-dict.txt --rules tests/data/rules.txt --region 11250 --nodes 2 --dcus-per-node 1 --walltime 00:03:00 --wait
python3 scripts/hc.py crack --hashes tests/data/mask-hashes.txt --mask '?d?d' --region 11250 --nodes 1 --dcus-per-node 1 --walltime 00:03:00 --wait
```

规则样例覆盖 `hello`、`HELLO`、`admin1` 及一个故意不包含的候选。
掩码样例覆盖 `00`、`42`、`99`。原始结果留在公开仓库之外；报告不包含作业号、
个人路径、节点名或恢复结果。

本地验证：Windows Python 3.12、13 项离线 Python 行为测试、输入预检、Bash 包装器、
模拟远端执行均通过。CI 另声明 Ubuntu Python 3.8/3.12 和 Windows Python 3.12，
CI 结果需单独查看，不能以本地通过替代。
