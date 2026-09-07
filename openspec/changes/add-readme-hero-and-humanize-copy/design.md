## Context

见 [proposal.md](proposal.md)。双语 README 已有共享头图及润色文案。本轮按用户反馈将头图调整为漫画破框风格，代理视觉案例改为 `socks5://proxy.example.com`。

## Goals / Non-Goals

**Goals:** 用项目终端命令形成背景纵深，让精确 slogan 以立体漫画字冲出分镜；保留红色 403 的紧张感与青绿色的恢复氛围。

**Non-Goals:** 不改变 CLI 行为、安装流程或正文中的可执行示例，不添加账号解锁或地区绕过暗示。

## Decisions

1. 使用内置 imagegen 编辑现有终端头图，最终 PNG 覆盖 `docs/assets/readme-hero.png`；生成目录保留旧版本，仓库只保留最终资产。
2. 主标题精确为小写 `no more codex 403`，分两行展示。采用倾斜粗体漫画字、米白字面、青绿挤出侧面、红橙色 403、粗墨线、网点阴影和速度线；字形遮挡并突破透视终端分镜边框，所有字母保持可读。
3. 背景显示七条命令：`codex-socks add local socks5://proxy.example.com`、`codex-socks list`、`codex-socks use local`、`codex-socks check`、`codex-socks backup`、`codex-socks safe-update`、`codex-socks restore`。代理地址使用用户指定的示例域名与协议，不添加端口。禁止真实端点、凭据、额外日志、第三方标识和水印。
4. 两份 README 引用同一资产，双语 alt text 描述漫画立体字冲破终端分镜。保留 Markdown 中可复制的 slogan。
5. 已完成的 humanizer-zh 润色和原有命令、代码块、日期、来源、安全提示保持原样；本轮只修改头图与替代文本。

## Risks / Trade-offs

- [复杂透视导致命令或标题难读] → 目视核对完整 slogan、协议、示例域名和七条命令，保证文字与边框碎片分离。
- [图片示例被当作真实代理] → 使用保留示例域名；正文继续提供可执行命令格式与配置条件。
- [视觉被误读为所有 403 都可修复] → 保留 README 的代理传输、账号、地区和授权边界。
- [图片版本增加仓库体积] → 仓库只保留最终 PNG，旧生成结果留在生成目录。

## Image Prompt

模式：内置 imagegen，编辑上一版立体终端海报。最终提示词：

```text
Use case: ads-marketing
Edit target: current README terminal hero image.
Create a dramatically better typographic treatment with the feeling of breaking out of a comic-book dimension, while preserving the terminal-command background and exact lowercase slogan. Wide 2:1 landscape banner.
Foreground lettering exact: "no more codex 403", with "no more" on the upper line and "codex 403" below. All letters lowercase. Monumental custom comic display lettering, boldly italicized, heavy black ink outlines, sharp cel-shaded sculptural extrusions, warm ivory front faces, teal offset rim accents and bright vermilion 403. Strong foreshortening, letters thrust forward OUT THROUGH the terminal panel borders, visibly overlap and fracture angular comic panel frames. Carefully drawn ink strokes, Ben-Day halftone shadow planes, controlled red/cyan print-registration accents. Graphic authored comic-cover aesthetic rather than shiny brushed-metal product rendering. Keep every letter legible and inside the image, including all of "403". Use dynamic angled baselines, subtle size variation and deep extruded shadows, not a generic uniform font.
Background: actual command-line terminal windows with believable monospace typography, receding at varied angles as comic panels. Pane borders break where foreground typography passes through, with a few flying flat ink fragments and energetic speed lines radiating behind the title. Dark charcoal field, restrained off-white paper-texture accents, red tension to cool teal relief. Leave calm areas around background commands so they remain readable. No people or characters.
Top terminal command MUST read exactly "$ codex-socks add local socks5://proxy.example.com". No port, no 127.0.0.1, no socks5h, no socks://.
Retain these other terminal lines exactly, once each:
"$ codex-socks list"
"$ codex-socks use local"
"$ codex-socks check"
"$ codex-socks backup"
"$ codex-socks safe-update"
"$ codex-socks restore"
Only the slogan and these seven commands as text. No sound-effect words, no invented output, no logos, no watermark. No real endpoints or credentials. No unlocking or region bypass imagery.
Hierarchy: huge dimensional slogan first, readable upper command second, quieter supporting terminal panels third. Sophisticated comic art direction: bold shapes, ink texture, perspective and broken panel borders communicate depth. Avoid clutter, excessive sparks, lens flares or gray chrome surfaces.
```
