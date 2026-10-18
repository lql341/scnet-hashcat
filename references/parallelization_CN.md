# 分布式执行

[English](parallelization.md) | 中文

协调进程用 GNU `split -n l/N` 只切一次共享输入，保留完整行。
该方法近似按字节平衡，不保证行数或计算时间相同。字典模式切字典；规则模式
切规则文件、共享字典。`srun -K0` 每节点启动一个 rank，不让失败 rank 杀死其余 rank。
空切片记录为正常耗尽，不反复重写其他 rank 的切片。

规则实际使用 hashcat `-a 0 -r`；尚未实现组合攻击 `-a 1`。
应用旧参数 `--attack 1` 仅保留历史规则模式别名。掩码仅支持单节点，
多节点掩码调度尚未实现。

## keyspace 解释更正

旧文档仅凭 `--keyspace` 小于理论候选数，推断“掩码丢令牌”，依据不足。
Hashcat 将工作分为 base 和 modifier 两层循环，`--keyspace` 描述 base 工作位置。
官方 FAQ 明确举出四位十进制掩码返回 1000 的例子：
[hashcat FAQ](https://hashcat.net/wiki/doku.php?id=frequently_asked_questions#what_is_a_keyspace)。

未来如实现 skip/limit 调度，必须使用安装版本实际的工作位置单位，并用合成哈希
验证候选覆盖，不能直接把理论候选总数当作分片单位。当前没有实现该调度；旧数据
也不能证明 DTK ABI 有问题。

## 失败与合并

各 rank 输出独立文件并原子写入状态。所有 rank 停止后，协调进程核对每个预期 rank。
缺失记录、负数错误、中止、runtime 到期都会使作业失败；只有 hashcat 0（找回）
和 1（耗尽）正常。回收还要求历史记账确认完成，合并时不读取旧 `pot.merged`。
OpenAPI 的 CPU 是作业总数；`--cpus-per-node` 相乘表达申请意图，不保证 Slurm
均匀分配。DCU 按每节点申请；各 rank 检查至少能看到所申请数量的设备。
