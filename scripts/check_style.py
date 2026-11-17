#!/usr/bin/env python3
"""Check hard style rules used by this WeChat writing workflow."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = [
    ("破折号", re.compile(r"—|–")),
    ("固定翻案句", re.compile(r"不是.{0,40}而是|并非.{0,40}而是|不在于.{0,40}而在于|你以为.{0,40}其实|看似.{0,40}实则")),
    ("洞察路标", re.compile(r"先说结论|说到底|真正的问题|本质上|值得注意的是|从某种意义上说")),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article", type=Path)
    args = parser.parse_args()
    text = args.article.read_text(encoding="utf-8")
    findings: list[dict[str, object]] = []
    in_fence = False

    for line_number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            continue
        scrubbed = re.sub(r"https?://\S+", "", raw)
        scrubbed = re.sub(r"`[^`]*`", "", scrubbed)
        if "：" in scrubbed or re.search(r"(?<!https)(?<!http):", scrubbed):
            findings.append({"line": line_number, "rule": "冒号需人工确认仅用于直接引语", "text": raw})
        for name, pattern in PATTERNS:
            if pattern.search(scrubbed):
                findings.append({"line": line_number, "rule": name, "text": raw})

    result = {"article": str(args.article.resolve()), "findings": findings, "passed": not findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
