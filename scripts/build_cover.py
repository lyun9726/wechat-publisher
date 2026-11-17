#!/usr/bin/env python3
"""Create a 900x383 text cover from a real background image."""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_chrome() -> str | None:
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def page(background: Path, headline: str, eyebrow: str, subtitle: str, accent: str) -> str:
    mime = mimetypes.guess_type(background.name)[0] or "image/png"
    data = base64.b64encode(background.read_bytes()).decode("ascii")
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}html,body{{margin:0;width:900px;height:383px;overflow:hidden}}body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#060b14}}.cover{{position:relative;width:900px;height:383px;background-image:linear-gradient(90deg,rgba(4,9,18,.98) 0%,rgba(4,9,18,.90) 48%,rgba(4,9,18,.28) 100%),url("data:{mime};base64,{data}");background-size:cover;background-position:center}}.cover:after{{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.38),transparent 55%);pointer-events:none}}.content{{position:absolute;z-index:2;left:54px;top:44px;width:600px}}.eyebrow{{display:inline-block;padding:7px 14px;border:1px solid {accent};border-radius:999px;color:{accent};font-size:16px;font-weight:700;letter-spacing:.04em}}h1{{margin:22px 0 0;color:#fff;font-size:52px;line-height:1.12;letter-spacing:-.03em;text-shadow:0 3px 18px rgba(0,0,0,.35)}}p{{margin:20px 0 0;color:#d7dfef;font-size:21px;font-weight:600;letter-spacing:.01em}}.mark{{position:absolute;z-index:2;right:34px;bottom:25px;padding:8px 14px;border-radius:10px;background:rgba(8,15,28,.74);border:1px solid rgba(255,255,255,.16);color:#cdd7ea;font-size:14px}}
</style></head><body><div class="cover"><div class="content"><span class="eyebrow">{html.escape(eyebrow)}</span><h1>{html.escape(headline)}</h1><p>{html.escape(subtitle)}</p></div><span class="mark">利云 · AI生产力</span></div></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("background", type=Path)
    parser.add_argument("--headline", required=True)
    parser.add_argument("--eyebrow", default="AI 工具实测")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--accent", default="#53f5a6")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--keep-html", action="store_true")
    args = parser.parse_args()

    background = args.background.resolve()
    if not background.is_file():
        print(f"背景图不存在: {background}", file=sys.stderr)
        return 2
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    html_output = output.with_suffix(".html")
    html_output.write_text(page(background, args.headline, args.eyebrow, args.subtitle, args.accent), encoding="utf-8")
    chrome = find_chrome()
    if chrome is None:
        print(f"未找到 Chrome。请用浏览器打开并按 900x383 截图: {html_output}")
        return 3
    with tempfile.TemporaryDirectory() as temp_dir:
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--user-data-dir={Path(temp_dir) / 'profile'}",
            "--window-size=900,383",
            f"--screenshot={output}",
            html_output.as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode != 0 or not output.is_file():
        print(result.stderr, file=sys.stderr)
        print(f"封面截图失败，可手动打开: {html_output}", file=sys.stderr)
        return 2
    if not args.keep_html:
        html_output.unlink(missing_ok=True)
    print(f"封面已生成: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
