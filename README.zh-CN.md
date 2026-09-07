# Codex SOCKS Manager

> no more codex 403

[English](README.md) · [简体中文](README.zh-CN.md)

让 Codex CLI 每次启动都使用一致的代理配置，并在更新后恢复代理层。一个 Linux 命令行工具，集中管理 SOCKS/HTTP 配置、注入代理环境变量、诊断 HTTPS 与 WebSocket 连接。slogan 表达的是减少代理相关故障的目标；账号访问、服务地区和远端授权仍有各自要求。

## 能做什么

- 管理具名 `socks5h://`、`socks5://`、`http://`、`https://` 代理。
- 为已有 standalone、npm 或 pnpm Codex 安装创建受管 launcher。
- 注入大小写 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`，在 `NO_PROXY` 中保留本地直连项。
- 切换配置、重启当前用户的匹配 app-server 角色，验收失败时回滚活动选择。
- 汇总 Codex Doctor 的 HTTPS、WebSocket、app-server 和代理环境检查。
- 备份、恢复代理层，保留 `codex-proxy-guard` 兼容命令。

## 快速开始

需要 Linux、Python 3.10+ 和已安装的 Codex CLI。Python 运行时仅依赖标准库。`check` 与切换验收要求 Codex 支持 `doctor --json`；`safe-update` 要求支持 `codex update`。

```bash
git clone https://github.com/UMRzcz-831/codex-socks-manager.git
cd codex-socks-manager
./scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"

# 在隐藏输入提示中粘贴代理 URL。
codex-socks add office
codex-socks list

# 需要已有可匹配的 Codex app-server 进程。
codex-socks use office
codex-socks check
```

安装器写入用户本地命令并替换 `~/.local/bin/codex`。如果已有自定义 launcher，请先备份。把 `~/.local/bin` 放在 shell 的 `PATH` 前部。可用 `PYTHON=/path/to/python3 ./scripts/install.sh` 指定解释器。

也可以在选定的 Python 环境执行 `python3 -m pip install .`，再运行该环境的 `codex-socks install`。请保留这个环境，生成的 launcher 会使用其中的 Python。

## 命令速查

| 命令 | 行为 |
| --- | --- |
| `add NAME [URL]` | 新增配置；不传 URL 时隐藏输入。 |
| `list [--json]` | 查看配置和活动选择，用户名、密码脱敏。 |
| `use NAME` | 切换配置，重启匹配的 app-server 并验收。 |
| `use off` / `off` | 清除受管代理变量，重启并验收直连。 |
| `edit NAME` | 通过 `$EDITOR` 编辑 `0600` 临时文件，校验后替换。 |
| `del NAME` | 删除非活动配置。 |
| `del NAME --force` | 活动配置先切换 off 并验收，再删除。 |
| `check` | 输出 Codex Doctor 的 JSON 汇总。 |
| `install` | 发现 Codex，安装或修复受管 launcher。 |
| `backup` | 创建本地快照，存在 Codex 配置时一并备份。 |
| `restore [SNAPSHOT]` | 恢复代理层；默认使用最新 known-good 快照。 |
| `safe-update` | 备份、调用 `codex update`、修复 launcher、重启并验收。 |
| `migrate-legacy [--jp PATH] [--us PATH]` | 导入旧 JP/US 环境文件，不执行其中的 shell 代码。 |

可通过 `EDITOR=vi codex-socks edit office` 临时指定编辑器。编辑活动配置不会重启已有进程；编辑后执行 `codex-socks use office` 应用并验收。

切换会重启发现的 app-server 角色，可能中断正在使用的 Codex 会话；它不会从零启动一个不存在的 app-server。直连不可用时，`off` 可能验收失败并回滚。

无凭据的本地代理可以直接传 URL：

```bash
codex-socks add local socks5h://127.0.0.1:1080
```

真实凭据请使用隐藏输入。命令行中的 URL 可能进入 shell history 和进程参数。`list` 仅隐藏用户名、密码，仍显示主机和端口，分享前应检查。

## 不支持的地区：API 列表示例

OpenAI 只发布 [API 支持的国家和地区列表](https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories)，没有独立的不支持清单。按 **2026-09-07** 核对结果，下列地点未出现在该列表中：

- 中国大陆、香港、澳门、伊朗、朝鲜。
- 俄罗斯、白俄罗斯。
- 古巴、委内瑞拉。

以上是依据支持列表整理的非完整示例，不是官方完整黑名单。官方将乌克兰列为支持地区，但注明存在部分例外；最新情况请核对原文。

该来源说明的是 API 可用范围，不代表所有 Codex 或 ChatGPT 登录方式的完整地区政策。OpenAI 提醒，在支持地区以外访问服务可能导致账号被封禁或暂停。代理配置不会改变服务资格，也不会授予账号或 workspace 权限。

## 诊断与连接器验收

```bash
codex-socks check
```

JSON 汇总包含 `https`、`wss`、`app_server`、`proxy_env`，以及总体 `ok` 和 `category`。这些结果来自 Doctor 输出；通过检查不等于另行审计了所有文件权限、子进程环境或连接器业务操作。

当前 403 分类基于 Doctor 输出中的关键词。`authorization` 和 `proxy_transport` 是诊断线索，并非根因证明。如果代理配置调整后仍无法访问，应检查账号、workspace 权限和远端 ACL。

`codex_apps`/MCP 还需要针对连接器做只读 smoke test：

1. 执行 `codex-socks check` 并查看汇总。
2. 在 Codex 中让已连接的应用读取你有权限访问的内容，例如一个 Issue 标题。
3. 确认返回预期内容，且没有传输或授权错误。包含敏感信息的原始响应和诊断输出只保留在本机。

## 更新与恢复

```bash
codex-socks backup
codex-socks safe-update

# 从已有 known-good 快照恢复：
codex-socks restore
```

`safe-update` 为代理层创建快照，调用已配置的真实 Codex 执行更新，重装 launcher、重启 app-server 并运行 Doctor。失败时尝试恢复快照，不复制或降级 Codex 二进制。更新前先运行 `check` 确认基线健康，并留意恢复过程中的错误。

`restore` 先生成 pre-restore 快照，再恢复管理器设置、profiles 和保存的 launcher，保留当前二进制路径。选定快照中不存在的 profile 会从活动存储中移除，可从 pre-restore 快照找回。`backup` 虽会备份存在的 `~/.codex/config.toml`，但 `restore` 不会自动回写这份 Codex 配置。

`codex-proxy-guard` 兼容入口转发相同的 `backup`、`check`、`restore`、`safe-update` 命令。

## 本地存储与旧配置迁移

| 数据 | 默认位置 |
| --- | --- |
| 管理器设置、代理配置 | `~/.config/codex-socks-manager/` |
| 快照和状态 | `~/.local/state/codex-socks-manager/` |
| shell 安装器部署的 Python 包 | `~/.local/share/codex-socks-manager/` |
| 用户命令、Codex launcher | `~/.local/bin/` |

`XDG_CONFIG_HOME`、`XDG_STATE_HOME` 以及 shell 安装器使用的 `XDG_DATA_HOME` 可覆盖相应根目录。敏感目录使用 `0700`，设置和 profile 文件使用 `0600`。凭据以本地明文保存，快照也需要同等保护。

导入旧配置：

```bash
codex-socks backup
codex-socks migrate-legacy \
  --jp ~/.config/openai-proxy/jp.env \
  --us ~/.config/openai-proxy/us.env
```

不传路径时默认使用上述位置。重复导入相同内容安全，已有配置内容不同时拒绝覆盖。迁移不会改变活动选择，准备重启时再通过 `use` 选择导入的配置。

真实代理 URL、主机信息、凭据、快照、Doctor 输出和日志不得进入公开 Git、Issues 或 CI 日志。仓库提供忽略规则和启发式密钥扫描，提交前也需要检查暂存 diff。

## 参与开发

项目协作约定见 [AGENTS.md](AGENTS.md)，漏洞反馈见 [SECURITY.md](SECURITY.md)。涉及使用方式的修改应同步更新中英文文档。用户要求结构化变更时使用 OpenSpec；纯文档变更可以声明 `skip_specs: true`。

在隔离环境安装开发依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
git config core.hooksPath .githooks
```

按改动范围选择检查：

```bash
git diff --check
python3 scripts/check-secrets.py
openspec validate refresh-readmes-and-agent-guidance --strict
# Python 或 shell 改动适用：
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q src tests
shellcheck .githooks/pre-commit scripts/install.sh
```

采用 MIT 许可证，见 [LICENSE](LICENSE)。
