# 代理作用域：Codex CLI 与 Claude Code CLI

状态：首版已实现，2026-09-20。生产 CLI/TUI 已实现只读作用域报告、客户端策略、绕过规则和显式启动；配套 [Textual 原型](prototype.py)仍只使用固定演示数据，用于评审更多冲突状态。

## 1. 用户首先看到什么

新增「作用域 / Scope」页，回答三个问题：**从哪里读到代理、启动哪个客户端时会改变什么、指定请求预计如何连接**。将「启动环境」「客户端采用情况」「网络连通结果」分开，避免把环境变量存在误报为代理已生效。

顶部明确显示观测上下文：客户端、直接或受管启动、工作目录、采集时间、客户端版本。当前终端实际指管理器进程继承的环境快照，不能代表另一个独立终端。

| 展示区域 | 首屏内容 | 展开后内容 |
| --- | --- | --- |
| 客户端 | Codex CLI / Claude Code CLI | 启动入口、版本及已知兼容范围 |
| 四个变量 | 变量、父环境、启动值、客户端判断 | 大小写分别列出、来源链、覆盖原因 |
| 影响范围 | 启动器 → 客户端 → 可能继承的子进程 | 父终端不变、其他终端不变、旧会话不更新 |
| 目标请求 | 预计绕过 / 预计代理 / 无代理变量 / 无法确定 | 命中的规则、来源、依据和未验证项 |
| 后续操作 | 刷新、编辑客户端规则、预览启动 | 保存位置、下一次启动何时采用 |

首屏默认折叠长地址。代理只显示配置名、协议、是否有认证，不显示真实主机、端口或用户信息；未知外部代理用本次报告内的「外部代理 A/B」表示，相同值可在内存中关联，不导出稳定指纹。错误、JSON、复制报告和截图同样隐藏端点。`NO_PROXY` 主界面显示规则数量，本机主动展开可查看规则；分享报告隐藏非示例目标和规则。

### 变量必须解释准确

| 变量 | 面向用户的解释 | 不能表达成 |
| --- | --- | --- |
| `HTTP_PROXY` | 客户端可采用的代理配置，是否用于某类请求由客户端决定 | HTTP 请求必定采用它 |
| `HTTPS_PROXY` | 客户端可采用的代理配置；值的协议描述代理本身 | 值必须以 `https://` 开头 |
| `ALL_PROXY` | 部分客户端或工具支持的通用代理配置 | 系统全局开关、所有流量强制代理 |
| `NO_PROXY` | 在支持它的客户端中，让匹配目标绕过代理 | 关闭整个客户端代理、配置模型 API 地址 |

大写名称是四个展示分组，实际处理八个大小写变量。继承模式不合并冲突值；`未设置`、`空值`、`已设置`分别展示。管理器写入时才按客户端策略规范大小写，并说明覆盖/清除动作。

## 2. 观测与推断的边界

当前 [runtime.py](../../../src/codex_socks_manager/runtime.py)为 Codex 写入六个代理变量，合并 `NO_PROXY` 并同步大小写；关闭时清除六个代理变量。受管 launcher 和 [appserver.py](../../../src/codex_socks_manager/appserver.py)使用该环境。[storage.py](../../../src/codex_socks_manager/storage.py)只有一个 Codex 活动配置，当前没有 Claude 适配器。

| 来源层 | 能确认的事实 | 展示边界 |
| --- | --- | --- |
| 调用环境 | 当前进程实际收到哪些变量 | 来源标「父环境，原始设置位置未知」，不能猜测来自 `.bashrc` |
| 管理器 | 已选择配置、每个变量的写入/删除计划 | 只承诺构造的启动环境 |
| 客户端文件 | 已发现的相关配置键及位置 | 找到文件不等于客户端实际加载；未读取/缺失/失败分别展示 |
| 客户端运行 | 受支持版本返回的状态或用户明确提供的诊断 | 没有证据时标「待客户端核实」 |
| 网络请求 | 特定客户端、目标、时间对应的验证结果 | 代理预测和 TCP 可达均不能代替模型请求成功 |

同一目录不会保存进程环境，但目录内配置可以影响客户端。Claude 检查候选来源包括用户配置目录（考虑 `CLAUDE_CONFIG_DIR`）、项目/本地 settings、显式 `--settings` 和可识别的 managed settings。只提取代理白名单键；不输出认证、hook、完整配置或原始错误。工作树、项目根和配置开关须按支持的客户端版本处理，不能只拼接 `cwd/.claude` 后声称检查完整。未知来源、无法读取的组织策略和不支持的启动参数使结果降为「不完整」。

文件间顺序与「文件 env 和启动环境谁优先」是两个问题。即使知道前者，也不能虚构后者；适配器未覆盖的组合一律显示可能覆盖，不声称管理器一定获胜。静态诊断不执行 `.envrc`、shell rc、hook 或 `apiKeyHelper`；`/proc` 中的启动环境也不是客户端最终配置的证明。

## 3. 双客户端策略

共享代理地址库，客户端策略独立。Codex 保留现有选择；新接入的 Claude 默认「继承」，由用户明确选择自己的 profile，不自动复制 Codex 的代理。共享一个 profile 只表示共享地址，不意味着共享绕过规则、会话或诊断结果。

| 模式 | 构造的启动环境 | 用户可依赖的保证 |
| --- | --- | --- |
| 继承 / Inherit | 保留调用环境，不规范大小写 | 管理器不覆盖；仍可能有代理 |
| 指定配置 / Profile | 按适配器清除旧值、写入所选配置、处理绕过规则 | 新启动进程收到显示的变量 |
| 清除代理变量 / Off | 移除六个代理变量，保留绕过规则 | 仅清除启动变量，不能保证客户端文件或系统网络不再使用代理 |

本设计不把 Off 命名为「强制直连」。客户端 settings 可以重新引入代理；系统代理/透明转发也不在本工具的环境变量保证内。已有 `off` 命令继续只针对 Codex，必须明确显示目标。

### 客户端差异

| 行为 | Codex CLI | Claude Code CLI |
| --- | --- | --- |
| Profile 注入 | 保留目前六个变量同步写入的契约 | 写入 HTTP/HTTPS 的大小写变量；清除继承的 `ALL_PROXY/all_proxy`，在预览中解释 |
| SOCKS profile | 管理器目前接受并注入；实际网络支持需按版本/诊断确认 | 预检拒绝；引导选择 HTTP/HTTPS profile，不自动搭建转换服务 |
| `ALL_PROXY` 展示 | 可显示「已注入，采用情况待检查」 | 显示「官方未列为支持」，不据此预测模型请求走代理；继承值可能影响子工具 |
| 子进程 | 可能受 shell 环境过滤、MCP 配置及网络隔离影响 | 工具可能继承，但各工具可覆盖或忽略 |
| 诊断/更新 | 复用当前 Doctor、app-server 和 safe-update，保持 Codex 专属 | 独立适配；不能调用 Codex Doctor，也不自动重启 Claude 会话 |

核对于 2026-09-20：Claude 官方列出 HTTP/HTTPS 代理、大小写取值顺序和 `NO_PROXY`，明确不支持 SOCKS；其环境变量参考没有列出 `ALL_PROXY`。因此“未列为支持”不写成“已证实无效”。[网络配置](https://code.claude.com/docs/en/network-config)、[环境变量参考](https://code.claude.com/docs/en/env-vars)。

Claude 官方说明 settings 存在用户、项目、本地及组织等层级；启动环境不是一个可直接插进文件优先级列表的统一层。[settings 与优先级](https://code.claude.com/docs/en/settings)。Codex 对工具命令可采用独立环境策略，因此进程树用“可能继承”。[官方 OpenAI 配置说明](https://developers.openai.com/codex/config-advanced/#shell-environment-policy)。

兼容声明限定 Linux 上的前台 CLI 进程。Claude Desktop、云会话和由 supervisor 托管的后台 agent 不自动列入受管范围；原型不模拟这些入口。

### `NO_PROXY` 规则归属

客户端单独保存 `append` / `replace` 策略及规则列表。Profile 模式默认合并本地绕过项、已解析的父环境绕过项和当前客户端规则，逐条保留来源；replace 明确展示被移除的继承规则。继承模式保留原始值，大小写不同则展示冲突，不替用户做合并。

规则输入为主机/IP 或已支持的匹配表达式，不接受完整 URL、认证和路径；「目标请求」字段才接受 URL，并只拿协议、主机、端口参与判断。对裸主机、子域边界、前导点、端口、IPv6、`*`、CIDR 分别记录适配器能力。通用模型不能把各库的匹配差异当成统一标准；未实现语义显示「无法确定」，不使用简单字符串包含判断。原型只演示精确主机匹配，不是生产解析器。

DeepSeek 场景：在 Claude 专属绕过规则中加入用户实际 API 主机，其他请求仍可走代理；若所有 Claude 请求都希望移除代理变量，则选择 Off。演示采用 `api.deepseek.example`，它不是 DeepSeek 真实服务地址。API base URL 与代理路径分开显示，添加绕过规则不改模型、密钥或 API base URL。

## 4. 交互与原型

默认路由：文字需求 → 布局树 → Textual 可运行原型。延续石墨主题，宽屏左侧变量和请求 65%，右侧影响范围和来源 35%；低于 100 列改为上下布局。目标尺寸 120×36 与 80×24。窄屏先显示四行变量和请求结果，长详情向下滚动，变量原始大小写详情仍可由选中行查看。

```text
作用域：客户端 + 入口 + 工作目录 + 快照状态
├── 变量与目标请求 [65%，窄屏 100%]
│   ├── 四行变量：父环境 → 启动值 → 客户端判断
│   ├── 目标 URL + 预计路径 + 匹配原因
│   └── 选中变量：来源、大小写、清除/覆盖动作
├── 影响范围与配置来源 [35%，窄屏下置]
│   ├── 调用终端 → 启动器 → 客户端 → 子进程
│   └── 文件候选、覆盖风险、证据不足
└── 状态 + 键盘操作 [常驻两行]
```

切换客户端仅浏览/编辑该客户端策略，不能立即切换代理。保存和启动分开；保存显示“下次受管启动采用，已有会话不更新”。新 `run` 显式调用可以一次性采用 profile，退出后不影响其他会话；生产 TUI 只有用户选择启动动作才让出终端启动客户端。

原型的场景选择器仅用于评审，提供受管 HTTP、直接启动继承、客户端文件冲突、清除代理变量和 SOCKS 五种演示。切换客户端或勾选 DeepSeek 绕过会更新表格、来源和请求结果；没有联网、配置保存、安装或启动真实客户端的动作。

在项目根运行：

```bash
.venv/bin/python docs/designs/proxy-scope/prototype.py
```

`Tab` 移动焦点，方向键选择变量，`Enter` 确认选择，`F2` 查看变量详情，`F6` 切换客户端，`F7` 切换示例绕过，`Ctrl+Q` 退出。颜色配合文本状态与焦点边框；不以红/绿区分唯一含义。原型支持 `--no-color` 和 `NO_COLOR`；目标实现同时提供中英文文案。

渲染与交互验收由 [preview.py](preview.py)执行，使用临时 XDG 路径和固定数据：

```bash
.venv/bin/python docs/designs/proxy-scope/preview.py --output /tmp/proxy-scope-preview
```

可选 `--png-font /path/to/CJK-font.otf` 生成 PNG（开发预览依赖 `resvg-py`，不加入运行依赖）。[验收记录](verification.md)和 [截图](previews/claude-bypass-120x36.png)随本设计保存。

## 5. CLI

CLI 默认纯标准库、无 ANSI，TUI 通过同一份结构化报告渲染。`scope` 不初始化存储、不运行 Doctor、不探测网络、不修改环境或重启服务；适合在启动 Claude 的那个终端中执行。

```text
codex-socks scope --client claude --entry direct
codex-socks scope --client codex --entry managed --json
codex-socks scope --client claude --entry managed --target https://api.deepseek.example
codex-socks run --client claude --profile office -- <客户端参数>
codex-socks bypass add --client claude api.deepseek.example
```

`scope --entry direct` 展示直接运行客户端时的已知环境与文件候选；`managed` 展示经过本管理器的新进程启动预览。`--target` 为可选项，默认隐藏凭据、路径、查询参数；也提供交互输入，避免把敏感 URL 留在 shell 历史。`run` 的 `--profile NAME`、`--inherit`、`--off` 互斥；`--` 后参数原样传给白名单客户端，使用进程执行接口，不拼 shell 字符串。

`policy set --client claude --mode profile --profile office` 保存 Claude 的默认策略；`bypass add/remove/list --client …` 管理客户端规则。旧 `use/off/check/install/safe-update` 无客户端参数时保持现有 Codex 行为。首版不替换 `claude` 可执行文件，直接 `claude` 仍是未经过管理器的入口。

JSON 报告建议包含 `schema_version`、`client`、`entry`、`observed_at`、`observation_scope`、`variables`、`config_candidates`、`launch_plan`、`route_prediction`、`connectivity`。每行用 `presence`、`source_kind`、`source_status`、`action`、`support`、`evidence` 表示事实与推断；原始敏感值不进入序列化 DTO。运行报告记录启动时快照，规则或上下文改变后标记过期，不能静默替换成新值冒充旧会话实际状态。

## 6. 实现拆分与验收条件

| 阶段 | 涉及文件/新增模块 | 完成条件 |
| --- | --- | --- |
| 1. 只读报告 | 新 `scope.py`、`adapters.py`，接入 operations | 只读调用无文件写入、无初始化副作用、无网络；观察/计划/实际严格区分 |
| 2. 客户端策略 | paths/storage/profiles/recovery，新增独立版本化 `clients.json` | Codex 的 `settings.active` 保持唯一来源；Claude 默认继承；锁、原子写与 0600/0700；备份恢复包含新文件 |
| 3. 显式启动 | runtime/cli/catalog | 识别真实客户端，避免 Codex wrapper 递归；参数、信号、退出码正确；不存在的 Claude 给出可执行错误；拒绝不兼容配置，不影响 Codex |
| 4. 展示与文档 | presentation/tui/manager.tcss，双语 README | 四变量、客户端选择、来源与路由联动；窄屏、键盘、NO_COLOR、未知/冲突/过期状态可读 |
| 5. 回归 | 现有 runtime/operations/recovery/CLI/TUI 测试及新增适配器测试 | 标准库 CLI 与 TUI 两个环境都通过；虚构进程/配置验证继承隔离，不调用真实客户端或代理 |

`clients.json` 缺失时回退到旧 Codex 配置和 Claude 继承策略；恢复旧快照时新策略恢复为默认状态并先保存 pre-restore 备份，不残留与快照不一致的 Claude 规则。不得通过在旧严格解析的 settings 文件塞入未知字段来假装兼容。新增文件与现有 settings 的更新需要同一锁及失败恢复设计。

验收必须覆盖：独立终端同目录不被归因于 Codex；父环境大小写冲突；Claude 项目覆盖候选；匹配/不匹配绕过；Claude SOCKS 拒绝与 ALL_PROXY 不确定；Off 清除变量但客户端文件仍可能覆盖；切换客户端规则隔离；Codex 子进程过滤导致继承不确定；未安装客户端和不可读配置；报告/错误/截图不泄露端点。网络是否连通另列未检查/失败/成功，不能从配置预测自动推导。

首版实现的 `scope` 保持离线，只报告配置与推断；验收不能替代真实 Codex/Claude 版本、代理协议或服务端连通认证。逐 MCP 主动探测、Claude 后台 supervisor 管理和 Desktop/云端入口仍在首版范围外。
