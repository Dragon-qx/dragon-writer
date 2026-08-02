#!/usr/bin/env python3
"""rollback_book — 安全回滚书籍到指定章节的状态快照。

默认只输出影响范围（dry-run）。验证所有目标路径都位于当前书根目录。
回滚前创建恢复点。删除动作必须通过显式参数开启。
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone


SNAPSHOT_FILES = [
    "current_state.md",
    "pending_hooks.md",
    "chapter_summaries.md",
    "current_focus.md",
    "audit-drift.md",
    "chapters/index.json",
]

SNAPSHOT_REL_DIR = "story"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_join(base: str, *paths: str) -> str:
    target = os.path.normpath(os.path.join(base, *paths))
    if not target.startswith(os.path.normpath(base) + os.sep) and target != os.path.normpath(base):
        raise ValueError(f"路径越界：{paths}")
    return target


def next_snapshot_dir(book_dir: str) -> str:
    snapshots_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR, "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)
    existing = []
    for name in os.listdir(snapshots_dir):
        if os.path.isdir(os.path.join(snapshots_dir, name)):
            try:
                existing.append(int(name))
            except ValueError:
                pass
    next_num = (max(existing) + 1) if existing else 0
    return f"{next_num:04d}"


def plan_rollback(book_dir: str, chapter: int) -> dict:
    """规划回滚影响范围。"""
    snap_name = f"{chapter:04d}"
    snap_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR, "snapshots", snap_name)
    manifest_path = os.path.join(snap_dir, "manifest.json")

    if not os.path.isfile(manifest_path):
        return {"ok": False, "error": f"快照 {snap_name} 不存在"}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 恢复的文件
    restore_files = manifest.get("includedFiles", [])

    # 需要删除的后续章节
    chapters_dir = os.path.join(book_dir, "chapters")
    chapters_to_delete = []
    if os.path.isdir(chapters_dir):
        for name in sorted(os.listdir(chapters_dir)):
            if not name.endswith(".md"):
                continue
            import re
            m = re.match(r"^(\d+)", name)
            if m and int(m.group(1)) > chapter:
                chapters_to_delete.append(name)

    return {
        "ok": True,
        "snapshot": snap_name,
        "restore_files": restore_files,
        "chapters_to_delete": chapters_to_delete,
    }


def execute_rollback(book_dir: str, chapter: int, delete_chapters: bool = False,
                     create_recovery: bool = True) -> dict:
    """执行回滚。"""
    plan = plan_rollback(book_dir, chapter)
    if not plan["ok"]:
        return plan

    snap_name = plan["snapshot"]
    snap_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR, "snapshots", snap_name)
    src_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR)

    # 回滚前创建恢复点
    recovery_dir = None
    if create_recovery:
        recovery_name = next_snapshot_dir(book_dir)
        recovery_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR, "snapshots", recovery_name)
        os.makedirs(recovery_dir, exist_ok=True)
        for fpath in SNAPSHOT_FILES:
            src = os.path.join(src_dir, fpath)
            if os.path.isfile(src):
                dst = safe_join(recovery_dir, fpath)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

    # 恢复快照文件到工作区
    restored = []
    for fpath in plan["restore_files"]:
        src = safe_join(snap_dir, fpath)
        dst = safe_join(src_dir, fpath)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(fpath)

    # 删除后续章节（必须显式开启）
    deleted = []
    if delete_chapters and plan["chapters_to_delete"]:
        chapters_dir = os.path.join(book_dir, "chapters")
        for name in plan["chapters_to_delete"]:
            full = os.path.join(chapters_dir, name)
            if os.path.isfile(full):
                os.remove(full)
                deleted.append(name)
        # 重建 index
        index_path = os.path.join(chapters_dir, "index.json")
        if os.path.isfile(index_path):
            import re
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
            index["chapters"] = [e for e in index.get("chapters", [])
                                if not e.get("file", "") in deleted]
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
                f.write("\n")

    return {
        "ok": True,
        "snapshot": snap_name,
        "recovery_snapshot": recovery_name if create_recovery else None,
        "restored_files": restored,
        "deleted_chapters": deleted,
    }


def main():
    parser = argparse.ArgumentParser(description="回滚书籍到指定章节")
    parser.add_argument("book_dir", help="书籍根目录")
    parser.add_argument("--chapter", type=int, required=True, help="回滚到的章节编号")
    parser.add_argument("--delete-chapters", action="store_true",
                        help="删除后续章节（必须显式开启）")
    parser.add_argument("--no-recovery", action="store_true",
                        help="不创建恢复点（默认创建）")
    parser.add_argument("--execute", action="store_true",
                        help="执行回滚（默认仅输出影响范围）")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    if args.execute:
        result = execute_rollback(
            args.book_dir, args.chapter,
            delete_chapters=args.delete_chapters,
            create_recovery=not args.no_recovery,
        )
    else:
        result = plan_rollback(args.book_dir, args.chapter)
        result["dry_run"] = True

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result["ok"]:
            print(f"[FAIL] 失败：{result.get('error', '未知错误')}", file=sys.stderr)
            sys.exit(1)
        if result.get("dry_run"):
            print(f"回滚影响范围（dry-run）：")
            print(f"  恢复快照：{result['snapshot']}")
            print(f"  恢复文件：{', '.join(result['restore_files'])}")
            if result.get("chapters_to_delete"):
                print(f"  待删章节：{', '.join(result['chapters_to_delete'])}（需 --delete-chapters）")
            else:
                print(f"  无后续章节需删除")
        else:
            print(f"[OK] 回滚完成")
            print(f"  恢复快照：{result['snapshot']}")
            if result.get("recovery_snapshot"):
                print(f"  恢复点：{result['recovery_snapshot']}")
            print(f"  恢复文件：{', '.join(result['restored_files'])}")
            if result.get("deleted_chapters"):
                print(f"  删除章节：{', '.join(result['deleted_chapters'])}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
