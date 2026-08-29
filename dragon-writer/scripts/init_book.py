#!/usr/bin/env python3
"""init_book — 创建新书的确定性脚本。

用法：
    python scripts/init_book.py --title "霜寒之纪" --genre 仙侠 --root ./books

生成 slug、创建目录、复制书籍骨架、写入时间戳和 schemaVersion、
注入 dashboard。第 0 章 closed 快照必须在基础文件填写完成后另行创建，
避免把空白占位模板误当成可回滚基线。避免覆盖已有书籍目录。
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

import _contract

SCHEMA_VERSION = "1.0.0"

# 书籍骨架目录（由仓库维护，直接复制，不让模型从 Markdown 重新拼装）
BOOK_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "book-template")
DASHBOARD_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "assets", "dashboard.html")


def slugify(title: str) -> str:
    """从书名生成 URL 安全的 slug。"""
    s = title.lower().strip()
    # 保留中文、字母、数字，其余替换为 -
    s = re.sub(r"[^\w一-鿿]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")


def create_book(title: str, genre: str, root: str, language: str = "zh",
                target_chapters: int = 200, chapter_word_count: int = 3000,
                chapter_min_chars: int = None, chapter_target_chars: int = None,
                chapter_max_chars: int = None) -> str:
    """创建新书，返回书目录路径。"""
    slug = slugify(title)
    book_dir = os.path.join(root, slug)

    # 避免覆盖已有书籍目录
    if os.path.exists(book_dir):
        print(f"错误：书籍目录已存在 {book_dir}，请使用其他书名或删除旧目录。", file=sys.stderr)
        sys.exit(1)

    # 创建目录结构
    dirs = [
        os.path.join(book_dir, "chapters"),
        os.path.join(book_dir, "story", "outline"),
        os.path.join(book_dir, "story", "roles", "major"),
        os.path.join(book_dir, "story", "roles", "minor"),
        os.path.join(book_dir, "story", "runtime"),
        os.path.join(book_dir, "story", "snapshots"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 写 book.json
    ts = now_iso()
    skill_ver = _contract.skill_version()
    if not skill_ver:
        print(
            "警告：无法读取 _meta.json 中的 skill 版本（skillVersion 将为空），"
            "请确认 skill 目录存在 _meta.json。",
            file=sys.stderr,
        )
    minimum = chapter_min_chars or chapter_word_count
    target = chapter_target_chars or chapter_word_count
    maximum = chapter_max_chars or max(target, round(target * 1.35))
    if not 0 < minimum <= target <= maximum:
        print(
            f"错误：章节长度必须满足 0 < min({minimum}) <= target({target}) <= max({maximum})。",
            file=sys.stderr,
        )
        sys.exit(1)

    book_json = {
        "id": slug,
        "title": title,
        "language": language,
        "genre": genre,
        "status": "outlining",
        "targetChapters": target_chapters,
        "chapterWordCount": chapter_word_count,
        "chapterMinChars": minimum,
        "chapterTargetChars": target,
        "chapterMaxChars": maximum,
        "chapterLengthGateFromChapter": 1,
        "createdAt": ts,
        "updatedAt": ts,
        "schemaVersion": SCHEMA_VERSION,
        "skillVersion": skill_ver,
    }
    write_json(os.path.join(book_dir, "book.json"), book_json)

    # 只复制空白结构模板；示例小说绝不能进入新项目。
    # 注意：跳过 book.json——本函数已在上面写入正确的 book.json
    # （含真实 id / slug / 版本 / 时间戳），不能被骨架占位版覆盖。
    if os.path.isdir(BOOK_TEMPLATE_DIR):
        for name in os.listdir(BOOK_TEMPLATE_DIR):
            if name == "book.json":
                continue
            src = os.path.join(BOOK_TEMPLATE_DIR, name)
            dst = os.path.join(book_dir, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

    # 注入 dashboard
    if os.path.isfile(DASHBOARD_TEMPLATE):
        shutil.copy2(DASHBOARD_TEMPLATE, os.path.join(book_dir, "dashboard.html"))

    print(f"已创建新书：{book_dir}")
    print(f"  slug: {slug}")
    print(f"  书名: {title}")
    print(f"  题材: {genre}")
    return book_dir


def main():
    parser = argparse.ArgumentParser(description="创建新书")
    parser.add_argument("--title", required=True, help="书名")
    parser.add_argument("--genre", default="通用", help="题材")
    parser.add_argument("--language", default="zh", help="语言代码")
    parser.add_argument("--target-chapters", type=int, default=200, help="目标章数")
    parser.add_argument("--chapter-word-count", type=int, default=3000, help="目标单章字数")
    parser.add_argument("--chapter-min-chars", type=int, help="单章去空白字符硬下限（默认等于目标）")
    parser.add_argument("--chapter-target-chars", type=int, help="单章规划字符数（默认等于目标）")
    parser.add_argument("--chapter-max-chars", type=int, help="单章去空白字符软上限（默认目标的 135%%）")
    parser.add_argument("--root", default="books", help="书籍根目录")
    args = parser.parse_args()

    create_book(
        title=args.title,
        genre=args.genre,
        root=args.root,
        language=args.language,
        target_chapters=args.target_chapters,
        chapter_word_count=args.chapter_word_count,
        chapter_min_chars=args.chapter_min_chars,
        chapter_target_chars=args.chapter_target_chars,
        chapter_max_chars=args.chapter_max_chars,
    )


if __name__ == "__main__":
    main()
