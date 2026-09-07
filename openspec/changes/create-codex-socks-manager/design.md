## Context

现有代理链由 `/root/.local/bin/codex`、多个 `/usr/local/bin` 脚本、`~/.config/openai-proxy/*.env` 与独立 guard 组成。Codex standalone 更新通过 `~/.codex/packages/standalone/current` 切换版本，可能重写 launcher；Codex Doctor 能验证 HTTPS、WSS 和 app-server，但不能替代具体 codex_app 的授权验收。

## Goals / Non-Goals

**Goals:**

- 提供单一、可测试、无第三方运行依赖的 Python CLI 和最小 shell launcher。
- 在普通 Linux 用户与 root 下使用 XDG 路径、安全权限、原子写入和进程级文件锁。
- 支持 standalone、npm、pnpm，迁移当前拆散的 JP/US 配置和 guard 行为。
- 更新后自动恢复代理层，并用真实 Codex Doctor 证明 HTTPS/WSS 传输。

**Non-Goals:**

- 不管理 Codex 登录、workspace、插件或远端 ACL。
- 不复制、修改或自动降级 Codex 二进制。
- v0.1.0 不支持 macOS/Windows、桌面 keyring 或代理服务本身的部署。
- 不声称通用诊断可以替代每个 codex_app 的业务权限 smoke test。

## Decisions

### Python 标准库包与薄 shell launcher

核心采用 Python 3.10+ 标准库，模块分为配置存储、Codex 发现、launcher、app-server、Doctor 和更新恢复。shell launcher 只读取活动配置、导出代理变量并 `exec` 记录的真实 Codex，减少更新期间的依赖面。相比单一 Bash 脚本，Python 更适合 URL/TOML/JSON 校验、原子文件和可移植测试。

### XDG 数据模型

`config.toml` 保存 schema version、活动配置和真实 Codex 路径；每个 `profiles/<name>.conf` 仅保存一行完整 URL。状态目录保存锁、app-server 角色快照和 `backups/<timestamp>`。所有写入使用同目录临时文件、fsync、replace；敏感文件 0600、目录 0700。列表只通过解析后的 scheme、脱敏 userinfo、host、port 生成输出。

### URL 与环境变量

接受 `socks5h`、`socks5`、`http`、`https`，要求显式主机和端口，拒绝控制字符、fragment 和路径外语义。launcher 同时设置 HTTP_PROXY、HTTPS_PROXY、ALL_PROXY 及小写形式，并把 localhost/127.0.0.1/::1 合并进 NO_PROXY。`off` 明确清除所有代理变量。

### Codex 发现和 launcher 安装

发现顺序为 standalone `current/bin/codex`、PATH 中排除受管 launcher 的 `codex`、npm、pnpm。安装前保存原 launcher，状态中记录发现来源和真实路径；不复制 Codex 二进制。更新后重新发现并刷新真实入口，避免版本目录被固定。

### app-server 重启与回滚

只读取当前 UID 的 `/proc`，匹配真实 Codex 路径且参数包含 `app-server` 的 host/proxy 角色。先记录 argv，再 TERM、有界等待、必要时 KILL，随后以新环境和原 argv 重启。若 restart 或 Doctor 验收失败，恢复之前的 active 值并按旧环境重启；两个方向都失败时保留诊断、返回非零且不循环重试。

### Doctor 与错误分类

`check` 解析 `codex doctor --json` 中 network.env、provider_reachability、websocket_reachability 和 app_server.status，并要求 WSS handshake 包含 101。HTTP/WSS 连通失败分类为 transport/proxy；通路正常后的 401/403 分类为 auth/ACL。进程环境只检查变量名存在，不输出值。

### 更新恢复

known-good 快照包含工具文件、launcher、profiles、状态和 Codex 配置副本及 SHA-256 清单。`safe-update` 在子进程执行官方 update；无论 update 状态如何都恢复受管 launcher和活动配置，再验收。pre-restore 快照容忍 updater 产生的 symlink/缺失文件。

## Risks / Trade-offs

- [重启 app-server 会中断当前会话] → CLI 在操作前明确告警，README 建议从独立 SSH shell 执行。
- [SOCKS 支持受 Codex/底层 HTTP 客户端版本影响] → 每次 use/update 都以 Doctor HTTPS/WSS 实测作为成功条件。
- [进程匹配误伤] → 同时限制 UID、真实 Codex 可执行路径和 `app-server` argv，不使用宽泛 pkill。
- [明文代理凭据] → 目录 0700、文件 0600、隐藏输入、脱敏输出、禁止日志和 Git 跟踪。
- [更新后配置格式变化] → 只对 `[features].respect_system_proxy` 做保留式更新，不用旧 config.toml 覆盖新版完整配置。

## Migration Plan

1. 安装新 CLI但不替换 launcher，运行静态自检。
2. 从 `~/.config/openai-proxy/{jp,us}.env` 读取组件并组装 URL，写入新 profile；迁移过程不输出值。
3. 创建 known-good 快照，安装受管 launcher和兼容入口。
4. 保留旧 `/usr/local/sbin/codex-proxy-guard` 及脚本于私密迁移备份。
5. 执行 `check`；失败则恢复原 launcher和旧脚本。
6. GitHub 仓库仅提交模板、测试和文档；本机 profiles/backups 永不提交。
