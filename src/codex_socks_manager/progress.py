from __future__ import annotations

from typing import Callable

Progress = Callable[[str], None]


def emit(callback: Progress | None, stage: str) -> None:
    if callback is not None:
        try:
            callback(stage)
        except Exception:
            # A disconnected UI must not change a transaction's outcome.
            pass


STAGES = {
    "working": ("Working…", "执行中…"),
    "selecting": ("Selecting profile…", "选择代理中…"),
    "restarting": ("Restarting app-server…", "重启 app-server 中…"),
    "validating": ("Validating with Doctor…", "Doctor 验收中…"),
    "snapshot": ("Creating recovery snapshot…", "创建恢复快照中…"),
    "restoring": ("Restoring the proxy layer…", "恢复代理层中…"),
    "updating": ("Updating Codex…", "更新 Codex 中…"),
    "launcher": ("Repairing launcher…", "修复 launcher 中…"),
    "rollback": ("Operation failed; recovering previous state…", "操作失败，正在恢复上一状态…"),
    "rolled_back": ("Previous proxy state restored.", "已恢复上一代理状态。"),
    "rollback_failed": ("Recovery failed; manual recovery is required.", "回滚失败，需要手动恢复。"),
    "complete": ("Completed.", "已完成。"),
}
