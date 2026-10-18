# 与 scnet-hpc 的关系

[English](architecture.md) | 中文

scnet-hpc 负责基础设施：凭证配置、集群发现、OpenAPI/SSH 和通用作业生命周期。
scnet-hashcat 负责应用：输入角色、hashcat 参数、切分、rank 执行和恢复产物。
应用不另建 SSH 配置流程或第二套凭据库。

scnet-hashcat 同时作为 [scnet-app](https://github.com/lql341/scnet-app) 的运行标杆，
后者规范新 SCNet 应用 skill 的编写。新脚手架调用 scnet-hpc CLI；本应用现有的
分布式驱动和内置适配层属于不同实现。可复用行为及当前规范差异见
[标杆对照](https://github.com/lql341/scnet-app/blob/main/references/hashcat-reference_CN.md)。

当前应用适配层内置精简 OpenAPI 实现，不在运行时导入另一份已安装 skill。
这样可以独立安装，但必须跟进上游认证、文件传输、作业记账变化，不能声称 SDK
自动保持一致。`scripts/vendor-manifest.json` 记录来源提交和辅助模块校验值。
`scnet_credentials.py`、`scnet_version.py` 保持上游原样；`scnet_lite.py`
是单独维护的派生实现，不是未修改的 SDK 快照。

统一约定包括：英文默认/中文翻译、根目录 `VERSION` 和 `CHANGELOG.md`、
`SKILL.md`、`agents/`、`clusters/`、`scripts/`、`references/`、`tests/`，
XDG 非敏感配置、环境变量或系统凭据库、OpenAPI 优先、明确目标、实时资源检查、
有限等待、计算节点证据和错误传播。应用 SemVer 独立，不强行使用 scnet-hpc 版本号。

内置应用 profile 仅保存非个人执行默认项。其他集群需要明确验证对应的 profile/module。
复用 SCNet 区域选择不证明已测环境的 hashcat module 在别处可用。未来有具体需求时，
再通过 backend 接口扩展传输；本版不宣称已支持 SSH 后备。
