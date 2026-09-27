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
    args = parser.parse_args()

    try:
        raw = read_html(args.html_file)
    except OSError as exc:
        print(f"无法读取 HTML: {exc}", file=sys.stderr)
        return 2

    decoded = html.unescape(raw)
    sources = IMG_RE.findall(raw)
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
        "local_reference_present": bool(LOCAL_RE.search(decoded)),
        "errors": errors,
        "passed": not errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
