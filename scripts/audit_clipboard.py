#!/usr/bin/env python3
"""Audit exported clipboard HTML for article identity and image portability."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


IMG_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)", re.I)
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I)
ALT_RE = re.compile(r"\balt=[\"']([^\"']*)", re.I)
ARTICLE_RE = re.compile(r"<article\b[^>]*\bid=[\"']article[\"'][^>]*>(.*?)</article>", re.I | re.S)
LOCAL_RE = re.compile(r"(?:localhost|127\.0\.0\.1|file://|/Users/|/home/|[A-Za-z]:\\)", re.I)


def read_html(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html_file", help="UTF-8 HTML file or - for stdin")
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--previous-fingerprint")
    parser.add_argument("--expected-images", type=int, required=True)
    parser.add_argument("--cover-position", choices=("start", "end", "any"), default="any")
    args = parser.parse_args()

    try:
        raw = read_html(args.html_file)
    except OSError as exc:
        print(f"无法读取 HTML: {exc}", file=sys.stderr)
        return 2

    decoded = html.unescape(raw)
    sources = IMG_RE.findall(raw)
    image_tags = IMG_TAG_RE.findall(raw)
    article_match = ARTICLE_RE.search(raw)
    article_html = article_match.group(1) if article_match else raw
    data_images = sum(src.startswith("data:image/") for src in sources)
    https_images = sum(src.startswith("https://") for src in sources)
    bad_sources = [src for src in sources if not (src.startswith("data:image/") or src.startswith("https://"))]
    errors: list[str] = []

    if args.fingerprint not in decoded:
        errors.append("缺少当前文章指纹")
    if args.previous_fingerprint and args.previous_fingerprint in decoded:
        errors.append("仍包含上一篇文章指纹")
    if len(sources) != args.expected_images:
        errors.append(f"图片数量 {len(sources)} 与预期 {args.expected_images} 不一致")
    if LOCAL_RE.search(decoded):
        errors.append("HTML 含本地服务器地址或本机路径")
    if bad_sources:
        errors.append(f"存在不可交付的图片地址 {len(bad_sources)} 个")
    if re.search(r"<h1\b", article_html, re.I):
        errors.append("可复制正文仍包含 H1 标题")
    if "公众号摘要" in html.unescape(article_html):
        errors.append("可复制正文仍包含公众号摘要")

    cover_indexes: list[int] = []
    for index, tag in enumerate(image_tags):
        alt_match = ALT_RE.search(tag)
        alt = html.unescape(alt_match.group(1)) if alt_match else ""
        if "封面" in alt or "cover" in alt.lower():
            cover_indexes.append(index)
    if args.cover_position != "any":
        if not cover_indexes:
            errors.append("HTML 没有识别到封面图片")
        elif args.cover_position == "start" and cover_indexes[0] != 0:
            errors.append("HTML 封面不是第一张图片")
        elif args.cover_position == "end" and cover_indexes[-1] != len(image_tags) - 1:
            errors.append("HTML 封面不是最后一张图片")

    result = {
        "html_length": len(raw),
        "fingerprint_present": args.fingerprint in decoded,
        "previous_fingerprint_present": bool(
            args.previous_fingerprint and args.previous_fingerprint in decoded
        ),
        "image_count": len(sources),
        "data_images": data_images,
        "https_images": https_images,
        "bad_image_sources": len(bad_sources),
        "cover_indexes": cover_indexes,
        "cover_position": args.cover_position,
        "article_h1_present": bool(re.search(r"<h1\b", article_html, re.I)),
        "article_abstract_present": "公众号摘要" in html.unescape(article_html),
        "local_reference_present": bool(LOCAL_RE.search(decoded)),
        "errors": errors,
        "passed": not errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
