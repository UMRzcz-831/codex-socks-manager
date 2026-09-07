## Context

见 [proposal.md](proposal.md)。现有 CLI 使用 Python 标准库，提供配置管理、Doctor 汇总及更新恢复；README 的能力描述必须以 `cli.py`、`runtime.py`、`doctor.py`、`recovery.py` 与安装脚本为准。

来源于 2026-09-07 核对：

- [OpenAI API 支持地区](https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories)：官方明确没有单独的不支持清单；未列出的地区不支持 API。
- Eric Provencher，[Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/status/2095991462416490862)，发布于 2026-09-04。用户给出的 article URL 使用了推文 ID；通过[公开镜像](https://api.fxtwitter.com/pvncher/status/2095991462416490862)取得作者原文，实际 Article ID 为 `2095989703967125509`。X 直连与 Jina 返回 403。

## Goals / Non-Goals

**Goals:** 让首次使用者能从任一语言文档理解用途、安装条件、命令与地区信息；让贡献者明确项目独有的安全约束和完成标准。

**Non-Goals:** 不调整 CLI 或生产配置，不添加模型专属强制流程，不把 API 地区列表当作所有 Codex 登录方式的完整政策。

## Decisions

1. 保持 `README.md` 为英文入口，中文使用 `README.zh-CN.md`，顶部互链；按功能同步而非逐字翻译。slogan 保留用户指定的精确小写文字，紧随适用范围说明。
2. 地区部分列出中国大陆、香港、澳门、俄罗斯、白俄罗斯、伊朗、朝鲜、古巴、委内瑞拉作为非完整示例。这些地点在当日官方列表中均未出现；保留日期和官方链接，不构造貌似官方的完整黑名单。乌克兰仅按官方“有部分例外”表述。
3. AGENTS.md 采用简短入口、按任务导航与验证指引，把文章观点改写为本项目可执行约定；不复制全文。除文章启发外，凭据保护、XDG 布局、重启影响和命令均从项目代码及用户要求推导。
4. 文档明确当前实现的限制：check 汇总 Doctor、403 分类是启发式结果，不等于任意 MCP 业务调用和文件权限均已验证；切换需要现有匹配的 app-server；restore 不自动恢复备份中的完整 Codex 配置，也不回退二进制。
5. 采用临时 Git checkout 编辑并静态验证，再快进同步本地项目和 GitHub。实际 VPS 代理链接及组件不进入编辑目录、示例或提交。

## Risks / Trade-offs

- 地区信息变化 → 标明日期、非完整示例与官方实时来源；双语同步维护。
- slogan 被误读为全面保证 → 首段限定为代理配置造成的连接问题，诊断部分解释账号和授权边界。
- 指令过密导致反复停顿 → 保留项目事实、必要红线与完成标准；按改动选择验证，沿用已有授权。
- 文档示例泄露凭据 → 只使用回环地址或保留测试域名，提交前运行现有密钥扫描；无需读取真实配置。
