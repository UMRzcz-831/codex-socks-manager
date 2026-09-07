## Why

当前 README 只有文字 slogan，缺少能快速传达“403 焦虑与代理链路恢复”的视觉入口；部分说明也偏机械、密集。此次改动为双语 README 增加统一头图，并在不改变事实和限制的前提下让文案更自然、直接。

## What Changes

- 生成一张包含精确立体 slogan `no more codex 403` 的横向漫画终端海报，以项目命令为背景，文字冲破分镜边框，保存为仓库内的 README 资产。按用户最新要求，图片中的代理案例使用 `socks5://proxy.example.com`。
- 在英文和简体中文 README 顶部引用同一张图片，并为各语言提供自然的替代文本。
- 使用 humanizer-zh 的原则同步润色两份 README 的说明性文字，保留命令、链接、日期、安全提示和功能边界。
- 明确图片与文案只表达对代理传输问题的缓解，不暗示可以绕过账号、地区、workspace 或 ACL 限制。

## Capabilities

### New Capabilities

无。纯文档和图片资产变更，`.openspec.yaml` 设置 `skip_specs: true`。

### Modified Capabilities

无。CLI 行为、公共接口和运行配置不变。

## Impact

修改 `README.md` 与 `README.zh-CN.md`，新增 `docs/assets/readme-hero.png` 及本次 OpenSpec 产物。使用内置图片生成工具，不新增运行时依赖；仅执行文档、图片和 OpenSpec 静态检查，不接触真实代理配置或生产进程。
