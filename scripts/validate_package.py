#!/usr/bin/env python3
"""Validate a Markdown article package before browser import."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article", type=Path)
    parser.add_argument("--min-images", type=int, default=0)
    parser.add_argument("--raphael", action="store_true")
    parser.add_argument("--allow-https", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    article = args.article.resolve()
    if not article.is_file():
        errors.append(f"文章不存在: {article}")
        text = ""
    else:
        text = article.read_text(encoding="utf-8")

    images = IMAGE_RE.findall(text)
    if len(images) < args.min_images:
        errors.append(f"图片数量 {len(images)} 少于要求的 {args.min_images}")
    if images:
        first_alt, first_url = images[0]
        first_name = Path(urlparse(first_url).path).name.lower()
        if "封面" not in first_alt and "cover" not in first_alt.lower() and "cover" not in first_name:
            errors.append("第一张图片没有被识别为封面")

    if args.raphael and text.lstrip().startswith("# "):
        errors.append("Raphael 正文仍包含 H1 标题")
    if args.raphael and "> 公众号摘要" in text:
        errors.append("Raphael 正文仍包含公众号摘要")

    for alt, raw_url in images:
        url = raw_url.strip().strip("<>").split(maxsplit=1)[0]
        parsed = urlparse(url)
        if not alt.strip():
            warnings.append(f"图片缺少替代文字: {url[:80]}")
        if parsed.scheme == "data":
            if not url.startswith("data:image/"):
                errors.append("data URL 不是图片")
            continue
        if parsed.scheme in {"http", "https"}:
            if parsed.hostname in LOCAL_HOSTS:
                errors.append(f"最终稿仍包含本地图片地址: {url}")
            elif parsed.scheme == "http":
                errors.append(f"图片不是 HTTPS: {url}")
            elif not args.allow_https:
                errors.append(f"外部图片尚未本地化: {url}")
            continue
        if parsed.scheme:
            errors.append(f"不支持的图片地址: {url}")
            continue
        path = Path(unquote(parsed.path))
        if not path.is_absolute():
            path = article.parent / path
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            errors.append(f"图片格式不支持: {path}")
        elif not path.is_file():
            errors.append(f"图片不存在: {path}")
        else:
            checked.append(str(path.resolve()))

    result = {
        "article": str(article),
        "image_count": len(images),
        "checked_files": checked,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
