#!/usr/bin/env python3
"""Render the real TUI using disposable profiles; never invoke real operations.

SVG is built in. Optional PNG export needs resvg-py and a local CJK font.
These preview-only dependencies are not installed with the manager.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from rich.cells import cell_len
from textual.widgets import DataTable, TabbedContent

from codex_socks_manager.operations import Manager
from codex_socks_manager.paths import Paths
from codex_socks_manager.tui import ManagerApp


class PreviewManager(Manager):
    def execute(self, *args, **kwargs):
        raise RuntimeError("Preview only: operations disabled")


def export(app: ManagerApp, target: Path, font: Path | None) -> None:
    svg = app.export_screenshot()
    # Rich 14.3's SVG textLength counts code points, not terminal cells. Correct
    # only the exported artifact; the running compositor and library stay intact.
    root = ET.fromstring(svg)
    for text in root.iter("{http://www.w3.org/2000/svg}text"):
        value = text.text or ""
        if value and "textLength" in text.attrib:
            text.set("textLength", str(float(text.get("textLength")) * cell_len(value) / len(value)))
    svg = ET.tostring(root, encoding="unicode")
    target.with_suffix(".svg").write_text(svg, encoding="utf-8")
    if font:
        import resvg_py
        target.with_suffix(".png").write_bytes(resvg_py.svg_to_bytes(
            svg_string=svg, font_files=[str(font)],
            font_dirs=["/usr/share/fonts/truetype/dejavu"], monospace_family="DejaVu Sans Mono"))


async def render(args) -> None:
    args.output.mkdir(parents=True, exist_ok=True)
    metrics = []
    for size in ((80, 24), (120, 36)):
        for lang in ("en", "zh-CN"):
            with tempfile.TemporaryDirectory(prefix="codex-socks-preview-") as directory:
                root = Path(directory)
                paths = Paths.discover({"HOME": str(root / "home"),
                                        "XDG_CONFIG_HOME": str(root / "config"),
                                        "XDG_STATE_HOME": str(root / "state")})
                manager = PreviewManager(paths)
                manager.store.add("office", "socks5://proxy.example:1080")
                manager.store.add("local", "http://127.0.0.1:8080")
                manager.store.add("backup", "https://backup.example:8443")
                manager.store.set_active("office")
                app = ManagerApp(paths, lang, manager=manager)
                async with app.run_test(size=size) as pilot:
                    await pilot.pause()
                    pages = app.query_one(TabbedContent)
                    for page in ("profiles", "diagnostics", "maintenance", "commands"):
                        pages.active = page + "-page"
                        await pilot.pause()
                        await pilot.wait_for_scheduled_animations()
                        assert pages.active == page + "-page", "Preview navigation returned to another page"
                        if page == "profiles":
                            app.query_one("#profiles", DataTable).move_cursor(row=1)
                            await pilot.pause()
                            primary = app.query_one("#profiles").region.width
                            detail = app.query_one("#profile-side").region.width
                            ratio = primary / (primary + detail) if size[0] >= 100 else None
                        export(app, args.output / f"{page}-{lang}-{size[0]}x{size[1]}", args.png_font)
                    pages.active = "profiles-page"
                    await pilot.pause()
                    for command in ("edit", "restore", "del"):
                        app.request_operation(command)
                        await pilot.pause()
                        export(app, args.output / f"{command}-{lang}-{size[0]}x{size[1]}", args.png_font)
                        await pilot.press("escape")
                        await pilot.pause()
                    app.set_status(("Failed: example operation. Recovery failed; review configuration.",
                                    "失败：示例操作未完成。回滚失败，请检查配置。"), True)
                    app.action_result()
                    await pilot.pause()
                    export(app, args.output / f"result-{lang}-{size[0]}x{size[1]}", args.png_font)
                    metrics.append({"size": size, "language": lang, "operations": "disabled",
                                    "profile_width_ratio": ratio})
    (args.output / "manifest.json").write_text(json.dumps(metrics, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--png-font", type=Path, help="Local CJK font; requires resvg-py for PNG export")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()
    if args.png_font and not args.png_font.is_file():
        parser.error("--png-font must name an existing local font")
    if args.no_color:
        os.environ["NO_COLOR"] = "1"
    else:
        os.environ.pop("NO_COLOR", None)
    asyncio.run(render(args))


if __name__ == "__main__":
    main()
