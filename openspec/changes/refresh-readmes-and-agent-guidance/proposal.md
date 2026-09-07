## Why

现有 README 缺少鲜明的项目概括、中文入口和地区可用性说明，仓库也尚无 AGENTS.md。此次完善面向使用者的文档与项目协作约定，保留真实代理配置不得公开的红线。

## What Changes

- 英文 README 使用 `no more codex 403` slogan，整理安装、命令、更新恢复与诊断说明，准确区分目标和已实现能力。
- 新增 `README.zh-CN.md`，两份文档相互链接，保持操作与限制一致。
- 根据官方 API 支持地区页面，列出不在支持列表中的地区示例，注明来源、核对日期、非完整清单及产品范围。
- 根据 Eric Provencher 的文章新增简洁 AGENTS.md：按需读取、适度验证、持续完成已授权工作、明确真实凭据和运行环境边界。

## Capabilities

### New Capabilities

无。纯文档变更，`.openspec.yaml` 设置 `skip_specs: true`。

### Modified Capabilities

无。CLI 行为、运行时配置及服务状态不变。

## Impact

修改 README.md，新增 README.zh-CN.md、AGENTS.md 和本次 OpenSpec 产物。核对来源与代码、运行文档静态检查和密钥扫描；不需要为了文档验证调用生产代理或重启 app-server。沿用本项目已经授权的 GitHub 发布流程同步文档，不修改现有 Release 标签。
