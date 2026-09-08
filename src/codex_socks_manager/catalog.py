"""Shared, bilingual command documentation; no terminal or storage imports."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


def language(explicit: str | None = None, env: Mapping[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    selected = explicit or values.get("CODEX_SOCKS_LANG")
    if not selected:
        selected = next((values[key] for key in ("LC_ALL", "LC_MESSAGES", "LANG") if values.get(key)), "en")
    return "zh-CN" if selected.lower().startswith("zh") else "en"


def translated(lang: str, en: str, zh: str) -> str:
    return zh if lang == "zh-CN" else en


@dataclass(frozen=True)
class Command:
    name: str
    arguments: str
    summary: tuple[str, str]
    detail: tuple[str, str]
    examples: tuple[str, ...]
    parameters: tuple[tuple[str, str, str], ...] = ()

    def text(self, field: str, lang: str) -> str:
        return getattr(self, field)[lang == "zh-CN"]

    @property
    def usage(self) -> str:
        return f"{self.name} {self.arguments}".strip()


COMMANDS = (
    Command("add", "NAME [URL]", ("Save a named proxy profile.", "保存具名代理配置。"),
            ("Omit URL for a hidden prompt. Supports SOCKS5/SOCKS5h/HTTP/HTTPS; an explicit port is required. URLs in arguments may remain in shell history.",
             "不传 URL 时隐藏输入。支持 SOCKS5/SOCKS5h/HTTP/HTTPS，必须指定端口。命令参数中的 URL 可能留在 shell history。"),
            ("codex-socks add office", "codex-socks add local socks5://127.0.0.1:1080"),
            (("name", "Profile name (1–64 safe characters; not off).", "配置名（1–64 个安全字符，不能是 off）。"),
             ("url", "Proxy URL; omit for hidden input.", "代理 URL；省略后隐藏输入。"))),
    Command("use", "NAME", ("Switch, restart app-server and validate.", "切换代理，重启 app-server 并验收。"),
            ("Requires matching current-user app-server processes. May interrupt sessions. Failed validation restores the previous selection and attempts runtime recovery. Use off for direct connectivity.",
             "需要当前用户下匹配的 app-server，可能中断会话。验收失败恢复上一选择并尝试恢复运行环境。使用 off 切换直连。"),
            ("codex-socks use office", "codex-socks use off"),
            (("name", "Existing profile name, or off.", "已有配置名，或 off。"),)),
    Command("list", "[--json]", ("Show profiles and the active selection.", "查看配置与活动选择。"),
            ("Usernames and passwords are masked; hosts and ports remain visible. Review output before sharing. JSON is intended for scripts.",
             "用户名和密码脱敏，主机和端口仍然可见。分享前检查输出；脚本请使用 JSON。"),
            ("codex-socks list", "codex-socks list --json"),
            (("--json", "Output stable JSON without styling.", "输出不带样式的兼容 JSON。"),)),
    Command("edit", "NAME", ("Edit and validate an existing profile.", "编辑并校验已有配置。"),
            ("Uses $EDITOR and a 0600 temporary file. Saving does not restart or apply an active profile; run use afterwards.",
             "通过 $EDITOR 和 0600 临时文件编辑。保存不会重启或应用活动配置，之后需要执行 use。"),
            ("EDITOR=vi codex-socks edit office", "codex-socks use office"),
            (("name", "Existing profile name.", "已有配置名。"),)),
    Command("del", "NAME [--force]", ("Delete a profile with active-profile protection.", "删除配置，保护活动配置。"),
            ("An active profile requires --force: switch off, restart and validate before deleting. Failed direct-connect validation keeps the profile.",
             "删除活动配置必须传 --force：先关闭代理、重启并验收，再删除。直连验收失败保留配置。"),
            ("codex-socks del office", "codex-socks del office --force"),
            (("name", "Profile to delete.", "待删除配置。"), ("--force", "Switch off and validate before deleting an active profile.", "删除活动配置前关闭代理并验收。"))),
    Command("off", "", ("Disable managed proxies and validate direct access.", "关闭受管代理并验收直连。"),
            ("Restarts matching app-server roles and may interrupt sessions. If direct access fails validation, restores the previous selection.",
             "重启匹配的 app-server，可能中断会话。直连验收失败恢复上一选择。"),
            ("codex-socks off",)),
    Command("check", "", ("Summarize Codex Doctor diagnostics as JSON.", "以 JSON 汇总 Codex Doctor 诊断。"),
            ("Checks HTTPS, WSS, app-server and proxy environment. Requires doctor --json. Categories are hints, not proof of account, region or workspace access. Returns 1 if unhealthy.",
             "检查 HTTPS、WSS、app-server 和代理环境。要求支持 doctor --json。分类是线索，不能证明账号、地区或 workspace 访问权限。异常时返回 1。"),
            ("codex-socks check",)),
    Command("install", "", ("Find Codex and install or repair its launcher.", "发现 Codex，安装或修复 launcher。"),
            ("Supports standalone, npm and pnpm. Replaces the managed launcher; back up any custom launcher first.",
             "支持 standalone、npm 和 pnpm。会替换受管 launcher；自定义 launcher 请先备份。"),
            ("codex-socks install",)),
    Command("backup", "", ("Create a local known-good recovery snapshot.", "创建本地 known-good 恢复快照。"),
            ("Includes settings, profiles, launcher and Codex configuration when present. Snapshots contain plaintext credentials; keep them private. The label does not run a health check.",
             "备份设置、配置、launcher 及存在的 Codex 配置。快照含明文凭据，需私密保存；known-good 标签不代表已执行健康检查。"),
            ("codex-socks backup",)),
    Command("restore", "[SNAPSHOT]", ("Restore the proxy layer and restart app-server.", "恢复代理层并重启 app-server。"),
            ("Defaults to the latest known-good snapshot. Creates a pre-restore snapshot, retains the installed Codex binary, and does not restore Codex configuration automatically.",
             "默认使用最新 known-good 快照。先建立 pre-restore 快照，保留已安装的 Codex 二进制，不自动恢复 Codex 配置。"),
            ("codex-socks restore", "codex-socks restore /path/to/snapshot"),
            (("snapshot", "Snapshot directory; defaults to latest known-good.", "快照目录；默认最新 known-good。"),)),
    Command("safe-update", "", ("Snapshot, update Codex, repair and validate.", "创建快照、更新 Codex、修复并验收。"),
            ("Requires codex update. Restarts app-server and runs Doctor; on failure attempts snapshot recovery. Recovery does not downgrade Codex binaries.",
             "要求支持 codex update。重启 app-server 并运行 Doctor；失败时尝试快照恢复，恢复不降级 Codex 二进制。"),
            ("codex-socks safe-update", "codex-socks check")),
    Command("migrate-legacy", "[--jp PATH] [--us PATH]", ("Import legacy proxy files without sourcing shell.", "导入旧代理文件，不执行 shell 内容。"),
            ("With neither path, reads ~/.config/openai-proxy/jp.env and us.env. Identical imports are safe; conflicting profiles are rejected. Does not change the active selection.",
             "均省略时读取 ~/.config/openai-proxy/jp.env 和 us.env。相同内容可重复导入，冲突配置会被拒绝，不改变活动选择。"),
            ("codex-socks migrate-legacy", "codex-socks migrate-legacy --jp /path/to/jp.env --us /path/to/us.env"),
            (("--jp", "Legacy JP file path.", "旧 JP 文件路径。"), ("--us", "Legacy US file path.", "旧 US 文件路径。"))),
    Command("tui", "", ("Open the optional interactive manager.", "打开选装的交互管理界面。"),
            ("Requires an interactive terminal and optional UI dependencies. From the project directory: ./scripts/install.sh --with-tui; for pip use the same environment: python -m pip install '.[tui]'. Without UI dependencies, invoking with no command shows help. Language changes inside the UI last for this session.",
             "需要交互终端和选装依赖。在项目目录执行 ./scripts/install.sh --with-tui；pip 安装在同一环境执行 python -m pip install '.[tui]'。未装界面时无参数显示帮助。界面内切换语言仅影响本次会话。"),
            ("codex-socks tui", "codex-socks", "codex-socks tui --lang zh-CN")),
)
BY_NAME = {command.name: command for command in COMMANDS}
