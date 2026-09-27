#!/usr/bin/env python3
"""Create a non-destructive WeChat article package from bundled templates."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


def load_profile(path: Path | None) -> tuple[dict[str, object], Path | None]:
    candidate = path
    if candidate is None:
        local = Path.cwd() / "author-profile.json"
        candidate = local if local.is_file() else None
    if candidate is None:
        return {}, None
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取作者配置 {candidate}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("作者配置必须是 JSON 对象")
    return data, candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="lowercase article id, for example jev-guide")
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", type=Path, default=Path("runs"))
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()

    if not SLUG_RE.fullmatch(args.slug):
        print("slug 只能包含小写字母、数字和连字符，且长度不超过 63", file=sys.stderr)
        return 2

    target = (args.output / args.slug).resolve()
    if target.exists():
        print(f"目标目录已存在，未覆盖: {target}", file=sys.stderr)
        return 2

    try:
        profile, profile_path = load_profile(args.profile)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    assets = Path(__file__).resolve().parent.parent / "assets"
    target.mkdir(parents=True)
    (target / "images").mkdir()
    shutil.copyfile(assets / "article-brief.md", target / "brief.md")
    shutil.copyfile(assets / "image-plan.md", target / "image-plan.md")
    shutil.copyfile(assets / "delivery-check.md", target / "delivery-check.md")

    (target / "author-profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (target / "sources.md").write_text("# 关键来源\n\n", encoding="utf-8")

    opening = str(profile.get("opening", "")).strip()
    opening_block = f"{opening}\n\n" if opening else ""
    article = (
        f"# {args.title}\n\n"
        "> 公众号摘要\n>\n> 待填写\n\n"
        f"{opening_block}"
        "正文从这里开始。\n"
    )
    (target / "article.md").write_text(article, encoding="utf-8")

    result = {
        "created": str(target),
        "title": args.title,
        "profile_source": str(profile_path) if profile_path else None,
        "files": sorted(path.name for path in target.iterdir()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
