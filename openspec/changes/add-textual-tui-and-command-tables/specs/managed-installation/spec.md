## Purpose

让安装完成后的用户立即获得完整终端界面及 CLI，同时通过用户私有隔离环境管理第三方依赖；升级失败时保留旧入口和原有配置，支持后续恢复。

## ADDED Requirements

### Requirement: 默认完整安装
系统 SHALL 在 Python 3.10+ 下默认安装界面依赖及样式语言资源；shell 安装 SHALL 使用用户数据目录中的版本化私有虚拟环境。

#### Scenario: 首次安装
- **WHEN** Python 支持虚拟环境且依赖安装成功
- **THEN** 用户入口 SHALL 使用新环境，tui、帮助和列表 SHALL 可用

### Requirement: 失败保护
安装器 MUST 完成依赖安装、资源检查及 Codex 发现后才切换入口，保留旧环境和敏感配置。

#### Scenario: 依赖安装失败
- **WHEN** 创建环境或安装依赖失败
- **THEN** 安装器 SHALL 返回非零状态并说明原因，旧入口和配置 MUST 保持可用

### Requirement: 启动路径隔离
真实 Codex 启动路径 MUST 不加载终端界面框架。

#### Scenario: 启动 Codex
- **WHEN** 受管 launcher 转发参数
- **THEN** 系统 SHALL 沿用代理环境和真实二进制执行方式，不初始化 TUI
