## MODIFIED Requirements

### Requirement: 完整命令目录
系统 SHALL 在根帮助及手册以命令、功能、示例三列覆盖原有十二个命令及 tui；子命令帮助 SHALL 包含参数、边界和示例。轻量模式 SHALL 保留 tui 的说明并标记为选装能力。

#### Scenario: 阅读帮助
- **WHEN** 用户请求根帮助或任一子命令帮助
- **THEN** 系统 SHALL 无需加载真实配置即展示对应内容，隐藏的 no-restart 参数不得公开

#### Scenario: 未安装界面时阅读帮助
- **WHEN** 环境没有界面依赖，用户请求根帮助或 `tui --help`
- **THEN** 系统 SHALL 正常展示双语说明、选装方式和示例，返回 0，不下载依赖

### Requirement: 列表及纯文本输出
list SHALL 输出状态、名称、协议、代理地址表头，标记活动配置、脱敏凭据，并显示空列表提示；长地址 SHALL 换行而非丢失。CLI 的帮助与列表 SHALL 在两种安装模式下保持一致的无 ANSI 纯文本表格，不依赖第三方运行包；中英文列宽 SHALL 按显示宽度处理。

#### Scenario: 非交互调用
- **WHEN** 标准输入或输出非终端，或 TERM 为 dumb
- **THEN** 表格 SHALL 不包含 ANSI 转义；无参数调用 SHALL 输出帮助并返回 0，显式 tui SHALL 返回 2

#### Scenario: 禁用颜色
- **WHEN** NO_COLOR 存在但终端支持交互
- **THEN** CLI 表格 SHALL 不包含 ANSI 转义，系统 MUST 不仅因禁用颜色而拒绝已安装的 TUI

#### Scenario: 独立轻量环境
- **WHEN** 在未安装任何第三方运行依赖的基础环境运行帮助、list 或核心 CLI 操作
- **THEN** 系统 SHALL 无界面导入错误，命令行为 SHALL 不因缺少界面而改变

#### Scenario: 窄屏中文与长地址
- **WHEN** 用户在窄终端显示中文表头、混合宽度名称及长代理地址
- **THEN** 表格 SHALL 按显示列宽折行，不静默省略名称或地址，活动标记和凭据脱敏 SHALL 保留
