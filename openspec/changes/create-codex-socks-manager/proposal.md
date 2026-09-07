## Why

Codex CLI 更新可能覆盖本机代理 launcher，导致 HTTPS、Responses WebSocket、codex_apps 或远程 MCP 请求失去代理并出现 403。当前脚本和敏感代理配置分散且硬编码 root 路径，需要一个可审计、可迁移、可回滚的 Linux 管理工具。

## What Changes

- 新增 `codex-socks` CLI，提供代理配置的 add/use/list/edit/del/off 生命周期管理。
- 支持 `socks5h`、`socks5`、`http`、`https` URL，凭据以本地 0600 文件保存并在所有输出中脱敏。
- 新增 Codex launcher 安装与 standalone/npm/pnpm 可执行文件发现，为 CLI、app-server、codex_apps 和 MCP 注入大小写代理环境变量。
- 整合现有 backup/restore/check/safe-update 能力，并保留 `codex-proxy-guard` 兼容入口。
- 新增 HTTPS、WSS 101、app-server 进程环境验收与失败回滚。
- 建立公开 GitHub 仓库、CI、Issues、Projects 看板和 v0.1.0 Release；真实配置与快照不得进入仓库。

## Capabilities

### New Capabilities

- `proxy-profile-management`: 管理代理配置、活动状态、安全存储、脱敏输出与原子切换。
- `codex-runtime-integration`: 发现 Codex 安装、安装 launcher、重启 app-server 并验证 CLI/codex_apps/MCP 的代理传递。
- `update-recovery`: 在 Codex 更新前后执行快照、恢复、验收与失败回滚。

### Modified Capabilities

无。

## Impact

- 新增零第三方运行依赖的 Python 包、shell launcher 模板、安装器和测试。
- 写入用户 XDG 配置/状态目录，并管理 `~/.local/bin/codex` 与兼容入口。
- `use`、`restore`、`safe-update` 会重启当前用户的 Codex app-server，可能使当前会话短暂断开。
- 不修改 Codex 二进制、不访问交易系统、不提交代理凭据；远程 403 若来自账号或 ACL，不归类为代理故障。
