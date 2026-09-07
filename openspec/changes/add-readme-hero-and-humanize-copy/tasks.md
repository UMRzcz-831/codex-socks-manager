## 1. README 头图

- [x] 1.1 使用内置 imagegen 生成横向漫画终端海报并保存为 `docs/assets/readme-hero.png`；目视确认项目命令背景、透视分镜、冲破边框的立体 slogan、网点阴影及红橙/青绿配色，没有真实端点、凭据、第三方 logo 或水印。
- [x] 1.2 检查精确小写 slogan `no more codex 403` 与设计中列出的七条背景命令；按用户最新要求将视觉案例改为 `socks5://proxy.example.com`，确认仓库只保留最终 PNG。

## 2. 双语 README

- [x] 2.1 在 `README.md` 与 `README.zh-CN.md` 的一级标题后引用同一头图并添加对应语言的 alt text；确认图片路径有效，Markdown 中的可复制 slogan 保持不变。
- [x] 2.2 按 humanizer-zh 原则同步润色两份 README 的说明性文字；逐项确认 12 个子命令、代码块、链接、日期、安全提示、诊断分类和账号/地区/ACL 边界没有改变。

## 3. 验证

- [x] 3.1 检查双语结构、链接、代码围栏和命令一致性，并按直接性、节奏、信任度、真实性、精炼度进行内部评分，确认两份 README 均达到 45/50 以上。
- [x] 3.2 运行 `git diff --check`、`python3 scripts/check-secrets.py` 和 `openspec validate add-readme-hero-and-humanize-copy --strict`，记录实际结果且不运行生产代理、Codex 更新、app-server 重启或 Python 测试套件。

humanizer-zh 内部评分：`README.md` 47/50（直接性 10、节奏 9、信任度 10、真实性 9、精炼度 9）；`README.zh-CN.md` 47/50（直接性 10、节奏 9、信任度 10、真实性 9、精炼度 9）。本地链接、代码围栏、命令行、日期和官方来源链接已逐项比对。

验证记录：`git diff --check`、`python3 scripts/check-secrets.py` 与 `openspec validate add-readme-hero-and-humanize-copy --strict` 均通过。未运行生产代理、Codex 更新、app-server 重启或 Python 测试套件。
