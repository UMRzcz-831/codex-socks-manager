# 原型生成提示词

生成日期：2026-09-08。使用内置 imagegen，未使用 CLI/API fallback。

以下为三张原型各自的完整提示词；生成图是开发视觉参考，不是运行截图。

## 01-profiles-wide

```text
Use case: ui-mockup.
Asset type: high fidelity raster development reference for an existing Linux Textual terminal application, NOT a marketing illustration and NOT a web dashboard.
Project: Codex SOCKS Manager. Make a crisp flat front-on terminal UI prototype with genuinely monospaced type and CJK-compatible Chinese labels, character-grid alignment, square single-line box-drawing borders, no perspective, no gradients, no shadows, no neon, no 3D, no rounded web cards, no OS traffic lights, no decorative logos. Use restrained generous spacing within a practical terminal grid. Header, four compact tabs, content, two-line footer. Palette: graphite background #17191C; surface #202328; warm white #EEECE6; secondary text #ADB2BA; thin borders #737D8C; ice blue accent #9CCBFF; selected row #303F52. Orange #EBC073 only warning and pale red #F29B97 only errors. Never rely on color alone. Compact bracketed buttons, not giant filled buttons. All addresses must be exactly the supplied reserved or loopback examples; no real endpoints, secrets, real person data, third-party logos or watermarks. Use no unsupported performance charts or promises of bypassing restrictions. This is a clean mockup, text must be legible and accurately spelled.
Primary request: One landscape 120-column by 36-row conceptual screen of the Chinese proxy management page, full screen only. Header "Codex SOCKS Manager" left; "当前: office | zh-CN" right. Tabs "[代理管理]  诊断  维护  命令手册"; active tab bold ice blue.
Main body split exactly 65% left table and 35% right details with a one-character gutter. Left panel title "代理配置". Four table columns "状态", "名称", "协议", "代理地址". Rows: "* 当前 | office | socks5 | socks5://proxy.example:1080"; ">      | local | http | http://127.0.0.1:8080"; "—      | backup | https | https://backup.example:8443". The local row is cursor-selected with muted blue-gray background and > prefix; office remains actual active with * 当前. Fit or wrap every address, do not truncate. Plenty of quiet empty rows below.
Right panel title "所选配置"; show "local", "协议  http", "http://127.0.0.1:8080", "尚未检查", "当前配置不代表实时连通", then compact controls "[应用] [编辑]" and "[新增] [关闭] [删除]". Only Apply has ice blue emphasis; Delete is neutral until confirmation. Helper text "编辑仅保存，应用需另行确认".
Footer first line "就绪 · 尚未检查"; second "a 新增  e 编辑  r 刷新  l 语言  q 退出  |  Tab / 方向键 / Enter". No other text, branding or annotations.
```

## 02-diagnostics-maintenance

```text
Use case: ui-mockup.
Asset type: high fidelity raster development reference for an existing Linux Textual terminal application, NOT a marketing illustration and NOT a web dashboard.
Project: Codex SOCKS Manager. Make a crisp flat front-on terminal UI prototype with genuinely monospaced type and CJK-compatible Chinese labels, character-grid alignment, square single-line box-drawing borders, no perspective, no gradients, no shadows, no neon, no 3D, no rounded web cards, no OS traffic lights, no decorative logos. Use restrained generous spacing within a practical terminal grid. Header, four compact tabs, content, two-line footer. Palette: graphite background #17191C; surface #202328; warm white #EEECE6; secondary text #ADB2BA; thin borders #737D8C; ice blue accent #9CCBFF; selected row #303F52. Orange #EBC073 only warning and pale red #F29B97 only errors. Never rely on color alone. Compact bracketed buttons, not giant filled buttons. All addresses must be exactly the supplied reserved or loopback examples; no real endpoints, secrets, real person data, third-party logos or watermarks. Use no unsupported performance charts or promises of bypassing restrictions. This is a clean mockup, text must be legible and accurately spelled.
Primary request: A portrait design sheet containing TWO separate landscape terminal screens stacked vertically with small external captions "诊断 · 初始状态" and "维护 · 操作分组". They are two different pages, NEVER merge these pages into one running application screen. Every screen has the identical header "Codex SOCKS Manager" and "当前: office | zh-CN", its own four tabs and footer.
Top screen: tabs "代理管理 [诊断] 维护 命令手册". One large left bordered panel "检查结果" (65%) and a right panel "说明" (35%). Left rows "HTTPS      — 尚未检查", "WSS        — 尚未检查", "app-server — 尚未检查", "代理环境   — 尚未检查". Below compact "[运行 Doctor]". Right text "手动检查后显示结果", "当前配置不是连通证明", "分类仅作诊断提示". No green success indicators or fake measurements. Footer "就绪 · 尚未检查" and "Tab 切换焦点  l 语言  q 退出".
Bottom screen: tabs "代理管理 诊断 [维护] 命令手册". Three clean horizontally divided groups within main bordered panel titled "维护操作": group "Launcher" with "[修复 launcher]" and "重新安装或修复代理启动层"; group "备份与恢复" with "[备份] [恢复]" and "恢复代理层，不回退 Codex 二进制"; group "更新与迁移" with "[安全更新] [导入旧配置]" and "执行前确认具体影响". Right compact bordered panel "操作提示" with pale orange "! 更新与恢复可能重启 app-server", and ordinary text "确认后执行", "失败时显示实际回滚结果". Footer "就绪" and "Tab 切换焦点  l 语言  q 退出". All buttons neutral bracketed text; warning not a large block. No invented extra controls or claims.
```

## 03-compact-edit

```text
Use case: ui-mockup.
Asset type: high fidelity raster development reference for an existing Linux Textual terminal application, NOT a marketing illustration and NOT a web dashboard.
Project: Codex SOCKS Manager. Make a crisp flat front-on terminal UI prototype with genuinely monospaced type and CJK-compatible Chinese labels, character-grid alignment, square single-line box-drawing borders, no perspective, no gradients, no shadows, no neon, no 3D, no rounded web cards, no OS traffic lights, no decorative logos. Use restrained generous spacing within a practical terminal grid. Header, four compact tabs, content, two-line footer. Palette: graphite background #17191C; surface #202328; warm white #EEECE6; secondary text #ADB2BA; thin borders #737D8C; ice blue accent #9CCBFF; selected row #303F52. Orange #EBC073 only warning and pale red #F29B97 only errors. Never rely on color alone. Compact bracketed buttons, not giant filled buttons. All addresses must be exactly the supplied reserved or loopback examples; no real endpoints, secrets, real person data, third-party logos or watermarks. Use no unsupported performance charts or promises of bypassing restrictions. This is a clean mockup, text must be legible and accurately spelled.
Primary request: A portrait reference sheet with TWO landscape 80-column by 24-row conceptual terminal screens stacked, external tiny captions "80 × 24 · 紧凑布局" and "80 × 24 · 编辑配置". Do NOT create a smartphone frame. Compact wide terminal aspect ratios, legible monospace.
Top screen: header "Codex SOCKS Manager", second line "当前: office | zh-CN"; tabs "[代理管理] 诊断 维护 命令手册". NO side-by-side panels. Upper full-width thin bordered panel "代理配置" with four columns "状态 名称 协议 代理地址", two rows "* 当前 office socks5 socks5://proxy.example:1080" and "> local http http://127.0.0.1:8080". local selected; office active. Lower full-width bordered panel "所选配置" with "local · http", "http://127.0.0.1:8080", short controls "[应用] [编辑] [新增] [关闭] [删除]". Footer "就绪 · 尚未检查" and "a 新增 e 编辑 r 刷新 l 语言 q 退出". Everything fits; text labels not miniature.
Bottom screen: same terminal behind a centered square single-line-bordered modal, background darkened but NOT blurred. Dialog occupies ~70% terminal width. Title "编辑配置". Label "名称" and disabled-looking field "[ local ]". Label "代理 URL" and focused ice-blue-border field filled ONLY with "****************". Checkbox "[ ] 显示 URL". Help line "仅保存配置，不重启；应用需另行确认。". Bottom compact "[保存] [取消]". Footer hint "Tab 切换焦点 · Esc 取消". No plaintext hidden URL, no real credentials, no remote service connections. Match font size, palette and border language of top screen.
```
