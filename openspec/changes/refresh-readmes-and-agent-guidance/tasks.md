## 1. 双语使用文档

- [x] 1.1 重写英文 README：包含精确 slogan、完整命令、安装与恢复条件；逐项与当前 CLI 和安装脚本核对。
- [x] 1.2 新增 README.zh-CN.md，包含双向语言链接及与英文一致的地区示例、来源、日期和操作限制；检查双语一致性。

## 2. 项目协作约定

- [x] 2.1 新增简洁 AGENTS.md，落实文章启发、项目凭据红线、按需读取/验证及持续完成要求；核对其中的文件路径和命令存在。

## 3. 验证与交付

- [x] 3.1 检查 Markdown 本地链接、代码围栏、命令与双语内容一致性，运行 diff --check、OpenSpec strict validate 和密钥扫描，记录结果。
- [x] 3.2 将变更提交并快进同步到本地项目和 GitHub，确认远端提交及现有 CI 结果；不改变运行时服务与 Release 标签。

验证记录：6 个 Markdown 文件的本地链接和代码围栏检查通过；README 覆盖全部 12 个 CLI 子命令，两种语言的命令表和 shell 示例一致；slogan、日期和官方链接一致；文档内 IPv4 地址仅为回环示例。`git diff --check`、现有密钥扫描及 OpenSpec strict validate 均通过。本地未执行生产命令或重复运行代码测试。

交付记录：文档提交 `4b939c3` 已快进同步到本地项目与 GitHub main；[GitHub Actions 34128860835](https://github.com/UMRzcz-831/codex-socks-manager/actions/runs/34128860835) 通过。运行时、VPS 配置及 v0.1.0 标签未修改。
