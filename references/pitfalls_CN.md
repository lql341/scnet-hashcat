# 运行排障

[English](pitfalls.md) | 中文

- 计算节点可能没有 Python 3，远端执行和汇总只用 Bash。module 在 login shell
  加载，不接管道。
- CentOS 旧 Bash 的 `set -u` 对空数组行为不同；额外参数非空时才追加到参数数组。
- OpenAPI command 只在首节点开始，需显式 `srun` 分发。CPU 按作业总量，DCU 按每节点申请。
- efile 列表使用 `start/limit`，不是 `pageNum/pageSize`；第一页成功不代表目录回收完整。
- module 加载成功不证明设备可见，检查各 rank 的 `devices.<n>.txt` 和日志。
  单 rank 失败不丢弃其他 rank 结果，公开记录不包含私有节点名。
- session 和输出须按 rank 隔离；禁用 session 日志和 restore 写入。
  字典统计或缓存仍可能使用程序安装目录，应部署可写应用前缀，不直接指向源码树。
- 实时 `statC` 可能先于记账层确认失败或取消；`FINALIZING` 不是成功，需核对历史状态和 rank 汇总。
- 哈希和字典可同名，按角色分目录上传，用 `run.json` 回收，不能猜文件名。
- 不凭 `--keyspace` 推断掩码生成有问题，详见[并行说明](parallelization_CN.md)。
- Windows 可直接运行 `python scripts/hc.py`；Git Bash 可通过 `SCNET_HASHCAT_PYTHON`
  指定原生 Python。仅本地路径选项转换 `/c/...`，远端路径保持 POSIX 格式。
