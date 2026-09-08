## Why

目前管理器默认安装 Textual 和 Rich，纯 CLI 用户也要承担界面依赖。现有 TUI 的青绿、蓝色和大块按钮抢占注意力，列表、详情与操作缺少清晰层次；需要恢复轻量安装，并统一终端界面的视觉语言。

## What Changes

- **BREAKING**：默认安装改为零第三方运行依赖 CLI；`./scripts/install.sh --with-tui` 或 pip 的 `[tui]` extra 才安装 Textual / Rich。保留 Python 3.10+ 和版本化私有 venv。
- 轻量版无参数显示帮助；完整版本在交互终端无参数进入 TUI。缺少界面依赖时，显式 `tui` 输出双语安装提示并返回 2，不自动下载依赖。
- CLI 帮助和代理列表统一使用标准库纯文本表格，保留双语、完整示例、长地址换行、凭据脱敏与 JSON 兼容性。
- 按 `designing-tuis` 重新设计 Textual 界面：石墨黑、暖白文字、冰蓝单色强调，细边框和紧凑导航；宽屏列表／详情 65%／35%，窄屏上下排列。
- 重绘代理、诊断、维护、命令手册及弹窗，保留全部操作、确认、后台串行、实际回滚结果和诊断状态边界。
- 补齐两种安装模式的隔离测试、设计验收和双语文档。

## Capabilities

### New Capabilities

无独立新增能力，沿用前序变更的三个能力标识。

### Modified Capabilities

- `managed-installation`：默认轻量、界面选装、分模式预检与版本切换失败保护。
- `command-presentation`：去除 CLI 的 Rich 运行依赖，保留双语纯文本表格及 JSON 契约。
- `terminal-ui`：按依赖可用性分流入口，增加石墨黑工作台的布局、主题和无障碍验收要求。

这三个规格目前位于已完成但未归档的 `add-textual-tui-and-command-tables`，尚未进入主规格。本变更以它们为前置基线；同步或归档时必须先落入前序规格，再应用本变更的 MODIFIED / ADDED 增量。本轮不修改或归档前序变更。

## Impact

涉及 `pyproject.toml`、`scripts/install.sh`、`bootstrap.py`、`cli.py`、`presentation.py`、`catalog.py`、`tui.py`、`manager.tcss`、相关测试与 CI，以及双语 README 和 AGENTS。标准库操作服务、代理存储、真实 Codex 执行路径和公开 JSON 结构保持不变。

本次使用 spec-driven，不设置 `skip_specs`。本轮只创建计划，不修改产品代码、不安装到真实用户环境、不重启 app-server、不提交或推送。
