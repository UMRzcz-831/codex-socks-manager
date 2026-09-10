# Codex SOCKS Manager

![立体漫画字样 no more codex 403 从显示 codex-socks 命令的终端面板中破壁而出](https://raw.githubusercontent.com/UMRzcz-831/codex-socks-manager/main/docs/assets/readme-hero.png)

> no more codex 403

[English](https://github.com/UMRzcz-831/codex-socks-manager/blob/main/README.md) · [简体中文](https://github.com/UMRzcz-831/codex-socks-manager/blob/main/README.zh-CN.md)

Codex SOCKS Manager 把代理配置、app-server 重启、诊断和更新恢复收在一个 Linux 工具里。脚本可以使用零第三方运行依赖的 CLI；日常管理则可选装 Textual 界面。

它解决的是代理传输问题，不能授予账号访问权、开放不支持的地区、修改 workspace 权限或绕过远端 ACL。slogan 是目标，不代表所有 403 都能修复。

![Codex SOCKS Manager TUI 的代理表格与所选配置详情](https://raw.githubusercontent.com/UMRzcz-831/codex-socks-manager/main/docs/designs/tui-graphite/rendered/profiles-zh-CN-120x36.png)

## 功能概览

| 范围 | 管理器会做什么 |
| --- | --- |
| 代理配置 | 保存具名的 `socks5h://`、`socks5://`、`http://` 和 `https://` 地址。 |
| 应用与回滚 | 写入大小写代理环境变量，重启当前用户下匹配的 app-server，通过 Doctor 验收；失败时恢复之前的选择。 |
| 诊断 | 汇总 HTTPS、WebSocket、app-server 和代理环境，不把结果误写成账号授权证明。 |
| 维护 | 安装或修复受管 launcher、创建快照、恢复代理层、迁移旧配置，并为 `codex update` 增加恢复路径。 |
| 使用方式 | 提供 13 个双语 CLI 命令和选装的四页 Textual TUI；机器读取的 JSON 保持不变。 |

只在一个 shell 中使用时，`export ALL_PROXY=...` 已经够用。这个项目适合还要管理多个地址、处理 app-server 生命周期、验收切换结果，并在 Codex 更新后恢复代理层的场景。

## 安装

环境要求：Linux、支持 venv/pip 的 Python 3.10+，以及已经安装的 Codex CLI。配置切换和 `check` 要求 Codex 支持 `doctor --json`；`safe-update` 还要求支持 `codex update`。

### GitHub Release 安装器

推荐使用 Release 安装器。它会下载 GitHub latest 的 wheel、校验 SHA-256、创建版本化私有环境并运行预检，全部通过后才切换命令入口。

```bash
install_dir=$(mktemp -d)
curl -fL https://github.com/UMRzcz-831/codex-socks-manager/releases/latest/download/install.sh \
  -o "$install_dir/install.sh"
curl -fL https://github.com/UMRzcz-831/codex-socks-manager/releases/latest/download/SHA256SUMS \
  -o "$install_dir/SHA256SUMS"
(cd "$install_dir" && awk '$2 == "install.sh" { print }' SHA256SUMS | sha256sum -c -)
sh "$install_dir/install.sh" --with-tui
export PATH="$HOME/.local/bin:$PATH"
```

轻量版去掉 `--with-tui`。安装器默认跟随 GitHub `latest`；需要固定版本时传 `--version v0.3.0`。`/usr/bin/python3` 不是目标解释器时，可设置 `PYTHON=/path/to/python3`。

每次安装都会在 `~/.local/share/codex-socks-manager/venvs/` 新建环境。下载、校验、依赖安装或预检失败都不会改动旧入口；已有配置、私有 bootstrap 备份和旧环境会保留。完整版升级时继续带 `--with-tui`，不带选项会主动切换到新的轻量 CLI 环境。

### 通过 pipx 从 PyPI 安装

这种方式由 `pipx` 管理 Python 环境：

```bash
# 轻量 CLI
pipx install codex-socks-manager

# 或 CLI + TUI
pipx install 'codex-socks-manager[tui]'

# 两种版本安装后都执行一次
codex-socks install
```

后续使用 `pipx upgrade codex-socks-manager` 更新管理器。pipx 不会保留本项目安装器提供的版本化回退环境。

### 从源码安装

```bash
git clone https://github.com/UMRzcz-831/codex-socks-manager.git
cd codex-socks-manager
./scripts/install.sh --with-tui
```

源码安装轻量版时去掉 `--with-tui`。普通 pip 重装不会移除已经安装的 extra；需要严格轻量时请使用新环境。

三种方式最后都会在找到真实的 standalone、npm 或 pnpm Codex 后安装受管的 `~/.local/bin/codex`。自定义 launcher 请先备份。

## 添加第一个配置

URL 含凭据时，使用隐藏输入：

```bash
codex-socks add office
codex-socks list
codex-socks use office
codex-socks check
```

无凭据的本地代理可以直接传入：

```bash
codex-socks add local socks5://127.0.0.1:1080
```

命令行里的 URL 可能留在 shell history 或进程参数中。`list` 会隐藏用户名和密码，但仍会显示主机与端口，分享前要检查输出。

应用配置会重启匹配的 app-server 角色，可能中断当前 Codex 会话。管理器不会启动原本不存在的 app-server。`off` 同样会验收；直连失败时恢复之前的选择。

## Textual 界面

安装完整版后，在交互终端运行 `codex-socks`，或显式执行 `codex-socks tui`。

| 页面 | 可以执行的操作 |
| --- | --- |
| 代理管理 | 新增、编辑、删除、应用或关闭代理。`>` 表示光标位置，`*` 表示活动配置；编辑只保存，不自动应用。 |
| 诊断 | 按需运行 Doctor，查看 HTTPS、WSS、app-server 和代理环境；本地状态变化后，旧结果会标为过期。 |
| 维护 | 修复 launcher、创建备份、选择或手工填写恢复快照、安全更新、迁移旧配置。 |
| 命令手册 | 筛选双语命令表，查看参数、示例和行为边界。 |

石墨黑主题使用暖白文字和冰蓝焦点，橙色、红色只留给警告与错误。终端宽度达到 100 列时，主列表和详情区约按 65/35 分栏；更窄时改为上下排列。支持的紧凑尺寸是 80×24。

界面支持鼠标、Tab、方向键、Enter、Page Up 和 Page Down。快捷键为 `a` 新增、`e` 编辑、`r` 刷新、`l` 切换语言、`q` 退出、`F2` 查看完整操作结果。在输入框中打字时，字母快捷键不会触发。会重启进程或替换数据的操作都要确认；操作和回滚结束前会阻止重复提交与普通退出。

[查看四个页面、两种语言和两种终端尺寸的截图](https://github.com/UMRzcz-831/codex-socks-manager/tree/main/docs/designs/tui-graphite/rendered)。这些截图由真实 Textual 应用配合一次性假配置生成，没有运行真实诊断或代理操作。

```bash
codex-socks tui --lang zh-CN
codex-socks --lang en list
CODEX_SOCKS_LANG=zh-CN codex-socks
```

`--lang` 可放在子命令前后。语言依次取显式参数、`CODEX_SOCKS_LANG`、`LC_ALL` / `LC_MESSAGES` / `LANG`；中文 locale 使用简体中文，其余回退英文。TUI 内切换语言只影响本次会话。

未安装 Textual 和 Rich 时，交互终端下无参数运行会显示帮助并返回 0；显式执行 `tui` 会给出安装方法并返回 2。非交互环境或 `TERM=dumb` 下，无参数也显示帮助，显式 `tui` 返回 2。CLI 表格不输出 ANSI。`NO_COLOR` 模式仍通过文字和符号区分状态。

## 命令参考

| 命令 | 行为 | 示例 |
| --- | --- | --- |
| `add NAME [URL]` | 新增并校验配置；不传 URL 时隐藏输入。 | `codex-socks add office` |
| `use NAME` | 应用配置，重启匹配的 app-server 并验收。 | `codex-socks use office` |
| `list [--json]` | 输出四列表格或稳定的 JSON。 | `codex-socks list --json` |
| `edit NAME` | 通过 `$EDITOR` 和 `0600` 临时文件编辑；保存但不应用。 | `EDITOR=vi codex-socks edit office` |
| `del NAME [--force]` | 删除配置；活动配置要先切换 off 并通过验收。 | `codex-socks del office --force` |
| `off` | 清除受管代理变量，重启匹配角色并验收直连。 | `codex-socks off` |
| `check` | 以 JSON 输出 Doctor 汇总；异常时返回 1。 | `codex-socks check` |
| `install` | 发现 Codex，安装或修复受管 launcher。 | `codex-socks install` |
| `backup` | 创建本地快照；存在 Codex 配置时一并备份。 | `codex-socks backup` |
| `restore [SNAPSHOT]` | 恢复代理层；默认选择最新 known-good 快照。 | `codex-socks restore /path/to/snapshot` |
| `safe-update` | 创建快照、执行 `codex update`、修复 launcher、重启并验收。 | `codex-socks safe-update` |
| `migrate-legacy [--jp PATH] [--us PATH]` | 导入旧 JP/US 环境文件，不执行其中的 shell 内容。 | `codex-socks migrate-legacy --jp /path/to/jp.env --us /path/to/us.env` |
| `tui` | 打开选装的交互管理界面。 | `codex-socks tui` |

执行 `codex-socks -h` 可在终端查看命令表，执行 `codex-socks COMMAND -h` 可查看详细参数、示例和边界。`codex-proxy-guard` 仍是兼容入口，把 `backup`、`check`、`restore` 和 `safe-update` 转给同一实现。

## 诊断与 403 边界

`codex-socks check` 返回 `https`、`wss`、`app_server`、`proxy_env`、总体 `ok` 和 `category`。403 分类根据 Doctor 输出中的关键词判断。`authorization`、`proxy_transport` 等分类是排查线索，不是最终结论。传输检查正常，也不能证明所有文件权限、子进程环境、连接器、账号或 workspace 都没有问题。

使用 `codex_apps` 或 MCP 连接器时，Doctor 之后再做一次账号有权执行的只读请求。如果原始响应和诊断信息含有标识或凭据，只在本机保存。

OpenAI 发布的是 [API 支持的国家和地区列表](https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories)，没有单独的不支持清单。我们在 **2026-09-07** 核对时，中国大陆、香港、澳门、伊朗、朝鲜、俄罗斯、白俄罗斯、古巴和委内瑞拉未出现在列表中。这是根据 API 列表做出的时点推断，不是官方完整黑名单，也不能代表每一种 Codex/ChatGPT 登录方式。OpenAI 提醒，从不支持的地区访问可能导致账号被封禁或暂停。代理不会改变服务资格。

## 更新与恢复

```bash
codex-socks check
codex-socks backup
codex-socks safe-update

# 恢复最新的 known-good 快照：
codex-socks restore
```

`safe-update` 先创建代理层快照，再让已配置的真实 Codex 执行更新，随后修复 launcher、重启 app-server 并运行 Doctor。失败时会尝试恢复快照，并说明回滚是否成功。恢复会保留当前安装的 Codex 二进制版本，不会降级二进制。

`restore` 会先创建 pre-restore 快照，再恢复管理器设置、profiles 和保存的 launcher，同时保留当前 Codex 二进制路径。选定快照中没有的 profile 会离开活动存储，但仍在 pre-restore 快照里。`backup` 会保存已有的 `~/.codex/config.toml`；`restore` 不会自动写回这份 Codex 配置。`known-good` 标签本身不代表已经运行健康检查。

## 存储与迁移

| 数据 | 默认位置 |
| --- | --- |
| 设置与代理配置 | `~/.config/codex-socks-manager/` |
| 快照与状态 | `~/.local/state/codex-socks-manager/` |
| 安装器创建的版本化环境 | `~/.local/share/codex-socks-manager/` |
| 用户命令与受管 Codex launcher | `~/.local/bin/` |

`XDG_CONFIG_HOME`、`XDG_STATE_HOME` 和安装器使用的 `XDG_DATA_HOME` 可以覆盖这些根目录。敏感目录使用 `0700`，设置与 profile 文件使用 `0600`。凭据以明文保存在本机，快照中也一样。

```bash
codex-socks backup
codex-socks migrate-legacy \
  --jp ~/.config/openai-proxy/jp.env \
  --us ~/.config/openai-proxy/us.env
```

两个路径都不传时，迁移使用上面的默认位置。重复导入相同内容是安全的；已有同名但内容不同的配置会被拒绝。迁移不会改变活动选择。

不要把真实代理 URL、主机信息、凭据、快照、Doctor 输出或运行日志放进 Git、Issues、CI 输出或 Release 附件。仓库的忽略规则和启发式扫描能提供帮助，但不能代替对暂存 diff 的检查。

## 开发

项目协作约定见 [AGENTS.md](https://github.com/UMRzcz-831/codex-socks-manager/blob/main/AGENTS.md)，漏洞报告方式见 [SECURITY.md](https://github.com/UMRzcz-831/codex-socks-manager/blob/main/SECURITY.md)，GitHub/PyPI 发布步骤见 [release checklist](https://github.com/UMRzcz-831/codex-socks-manager/blob/main/docs/releasing.md)。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,tui]'
git config core.hooksPath .githooks

.venv/bin/python -m pytest
.venv/bin/python -m compileall -q src tests
python3 scripts/check-secrets.py
shellcheck .githooks/pre-commit scripts/install.sh scripts/install-release.sh
```

CI 在 Python 3.10 和 3.12 下分别运行轻量 CLI 与完整 TUI 任务。离线安装集成测试还需要通过 `CODEX_SOCKS_TEST_WHEELHOUSE` 指定本地 wheel 目录；未设置时只跳过这一项。

项目采用 MIT 许可证，见 [LICENSE](https://github.com/UMRzcz-831/codex-socks-manager/blob/main/LICENSE)。
