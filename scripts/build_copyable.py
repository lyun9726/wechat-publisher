#!/usr/bin/env python3
"""Build a standalone, image-embedded WeChat copy page from Markdown."""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


IMAGE_ONLY_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
STRONG_RE = re.compile(r"\*\*([^*]+)\*\*")
EM_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def inline_markup(text: str) -> str:
    codes: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        codes.append(html.escape(match.group(1)))
        return f"\x00CODE{len(codes) - 1}\x00"

    text = CODE_RE.sub(save_code, text)
    text = html.escape(text, quote=False)
    text = LINK_RE.sub(
        lambda m: (
            f'<a href="{html.escape(html.unescape(m.group(2)), quote=True)}" '
            f'style="color:#246bfe;text-decoration:none;">{m.group(1)}</a>'
        ),
        text,
    )
    text = STRONG_RE.sub(r"<strong>\1</strong>", text)
    text = EM_RE.sub(r"<em>\1</em>", text)
    for index, code in enumerate(codes):
        text = text.replace(
            f"\x00CODE{index}\x00",
            f'<code style="padding:2px 6px;border-radius:4px;background:#eef4ff;'
            f'color:#1769d2;font-size:.92em;">{code}</code>',
        )
    return text


def strip_frontmatter(lines: list[str]) -> tuple[str, list[str]]:
    title = "微信公众号文章"
    output: list[str] = []
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index < len(lines) and lines[index].startswith("# "):
        title = lines[index][2:].strip()
        index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index < len(lines) and lines[index].strip() == "> 公众号摘要":
        index += 1
        while index < len(lines) and (
            not lines[index].strip() or lines[index].lstrip().startswith(">")
        ):
            index += 1
    output.extend(lines[index:])
    return title, output


class Renderer:
    def __init__(self, article: Path, allow_https: bool) -> None:
        self.article = article
        self.allow_https = allow_https
        self.image_count = 0
        self.embedded_count = 0

    def image_source(self, raw: str) -> str:
        url = raw.strip().strip("<>").split(maxsplit=1)[0]
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"}:
            if self.allow_https and parsed.scheme == "https":
                return url
            raise ValueError(f"远程图片必须先下载到文章目录: {url}")
        if parsed.scheme:
            raise ValueError(f"不支持的图片地址: {url}")
        path = Path(parsed.path)
        if not path.is_absolute():
            path = self.article.parent / path
        path = path.resolve()
        if not path.is_file():
            raise ValueError(f"图片不存在: {path}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if not mime.startswith("image/"):
            raise ValueError(f"文件不是图片: {path}")
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        self.embedded_count += 1
        return f"data:{mime};base64,{payload}"

    def render_image(self, alt: str, raw: str) -> str:
        self.image_count += 1
        source = self.image_source(raw)
        safe_alt = html.escape(alt, quote=True)
        caption = (
            f'<figcaption style="margin-top:8px;text-align:center;color:#778197;'
            f'font-size:13px;line-height:1.6;">{html.escape(alt)}</figcaption>'
            if alt
            else ""
        )
        return (
            '<figure style="margin:24px 0 26px;">'
            f'<img src="{source}" alt="{safe_alt}" style="display:block;width:100%;'
            'height:auto;border-radius:8px;border:1px solid #e2e8f0;">'
            f"{caption}</figure>"
        )

    def render(self, lines: list[str]) -> str:
        blocks: list[str] = []
        index = 0
        while index < len(lines):
            raw = lines[index]
            line = raw.strip()
            if not line:
                index += 1
                continue
            if line.startswith("```"):
                language = line[3:].strip()
                index += 1
                code_lines: list[str] = []
                while index < len(lines) and not lines[index].strip().startswith("```"):
                    code_lines.append(lines[index])
                    index += 1
                index += 1 if index < len(lines) else 0
                code = html.escape("\n".join(code_lines))
                label = f' data-language="{html.escape(language, quote=True)}"' if language else ""
                blocks.append(
                    f'<pre{label} style="margin:18px 0;padding:16px;overflow:auto;border-radius:8px;'
                    f'background:#111827;color:#e5e7eb;font-size:14px;line-height:1.65;"><code>{code}</code></pre>'
                )
                continue
            image = IMAGE_ONLY_RE.match(line)
            if image:
                blocks.append(self.render_image(image.group(1), image.group(2)))
                index += 1
                continue
            if line.startswith("#### "):
                blocks.append(f'<h4 style="margin:24px 0 10px;font-size:18px;color:#243b63;">{inline_markup(line[5:])}</h4>')
                index += 1
                continue
            if line.startswith("### "):
                blocks.append(f'<h3 style="margin:28px 0 12px;font-size:20px;color:#20385f;">{inline_markup(line[4:])}</h3>')
                index += 1
                continue
            if line.startswith("## "):
                blocks.append(
                    f'<h2 style="margin:34px 0 14px;padding-left:12px;border-left:4px solid #246bfe;'
                    f'font-size:24px;line-height:1.45;color:#172d52;font-weight:800;">{inline_markup(line[3:])}</h2>'
                )
                index += 1
                continue
            if line in {"---", "***"}:
                blocks.append('<hr style="margin:30px 0;border:0;border-top:1px solid #e5e9f0;">')
                index += 1
                continue
            if line.startswith(">"):
                quote_lines: list[str] = []
                while index < len(lines) and lines[index].lstrip().startswith(">"):
                    quote_lines.append(lines[index].lstrip()[1:].lstrip())
                    index += 1
                blocks.append(
                    '<blockquote style="margin:20px 0;padding:14px 18px;border-left:4px solid #9db9ff;'
                    f'background:#f5f8ff;color:#52617a;line-height:1.8;">{inline_markup(" ".join(quote_lines))}</blockquote>'
                )
                continue
            if re.match(r"^[-*+]\s+", line):
                items: list[str] = []
                while index < len(lines) and re.match(r"^[-*+]\s+", lines[index].strip()):
                    items.append(re.sub(r"^[-*+]\s+", "", lines[index].strip()))
                    index += 1
                body = "".join(f'<li style="margin:8px 0;">{inline_markup(item)}</li>' for item in items)
                blocks.append(f'<ul style="margin:12px 0 20px;padding-left:24px;font-size:17px;line-height:1.8;color:#293245;">{body}</ul>')
                continue
            if re.match(r"^\d+[.)]\s+", line):
                items = []
                while index < len(lines) and re.match(r"^\d+[.)]\s+", lines[index].strip()):
                    items.append(re.sub(r"^\d+[.)]\s+", "", lines[index].strip()))
                    index += 1
                body = "".join(f'<li style="margin:8px 0;">{inline_markup(item)}</li>' for item in items)
                blocks.append(f'<ol style="margin:12px 0 20px;padding-left:26px;font-size:17px;line-height:1.8;color:#293245;">{body}</ol>')
                continue
            paragraph = [line]
            index += 1
            while index < len(lines) and lines[index].strip():
                candidate = lines[index].strip()
                if (
                    candidate.startswith(("#", ">", "```"))
                    or candidate in {"---", "***"}
                    or IMAGE_ONLY_RE.match(candidate)
                    or re.match(r"^[-*+]\s+", candidate)
                    or re.match(r"^\d+[.)]\s+", candidate)
                ):
                    break
                paragraph.append(candidate)
                index += 1
            text = " ".join(paragraph)
            if re.fullmatch(r"https?://\S+", text):
                safe = html.escape(text, quote=True)
                content = f'<a href="{safe}" style="color:#246bfe;text-decoration:none;word-break:break-all;">{html.escape(text)}</a>'
            else:
                content = inline_markup(text)
            blocks.append(f'<p style="margin:0 0 18px;font-size:17px;line-height:1.9;color:#293245;letter-spacing:.02em;">{content}</p>')
        return "\n".join(blocks)


def page(title: str, body: str) -> str:
    safe_title = html.escape(title)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe_title}</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fb;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:#293245}}.top{{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;padding:16px 22px;background:rgba(255,255,255,.96);border-bottom:1px solid #e2e7ef}}.top strong{{font-size:15px}}.actions{{display:flex;align-items:center;gap:12px}}.status{{font-size:13px;color:#6d7688}}.copy{{border:0;border-radius:999px;padding:11px 20px;background:#111827;color:#fff;font-size:15px;font-weight:700;cursor:pointer}}.wrap{{max-width:780px;margin:24px auto 60px;background:#fff;padding:38px 54px 58px;box-shadow:0 10px 34px rgba(25,46,89,.08)}}.page-title{{margin:0 0 28px;font-size:30px;line-height:1.35;color:#172d52}}article figure:last-child{{margin-top:36px;padding-top:28px;border-top:1px solid #e5e9f0}}@media(max-width:760px){{.wrap{{margin:0;padding:28px 20px 48px;box-shadow:none}}.page-title{{font-size:26px}}.status{{display:none}}}}</style></head>
<body><div class="top"><strong>带图可复制版</strong><div class="actions"><span class="status" id="status">图片已内嵌，可直接粘贴</span><button class="copy" id="copy">复制带图全文</button></div></div><main class="wrap"><h1 class="page-title">{safe_title}</h1><article id="article">{body}</article></main>
<script>const btn=document.getElementById('copy');const status=document.getElementById('status');btn.addEventListener('click',async()=>{{const node=document.getElementById('article');const rich=node.innerHTML;const plain=node.innerText;try{{await navigator.clipboard.write([new ClipboardItem({{'text/html':new Blob([rich],{{type:'text/html'}}),'text/plain':new Blob([plain],{{type:'text/plain'}})}})]);status.textContent='已复制，可直接粘贴到公众号后台';btn.textContent='复制成功';}}catch(e){{const range=document.createRange();range.selectNodeContents(node);const sel=getSelection();sel.removeAllRanges();sel.addRange(range);document.execCommand('copy');sel.removeAllRanges();status.textContent='已复制，可直接粘贴到公众号后台';btn.textContent='复制成功';}}}});</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-https", action="store_true")
    args = parser.parse_args()

    article = args.article.resolve()
    if not article.is_file():
        print(f"文章不存在: {article}", file=sys.stderr)
        return 2
    title, lines = strip_frontmatter(article.read_text(encoding="utf-8").splitlines())
    renderer = Renderer(article, args.allow_https)
    try:
        body = renderer.render(lines)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    output = args.output.resolve() if args.output else article.with_name("带图可复制版.html")
    output.write_text(page(title, body), encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "title": title,
        "images": renderer.image_count,
        "embedded_images": renderer.embedded_count,
        "html_bytes": output.stat().st_size,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
