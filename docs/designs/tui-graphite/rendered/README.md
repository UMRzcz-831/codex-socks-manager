# Textual 实际渲染验收

这些是 2026-09-08 从当前 Textual 实现导出的界面，不是 imagegen 原型。全部使用临时 XDG 目录、回环／保留域名和禁用真实操作的 PreviewManager；没有加载用户配置。图中的终端窗口装饰来自截图导出器，不属于应用布局。

## 页面索引

| 页面 | 中文 80×24 | 中文 120×36 | English 80×24 | English 120×36 |
| --- | --- | --- | --- | --- |
| 代理 | [PNG](profiles-zh-CN-80x24.png) | [PNG](profiles-zh-CN-120x36.png) | [PNG](profiles-en-80x24.png) | [PNG](profiles-en-120x36.png) |
| 诊断 | [PNG](diagnostics-zh-CN-80x24.png) | [PNG](diagnostics-zh-CN-120x36.png) | [PNG](diagnostics-en-80x24.png) | [PNG](diagnostics-en-120x36.png) |
| 维护 | [PNG](maintenance-zh-CN-80x24.png) | [PNG](maintenance-zh-CN-120x36.png) | [PNG](maintenance-en-80x24.png) | [PNG](maintenance-en-120x36.png) |
| 手册 | [PNG](commands-zh-CN-80x24.png) | [PNG](commands-zh-CN-120x36.png) | [PNG](commands-en-80x24.png) | [PNG](commands-en-120x36.png) |

编辑、恢复、删除确认和完整结果窗口也分别导出了中英文两种尺寸：文件前缀为 `edit-`、`restore-`、`del-`、`result-`。每张 PNG 都有同名 SVG。

## 复现

完整开发环境安装 `.[test,tui]` 后，在项目目录运行：

```bash
.venv/bin/python scripts/preview-tui.py --output /path/to/previews
```

默认输出 SVG。PNG 额外需要预览专用的 `resvg-py` 和本地 CJK 字体，不属于管理器运行依赖：

```bash
.venv/bin/python scripts/preview-tui.py --output /path/to/previews --png-font /path/to/CJK-font.otf
.venv/bin/python scripts/preview-tui.py --output /path/to/monochrome --no-color --png-font /path/to/CJK-font.otf
```

导出脚本仅修正 Rich SVG 的 CJK `textLength` 字格计数，不改运行时或框架源码。不要用 AI 原型上的像素坐标替代 Textual 的字符尺寸。

## 验收记录

- 布局：宽屏代理／手册双栏，窄屏上下排列；常驻一行状态和一行快捷键。Pilot 往返缩放通过，宽屏代理分栏偏差在设计比例 65% 的 10% 以内，测量结果在 [manifest.json](manifest.json)。
- 组件：四列代理表、三列手册表、可滚动详情、表单和确认窗口。`>` 光标选择与 `* 当前` 独立；复选框使用 `[ ]`／`[x]`，不是只换颜色。
- 内容：代理地址与命令示例允许换行；长错误用 F2 打开完整结果，Tab／方向键／Page Up／Page Down 可查看。窄屏超出区域的内容需要滚动，不能把首屏截图当成所有内容的总览。
- 安全：初始诊断为尚未检查，旧结果标过期；表单默认隐藏 URL；取消不执行，保存编辑不应用，操作与回滚期间禁止重复提交／普通退出。
- 视觉：按 designing-tuis 的 P0→P4 顺序修复了切页焦点回跳、宽度溢出、缩放断点和默认复选框状态问题，再统一边框与间距。目标尺寸中未发现未解决的布局或组件级问题。
- 无颜色：用 `--no-color` 另行导出，并通过无颜色模式的焦点、活动标记、长结果和键盘滚动测试。

### 对比度

以下为主题 token 的计算值，不是仅凭位图估计。

| 前景 | 石墨背景 | 面板背景 | 选中背景 |
| --- | --- | --- | --- |
| 正文 | 14.91 | 13.34 | 9.08 |
| 次级文字 | 8.27 | 7.40 | 5.03 |
| 冰蓝强调 | 10.40 | 9.31 | 6.33 |
| 警告 | 10.33 | 9.25 | 6.29 |
| 错误 | 8.31 | 7.44 | 5.06 |

普通边框对石墨／面板背景为 4.23／3.78；焦点边框使用冰蓝。正文组合均 >=4.5:1，必要边框组合 >=3:1。

### 自动验证与限制

Python 3.12 本地隔离验证：CLI 环境 100 项通过；完整环境 137 项通过；末轮页面调整后 20 项 TUI 测试再次通过。包括离线 CLI→TUI→CLI 安装、失败保留入口、全部命令、JSON、后台操作和恢复测试。

已运行 secrets 扫描、shellcheck、compileall、diff 空白检查和 OpenSpec 严格校验。校验器提示三个主规格尚未同步：需要先处理前序 `add-textual-tui-and-command-tables`，再归档本变更；本次不归档。

未运行远程 CI、真实代理、真实 app-server 重启或实体终端模拟器验收。快照及 Pilot 验证不能证明所有终端字体、驱动和刷新频率都相同；最终环境仍可能有字体或渲染差异。
