## Purpose

将活动代理可靠地传递给 Codex CLI、Responses HTTPS/WSS、app-server、codex_apps 和 MCP，同时兼容 Linux 上常见的 Codex 安装来源。

## ADDED Requirements

### Requirement: Codex 安装发现
系统 SHALL 发现 standalone、npm 和 pnpm Codex，并 MUST 避免把受管 launcher 自身识别为真实 Codex。

#### Scenario: standalone 安装
- **WHEN** standalone `current/bin/codex` 可执行
- **THEN** 系统 SHALL 优先记录该稳定入口而不是复制 Codex 二进制

#### Scenario: 无可用 Codex
- **WHEN** 所有受支持来源均不可用
- **THEN** 安装和运行时命令 SHALL 失败且不得覆盖现有 launcher

### Requirement: 受管 launcher
系统 SHALL 安装可恢复的 launcher，为 HTTP_PROXY、HTTPS_PROXY、ALL_PROXY 及其小写形式注入同一活动 URL，合并本地 NO_PROXY 后执行真实 Codex。

#### Scenario: 使用代理启动
- **WHEN** 活动配置不是 `off`
- **THEN** Codex 进程 SHALL 收到完整代理变量且命令参数原样传递

#### Scenario: 直连启动
- **WHEN** 活动配置为 `off`
- **THEN** launcher SHALL 清除代理变量并执行真实 Codex

### Requirement: app-server 应用
`use`、`restore` 和 `safe-update` SHALL 仅管理当前用户且命令行明确匹配 Codex app-server 的进程，并以活动代理重新启动原有角色。

#### Scenario: 切换活动代理
- **WHEN** 用户执行 `use NAME`
- **THEN** 系统 SHALL 更新状态、重启 app-server 并验证新进程继承代理

#### Scenario: 应用失败回滚
- **WHEN** app-server 重启或传输验收失败
- **THEN** 系统 MUST 恢复上一活动配置并尝试恢复上一运行时环境

### Requirement: 传输诊断
`check` SHALL 验证静态配置、Codex Doctor HTTPS、Responses WSS 101、app-server 状态和进程代理环境，并区分代理故障与授权故障。

#### Scenario: WSS 验收成功
- **WHEN** Doctor 返回网络检查正常且握手结果包含 HTTP 101
- **THEN** 系统 SHALL 报告 HTTPS、WSS 和 app-server 传输正常

#### Scenario: 远端返回 403
- **WHEN** 网络通路正常但远端返回账号、workspace、插件或 ACL 拒绝
- **THEN** 系统 SHALL 标记为授权错误且不得声称代理恢复可以解决
