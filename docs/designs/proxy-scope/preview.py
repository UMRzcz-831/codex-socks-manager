"""Render and exercise the offline scope prototype with Textual Pilot."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from rich.cells import cell_len
from textual.widgets import Checkbox, DataTable, Input, Select, Static

from prototype import DEMO_HOST, ScopePrototype


def export(app: ScopePrototype, target: Path, font: Path | None) -> None:
    root = ET.fromstring(app.export_screenshot())
    for element in root.iter("{http://www.w3.org/2000/svg}text"):
        value = element.text or ""
        if value and "textLength" in element.attrib:
            element.set("textLength", str(float(element.get("textLength")) * cell_len(value) / len(value)))
    svg = "\n".join(line.rstrip() for line in ET.tostring(root, encoding="unicode").splitlines()) + "\n"
    target.with_suffix(".svg").write_text(svg, encoding="utf-8")
    if font:
        import resvg_py
        target.with_suffix(".png").write_bytes(resvg_py.svg_to_bytes(
            svg_string=svg, font_files=[str(font)],
            font_dirs=["/usr/share/fonts/truetype/dejavu"], monospace_family="DejaVu Sans Mono"))


def result_text(app: ScopePrototype) -> str:
    return str(app.query_one("#route", Static).render())


async def render(output: Path, font: Path | None) -> None:
    output.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix="scope-design-") as directory:
        # Isolate any incidental framework state; the prototype has no profile reader.
        os.environ.update({key: str(Path(directory) / key) for key in (
            "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME")})
        for size in ((120, 36), (80, 24)):
            app = ScopePrototype(no_color=False)
            async with app.run_test(size=size) as pilot:
                await pilot.pause()
                suffix = f"{size[0]}x{size[1]}"
                assert app.query_one("#vars", DataTable).row_count == 4
                assert "预计绕过代理" in result_text(app)
                assert app.query_one("#route").region.bottom <= app.query_one("#status").region.y
                export(app, output / f"claude-bypass-{suffix}", font)
                main, side = app.query_one("#main").region, app.query_one("#side").region
                if size[0] >= 100:
                    ratio = main.width / (main.width + side.width)
                    assert abs(ratio - 0.65) < 0.065
                    assert side.x >= main.right
                else:
                    ratio = None
                    assert side.y >= main.bottom
                    assert main.right <= size[0] and side.right <= size[0]
                await pilot.press("f7")
                await pilot.pause()
                assert "预计使用代理" in result_text(app)
                if size[0] >= 100:
                    export(app, output / f"claude-proxy-{suffix}", font)
                await pilot.press("f7", "f6")
                await pilot.pause()
                assert app.client == "codex"
                assert not app.query_one("#bypass", Checkbox).value
                assert "预计使用代理" in result_text(app)
                await pilot.press("f6")
                await pilot.pause()
                assert app.query_one("#bypass", Checkbox).value
                assert "预计绕过代理" in result_text(app)
                app.query_one("#scene", Select).value = "conflict"
                await pilot.pause()
                assert "无法确定" in result_text(app)
                if size[0] >= 100:
                    export(app, output / f"claude-conflict-{suffix}", font)
                app.query_one("#scene", Select).value = "socks"
                await pilot.pause()
                assert "阻止受管启动" in result_text(app)
                if size[0] >= 100:
                    export(app, output / f"claude-socks-{suffix}", font)
                await pilot.press("f6", "f7")
                await pilot.pause()
                app.query_one("#target", Input).value = "https://api.provider.example"
                await pilot.pause()
                assert "采用待检查" in result_text(app)
                if size[0] >= 100:
                    export(app, output / f"codex-socks-{suffix}", font)
                app.query_one("#scene", Select).value = "off"
                await pilot.pause()
                assert "启动环境无代理变量" in result_text(app)
                assert app.query_one("#bypass", Checkbox).disabled
                app.query_one("#scene", Select).value = "inherit"
                await pilot.pause()
                assert all(row.launch == "原样继承" for row in app.rows[:3])
                assert app.query_one("#bypass", Checkbox).disabled
                app.query_one("#target", Input).value = "invalid"
                await pilot.pause()
                assert "输入无效" in result_text(app)
                app.query_one("#target", Input).value = f"https://{DEMO_HOST}"
                app.query_one("#scene", Select).value = "managed"
                app.query_one("#client", Select).value = "claude"
                await pilot.pause()
                # Resize repeatedly, then verify all four rows and the route survive.
                await pilot.resize_terminal(80, 24)
                await pilot.pause()
                await pilot.resize_terminal(120, 36)
                await pilot.pause()
                await pilot.resize_terminal(*size)
                await pilot.pause()
                assert app.query_one("#vars", DataTable).row_count == 4
                assert "预计绕过代理" in result_text(app)
                # Keyboard traversal reaches the scenario and target inputs.
                focus_seen = set()
                for _ in range(12):
                    await pilot.press("tab")
                    if app.focused:
                        focus_seen.add(app.focused.id)
                assert {"client", "scene", "vars", "target", "bypass"} <= focus_seen
                await pilot.press("f2")
                await pilot.pause()
                assert app.focused.id == "selected"
                app.query_one("#side").scroll_visible(animate=False, force=True)
                await pilot.pause()
                visible = app.query_one("#side").region.intersection(app.query_one("#body").region)
                assert visible.height > 0
                if size[0] < 100:
                    export(app, output / f"claude-details-{suffix}", font)
                records.append({"size": size, "wide_ratio": ratio, "scenario_checks": "passed",
                                "client_rules_isolated": True, "resize": "passed", "keyboard": "passed",
                                "real_configuration": "not read", "network": "not used"})
        app = ScopePrototype(no_color=True)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert app.no_color
            assert "预计绕过代理" in result_text(app)
            await pilot.press("f7")
            await pilot.pause()
            assert "预计使用代理" in result_text(app)
            export(app, output / "claude-no-color-80x24", font)
            records.append({"size": [80, 24], "no_color": True, "toggle": "passed"})
    (output / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--png-font", type=Path)
    args = parser.parse_args()
    if args.png_font and not args.png_font.is_file():
        parser.error("--png-font must name a readable local font")
    asyncio.run(render(args.output, args.png_font))
