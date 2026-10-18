# 踩坑记录（开发期实测，2026-10-18）

按「现象 → 根因 → 对策」记录，全部在 SCNet 昆山集群（区域 11250）实测复现。

## 1. `kshdnormal` 分区只申请 CPU 会被 QOS 拒绝

- 现象：提交报 `min tres(gres/dcu) request 0 exceeds per-job max tres limit 1`
- 根因：`partition_normal` QOS 有 `QOSMinGRES`，最少 1 DCU
- 对策：`--dcus 1` 起步；本技能默认 `--dcus-per-node 4`

## 2. 计算节点默认没有 python3

- 现象：作业 exit 10005，`python3: command not found`
- 根因：计算节点基础镜像只有 `/usr/bin/python`（2.7）
- 对策：作业脚本先 `module load python/3.11.17`（个人 module）。
  **本技能的远端脚本不依赖 python3 跑 hashcat，结果汇总也已改为纯 shell
  （key=value 文件 + printf 拼 JSON）**，计算节点上零 python3 依赖。

## 3. Git Bash 改写远程绝对路径

- 现象：`mkdir /public/home/...` 报「非安全绝对路径」；`files` 报
  `File does not exist`
- 根因：MSYS 参数转换把 `/public/...` 变成
  `C:/Program Files/Git/public/...`
- 对策：命令前 `export MSYS2_ARG_CONV_EXCL="*"`；本技能驱动内部对
  Windows 路径另做了 `cygpath`/`pwd -W` 归一化（`to_native_path`），
  否则原生 Windows python 会把 `/c/...` 读成 `C:\c\...`

## 4. 全局参数位置

`--dry-run / --details / --raw` 必须放在子命令**之前**（scnet-hpc CLI
的约定）。本技能的 `scnet_lite.py` 只保留了 `--region/--timeout` 两个
全局参数，均无歧义。

## 5. `module` 是 shell 函数，不能进管道

- 现象：`module load hashcat/7.1.2-dtk | head` 后 `which hashcat` 为空，
  表现为「加载静默失败」
- 根因：管道创建子 Shell，函数内修改的环境变量不会传回父 Shell
- 对策：`module use` / `module load` 一律独立成行，不接管道

## 6. 软链接部署 hashcat 无效

- 现象：软链到工作目录执行，`hashcat.log` / `hashcat.dictstat2` 仍写回
  源目录
- 根因：hashcat 用 realpath 解析自身路径确定 install_dir
- 对策：**整树拷贝**。本技能依赖已部署好的模块前缀
  （`apprepo/hashcat/7.1.2-dtk`），日志写进模块自己的目录

## 7. hashcat 把 log/dictstat2 写进 install_dir

- 现象：跑了 hashcat 之后，二进制所在目录多出/变大 `hashcat.log`、
  `hashcat.dictstat2`，`--potfile-path` 管不到
- 对策：模块前缀即 install_dir，属模块自有文件；若指向源码/构建树，
  先整树拷贝再跑

## 8. 掩码引擎丢令牌（本环境缺陷）

见 `references/parallelization.md`。结论：跨节点禁用 keyspace 切分，
掩码攻击只单节点跑。

## 9. `--command` 只在首节点执行

- 现象：`--nodes 2` 提交，只有 NODEID=0 的节点有输出
- 根因：OpenAPI 提交的 command 是批处理脚本，非 srun 分发
- 对策：远端脚本内 `srun -N N -n N --ntasks-per-node=1`（已验证 2 节点
  都执行到）

## 10. `--cpus` 是作业总数，`--dcus` 是每节点数

OpenAPI 提交接口的两个资源参数语义不一致（2026-10-18 实测）：

- `GAP_NPROC`（cpus）是**作业总数**，按节点分摊（2 节点 16 核 → 15+1）
- `GAP_NDCU`（dcus）是**每节点**数：2 节点传 8 直接被调度器拒绝
  （`Requested node configuration is not available`），传 4 才正常

本技能用 `--cpus-per-node` 表达意图并自动相乘；`--dcus-per-node` 原样
传递（默认 4 = 单节点上限）。

## 14. 原生 Windows Python 读不懂 `/dev/stdin` 和 `/c/...`

- 现象：驱动里 `echo "$json" | json_get /dev/stdin key` 静默返回空；
  传 `/c/Users/...` 路径给 python 报 `No such file`（实际被 MSYS 改写成
  `C:\c\Users\...`）
- 根因：Git Bash 的参数转换 + 原生 Windows python 不认识 MSYS 路径
- 对策：驱动内统一走 `to_native_path()`（cygpath / pwd -W），JSON 一律
  用 `-` 表示 stdin，临时文件也过原生路径转换

## 15. `A && B || C` 优先级陷阱

- 现象：`[ -n "$RULES" ] && lite upload ... || exit 1`——RULES 为空时
  `[ -n "" ]` 失败，直接触发 `exit 1`，表现为"上传失败但无错误信息"
- 对策：条件上传一律改写为 `if [ -n "$X" ]; then ...; fi`

## 16. argparse 子命令 dest 与选项 dest 撞名

- 现象：`add_subparsers(dest="command")` 又被 `--command` 参数覆盖，
  `args.command` 变成作业命令字符串，分派全部落入 unknown command
- 对策：子命令 dest 用 `op` 等不与选项撞名的名字

## 17. 部分计算节点 DCU 可见性故障（集群侧）

- 现象：`e13r3n19` 连续三次作业分到它，Slurm 正常分配 4 DCU
  （`HIP_VISIBLE_DEVICES=0,1,2,3`），但 `hashcat -I` 枚举到 0 张卡；
  `e13r3n18` 也出现过一次
- 影响：单 rank 失败；本技能的容错设计（失败记入 `rank.<id>.kv`、
  exit 0、`srun -K0`）保证其余 rank 跑完，作业整体 COMPLETED
- 建议：向集群方反馈该节点 DCU 驱动状态；跑重要任务前可用
  `scripts/hc status` 关注 `ranks_failed`

## 11. efile 上传的远端文件名 = 本地文件名

想覆盖远端 `hashcat.log`，本地文件必须叫 `hashcat.log`；传
`hashcat.log.orig` 会在远端新增一个文件。删除用
`POST /openapi/v2/file/remove?paths=<逗号分隔>`（SDK 未封装删除，
`scnet_lite.py` 已实现 `rm` 子命令）。

## 12. bash 大括号组内定义函数

`{ foo() { ...; }; } > file` 会报语法错误。改用
`exec > file 2>&1` 做整脚本重定向。

## 13. hashcat 退出码语义

- `0` = 全部破解；`1` = 跑完未全部破解（**正常结束**，不是错误）
- `2` = 中止；`≥3` = 错误
- 远端脚本把 `≥3` 当失败、`0/1` 当成功，避免 Slurm 误报 FAILED
