## Purpose

在 Codex CLI 更新覆盖 launcher 或改变运行时行为时，提供完整性校验、可恢复快照、自动恢复和可验证的安全更新流程。

## ADDED Requirements

### Requirement: known-good 快照
`backup` SHALL 保存 launcher、代理配置、Codex 配置和管理元数据，不复制 Codex 二进制，并 MUST 生成校验清单。

#### Scenario: 创建快照
- **WHEN** 当前代理链路通过静态检查
- **THEN** 系统 SHALL 创建 0700 快照目录、0600 敏感文件并原子更新 known-good 指针

#### Scenario: 快照被篡改
- **WHEN** 恢复前校验和或权限检查失败
- **THEN** 系统 MUST 拒绝恢复且不覆盖当前文件

### Requirement: 更新后恢复
`restore` SHALL 容忍 launcher 已被替换为软链接或缺失，先保存可用的更新后状态，再恢复代理层、保留新版 Codex 二进制并执行验收。

#### Scenario: launcher 被更新覆盖
- **WHEN** 官方更新器替换受管 launcher
- **THEN** 系统 SHALL 从 known-good 恢复 launcher 并继续使用新版真实 Codex 入口

### Requirement: 一键安全更新
`safe-update` SHALL 按“备份、官方更新、恢复代理层、重启、验收”的固定顺序运行；更新或验收失败时 MUST 返回非零状态。

#### Scenario: 更新成功
- **WHEN** 官方 `codex update` 成功且所有代理检查通过
- **THEN** 系统 SHALL 保留新版 Codex 并报告 safe-update 完成

#### Scenario: 更新命令失败
- **WHEN** 官方更新返回非零状态
- **THEN** 系统 SHALL 恢复代理层、报告原始更新状态并且不得宣称更新成功

### Requirement: 向后兼容
系统 SHALL 提供 `codex-proxy-guard` 兼容入口，支持既有 `backup`、`check`、`restore`、`safe-update` 调用。

#### Scenario: 调用旧命令
- **WHEN** 用户通过兼容入口执行既有子命令
- **THEN** 系统 SHALL 转发到相同行为且不要求迁移真实凭据到仓库
