# 与 scnet-hpc 的关系

[English](architecture.md) | 中文

`scnet-hashcat` 是用户安装和加载的唯一 skill。`scnet-hpc` 是上游基础设施能力：
凭证配置、集群发现、OpenAPI/SSH 和通用作业生命周期。已有凭证和远端 module 时，
普通 OpenAPI-only hashcat 运行不需要额外加载 `scnet-hpc`；首次配置、SSH、软件
部署或更广泛的诊断再使用它。

应用通过一个最小的内嵌 OpenAPI adapter 保持自包含，不在运行时要求第二个 skill。
这是应用 skill 优选的单 skill 模式，已写入
[scnet-app](https://github.com/lql341/scnet-app) 规范。adapter 复用
`scnet-hpc-openapi` 凭证库和配置约定，不提供 SSH fallback，也不创建第二套
凭证库。

这带来维护责任，而不是自动 SDK 一致性。需要跟进上游认证、文件传输和作业记账
变化；`scripts/vendor-manifest.json` 记录上游仓库、commit、许可证、helper
checksum 和派生 adapter。`scnet_credentials.py`、`scnet_version.py` 保持上游
原样；`scnet_lite.py` 是单独维护的派生实现，不是未修改的 SDK 快照。

应用负责输入角色、hashcat 参数、切分、rank 执行和恢复产物；`scnet-hpc` 负责
基础设施。应用 SemVer 独立，不强行使用 `scnet-hpc` 版本号。
