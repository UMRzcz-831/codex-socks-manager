## Purpose

为 Linux 用户提供安全、可审计且可自动化的代理配置生命周期管理，避免凭据泄露、非原子切换和活动配置被误删。

## ADDED Requirements

### Requirement: 代理配置 CRUD
系统 SHALL 提供 `add`、`list`、`edit`、`del` 与 `use` 命令，并接受 `socks5h`、`socks5`、`http`、`https` URL。

#### Scenario: 新增有效配置
- **WHEN** 用户以合法名称提交受支持的代理 URL
- **THEN** 系统以 0600 权限原子保存配置且不在输出中显示明文凭据

#### Scenario: 拒绝无效配置
- **WHEN** 名称包含路径分隔符或 URL 使用不支持的协议、缺少主机或端口
- **THEN** 系统 SHALL 返回非零状态且不修改现有配置

### Requirement: 安全展示和编辑
系统 MUST 在文本及 JSON 输出中隐藏代理密码，并 SHALL 使用 0600 临时文件完成编辑和校验后原子替换。

#### Scenario: 列出带凭据的配置
- **WHEN** 用户执行 `list` 或 `list --json`
- **THEN** 输出 SHALL 标记活动配置并仅展示脱敏 URL

#### Scenario: 编辑失败
- **WHEN** 编辑器返回非零状态或修改后的 URL 校验失败
- **THEN** 原配置 SHALL 保持不变且临时文件被清理

### Requirement: 活动配置保护
系统 SHALL 拒绝普通删除活动配置；`del --force` MUST 先切换为直连并应用运行时变更后再删除。

#### Scenario: 删除活动配置
- **WHEN** 用户未提供 `--force` 删除活动配置
- **THEN** 系统 SHALL 返回冲突错误且保留配置和当前状态

### Requirement: XDG 与权限
系统 SHALL 使用 XDG 配置和状态目录，目录权限 MUST 为 0700，含凭据文件权限 MUST 为 0600，并通过文件锁避免并发写入。

#### Scenario: 首次运行
- **WHEN** 配置目录尚不存在
- **THEN** 系统 SHALL 创建正确权限的目录和版本化状态文件
