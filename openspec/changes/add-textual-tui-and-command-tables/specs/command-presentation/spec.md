## Purpose

提供可读且完整的终端命令说明、参数和示例，使用户可以从帮助页或交互手册了解工具能力；同时保留脚本依赖的 JSON 输出和明确的退出状态。

## ADDED Requirements

### Requirement: 完整命令目录
系统 SHALL 在根帮助及手册以命令、功能、示例三列覆盖原有十二个命令及 tui；子命令帮助 SHALL 包含参数、边界和示例。

#### Scenario: 阅读帮助
- **WHEN** 用户请求根帮助或任一子命令帮助
- **THEN** 系统 SHALL 无需加载真实配置即展示对应内容，隐藏的 no-restart 参数不得公开

### Requirement: 列表及纯文本输出
list SHALL 输出状态、名称、协议、代理地址表头，标记活动配置、脱敏凭据，并显示空列表提示；长地址 SHALL 换行而非丢失。

#### Scenario: 非交互调用
- **WHEN** 输出非终端、NO_COLOR 存在或 TERM 为 dumb
- **THEN** 表格 SHALL 不包含 ANSI 转义；无参数非交互调用 SHALL 输出帮助并返回 0，显式 tui SHALL 返回 2

### Requirement: 双语及 JSON 兼容
系统 SHALL 支持命令前后的 --lang，按显式参数、CODEX_SOCKS_LANG、系统 locale、英文回退选择语言；JSON MUST 不受语言和主题影响。

#### Scenario: 中文环境中的脚本
- **WHEN** 用户执行 list --json 或 check
- **THEN** 字段、值和退出码 MUST 保持现有兼容，输出不得混入标题或控制序列
