## RENAMED Requirements

- FROM: `### Requirement: 默认完整安装`
- TO: `### Requirement: 默认轻量与界面选装`

## MODIFIED Requirements

### Requirement: 默认轻量与界面选装
系统 SHALL 支持 Python 3.10+，默认只安装零第三方运行依赖的 CLI；shell 安装 SHALL 使用用户数据目录中的版本化私有虚拟环境。用户 SHALL 能通过 `./scripts/install.sh --with-tui` 或 pip 安装 `.[tui]` 选择完整界面及所需依赖、样式语言资源。

#### Scenario: 默认首次安装
- **WHEN** 用户不传安装选项且安装成功
- **THEN** 新环境 SHALL 不安装第三方运行依赖，全部核心 CLI 操作和帮助 SHALL 可用

#### Scenario: 显式选装界面
- **WHEN** 用户使用 `--with-tui` 或在目标 Python 环境安装 `.[tui]`
- **THEN** 安装结果 SHALL 支持完整交互界面及全部 CLI 操作

### Requirement: 失败保护
安装器 MUST 完成所选模式的包安装、导入检查及 Codex 发现后才切换入口，保留旧环境和敏感配置；完整模式 MUST 额外通过界面依赖和资源检查，轻量模式 MUST 不以界面依赖存在作为成功前提。

#### Scenario: 依赖安装失败
- **WHEN** 创建环境或安装依赖失败
- **THEN** 安装器 SHALL 返回非零状态并说明原因，旧入口和配置 MUST 保持可用

#### Scenario: 完整模式预检或发布失败
- **WHEN** 用户请求完整模式，但界面预检或入口发布失败
- **THEN** 安装器 MUST 不静默降级为轻量版，MUST 保持或恢复旧入口和配置，并保留旧环境

## ADDED Requirements

### Requirement: 安装模式切换与说明
shell 安装器 SHALL 在每次调用时按本次选项创建新环境；无选项表示轻量模式，`--with-tui` 表示完整模式。系统 MUST 保留既有代理配置和旧环境，SHALL 说明当前安装模式及启动、补装方式。

#### Scenario: 轻量与完整相互切换
- **WHEN** 用户先默认安装，再带 `--with-tui` 安装，最后默认安装
- **THEN** 用户入口 SHALL 依次指向轻量、完整、轻量的新环境，代理配置 MUST 保留，旧环境 MUST 不被删除

#### Scenario: 安装帮助或无效选项
- **WHEN** 用户传入 `--help` 或未知安装选项
- **THEN** 安装器 SHALL 分别输出帮助返回 0，或输出参数错误返回非零；两者 MUST 不创建环境或替换入口
