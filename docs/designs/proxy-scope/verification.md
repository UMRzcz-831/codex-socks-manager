# 原型验收记录

2026-09-20。验证对象仅为本目录中的离线 Textual 原型，不是生产代理功能。未修改 `src/`、安装器、真实配置或已运行会话。

## 实际完成

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 120×36 双栏 | 通过，左栏占可用双栏宽度约 64.96% | [宽屏](previews/claude-bypass-120x36.png)、[manifest](previews/manifest.json) |
| 80×24 上下布局 | 通过，首屏四个变量及请求结果可见，详情可滚动 | [窄屏](previews/claude-bypass-80x24.png)、[下方详情](previews/claude-details-80x24.png) |
| 绕过规则切换 | F7 在预计绕过与预计代理之间切换 | [未绕过](previews/claude-proxy-120x36.png) |
| 客户端规则隔离 | F6 往返切换保持每个客户端自己的绕过选择 | Pilot 断言通过 |
| 文件冲突与 SOCKS | 冲突为无法确定；Claude SOCKS 阻止预览启动；Codex 标采用待检查 | [冲突](previews/claude-conflict-120x36.png)、[Claude SOCKS](previews/claude-socks-120x36.png)、[Codex SOCKS](previews/codex-socks-120x36.png) |
| 继承、Off、无效 URL | 状态与禁用操作符合设计 | Pilot 断言通过 |
| 键盘与缩放 | Tab 可达全部选择器/输入；F2 聚焦详情；80↔120 往返保留四行与结果 | Pilot 断言通过 |
| 无颜色 | 文本结论和 F7 操作保留，使用实际 Textual 单色过滤 | [单色](previews/claude-no-color-80x24.png) |

执行命令：

```bash
.venv/bin/python docs/designs/proxy-scope/preview.py --output docs/designs/proxy-scope/previews --png-font /tmp/NotoSansCJKsc-Regular.otf
.venv/bin/python -m py_compile docs/designs/proxy-scope/prototype.py docs/designs/proxy-scope/preview.py
python3 scripts/check-secrets.py
git diff --check
```

渲染脚本为测试运行创建临时 XDG 路径，所有代理标签与目标主机都是演示数据。SVG 使用 Rich 字格导出并校正 CJK 字宽，PNG 使用本地字体转换；没有 AI 生成截图。窗口顶端装饰来自导出器，不属于应用布局。

人工查看了宽屏、窄屏及文件冲突截图，修复窄屏结果被详情推到首屏下方的问题；宽屏使用现有 graphite token，单色模式保留文字状态。另检查本目录文档相对链接及新增文本空白。

## 验证范围

原型只有中文，英文文案列入正式实现。只有精确主机/本地地址的演示匹配，不包含完整 `NO_PROXY` 语法解析。未执行真实 Codex/Claude、服务连通探测、后台 agent 或 Desktop 集成，也未运行生产测试套件或远程 CI。Pilot 与截图无法证明实体终端中每种字体和刷新行为都一致。

生产功能需按 [设计中的实现与验收阶段](README.md#6-实现拆分与验收条件)继续完成，不能将本次原型验收替代双客户端运行兼容性测试。
