#!/usr/bin/env python3
"""Build a Raphael body, embedding local Markdown images as data URLs."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlparse


IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def strip_title_and_abstract(text: str) -> str:
    lines = text.splitlines()
    index = 0
    if lines and lines[0].startswith("# "):
        index = 1
        while index < len(lines) and not lines[index].strip():
            index += 1
    if index < len(lines) and lines[index].strip() == "> 公众号摘要":
        while index < len(lines) and (not lines[index].strip() or lines[index].lstrip().startswith(">")):
            index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    return "\n".join(lines[index:]).rstrip() + "\n"


def local_path(raw_url: str, article: Path) -> Path | None:
    url = raw_url.strip().strip("<>").split(maxsplit=1)[0]
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None
    path = Path(parsed.path)
    return path if path.is_absolute() else article.parent / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--transport-base",
        help="also create article-transport.md using this temporary CORS base URL",
    )
    args = parser.parse_args()

    article = args.article.resolve()
    if not article.is_file():
        print(f"文章不存在: {article}", file=sys.stderr)
        return 2
    body = strip_title_and_abstract(article.read_text(encoding="utf-8"))
    embedded = 0
    external = 0

    def embed(match: re.Match[str]) -> str:
        nonlocal embedded, external
        alt, raw_url = match.group(1), match.group(2)
        path = local_path(raw_url, article)
        if path is None:
            external += 1
            return match.group(0)
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"图片不存在: {path}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if not mime.startswith("image/"):
            raise ValueError(f"不是受支持的图片: {path}")
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        embedded += 1
        return f"![{alt}](data:{mime};base64,{data})"

    try:
        raphael = IMAGE_RE.sub(embed, body)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    output = args.output.resolve() if args.output else article.with_name("article-raphael.md")
    output.write_text(raphael, encoding="utf-8")
    result: dict[str, object] = {
        "output": str(output),
        "embedded_images": embedded,
        "external_images": external,
        "characters": len(raphael),
    }

    if args.transport_base:
        base = args.transport_base.rstrip("/")

        def transport(match: re.Match[str]) -> str:
            alt, raw_url = match.group(1), match.group(2)
            path = local_path(raw_url, article)
            if path is None:
                return match.group(0)
            try:
                relative = path.resolve().relative_to(article.parent)
            except ValueError as exc:
                raise ValueError(f"transport 图片必须位于文章目录内: {path}") from exc
            encoded = "/".join(quote(part) for part in relative.parts)
            return f"![{alt}]({base}/{encoded})"

        try:
            compact = IMAGE_RE.sub(transport, body)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        transport_path = output.with_name("article-transport.md")
        transport_path.write_text(compact, encoding="utf-8")
        result["transport"] = str(transport_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
