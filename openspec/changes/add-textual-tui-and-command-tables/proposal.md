## Why

现有帮助缺少命令说明和示例，代理列表没有表头；用户必须记住命令才能完成管理。引入 Textual 提供可发现的交互操作，同时完善可直接阅读的 CLI 表格。

## What Changes

- 提供代理、诊断、维护、命令手册四页 TUI，覆盖现有管理能力。
- **BREAKING**：交互终端无参数启动进入 TUI；非交互无参数显示帮助并成功退出。
- 新增 `tui`、双语 `--lang`、共享命令目录，以及帮助和列表表格；JSON 保持兼容。
- **BREAKING**：默认安装 Textual/Rich，shell 安装器改用版本化私有 venv。
- 同步双语文档、安装说明和隔离测试。

## Capabilities

### New Capabilities

- `terminal-ui`：完整交互管理、双语界面、后台操作与结果反馈。
- `command-presentation`：命令说明、示例、列表表格及机器输出兼容。
- `managed-installation`：默认界面依赖、隔离安装及失败时保护旧入口。

### Modified Capabilities

无；主规格目录尚无已归档能力，历史变更保持原状。

## Impact

影响 CLI、操作编排、安装脚本、包依赖和资源、测试、双语 README 与 AGENTS。保留 Python 3.10+、XDG 存储、凭据保护和现有代理/恢复语义；测试只使用临时配置和模拟进程。
