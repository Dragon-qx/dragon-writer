#!/usr/bin/env python3
"""规划并执行可恢复回滚：后续章进入归档，不直接删除。"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

from _contract import file_sha256, now_iso, safe_join
from snapshot_book import SNAPSHOT_VERSION, _manifest_hash, _snapshot_sources, verify_snapshot


def _snapshot_dir(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "snapshots", f"{chapter:04d}")


def plan_rollback(book_dir: str, chapter: int) -> dict:
    verified = verify_snapshot(book_dir, chapter)
    if not verified.get("ok"):
        return {"ok": False, "error": verified.get("error", "目标快照无效")}
    snap_dir = _snapshot_dir(book_dir, chapter)
    with open(os.path.join(snap_dir, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    if (manifest.get("snapshotVersion") != SNAPSHOT_VERSION
            or manifest.get("snapshotType") != "closed"
            or manifest.get("manifestSha256") != _manifest_hash(manifest)):
        return {"ok": False, "error": "回滚只接受当前协议且自哈希有效的 closed 快照"}
    later = []
    for root in (os.path.join(book_dir, "chapters"), os.path.join(book_dir, "story", "runtime")):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            match = re.match(r"^(?:chapter-)?(\d+)", name)
            path = os.path.join(root, name)
            if match and int(match.group(1)) > chapter and os.path.isfile(path):
                later.append(os.path.relpath(path, book_dir).replace(os.sep, "/"))
    return {
        "ok": True,
        "snapshot": f"{chapter:04d}",
        "restore_files": manifest["includedFiles"],
        "files_to_archive": later,
        "chapters_to_delete": [os.path.basename(path) for path in later if path.startswith("chapters/")],
    }


def _max_current_chapter(book_dir: str) -> int:
    numbers = []
    for root in (os.path.join(book_dir, "chapters"), os.path.join(book_dir, "story", "runtime")):
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            match = re.match(r"^(?:chapter-)?(\d+)", name)
            if match:
                numbers.append(int(match.group(1)))
    return max(numbers, default=0)


def _create_recovery(book_dir: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"recovery-{stamp}"
    target = safe_join(os.path.join(book_dir, "story", "snapshots"), name)
    counter = 1
    while os.path.exists(target):
        target = safe_join(os.path.join(book_dir, "story", "snapshots"), f"{name}-{counter}")
        counter += 1
    sources = []
    hashes = {}
    for rel in _snapshot_sources(book_dir, _max_current_chapter(book_dir)):
        src = safe_join(book_dir, rel)
        if os.path.isfile(src):
            sources.append(rel)
            hashes[rel] = file_sha256(src)
            dst = safe_join(target, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    manifest = {
        "snapshotVersion": SNAPSHOT_VERSION,
        "snapshotType": "recovery",
        "chapter": _max_current_chapter(book_dir),
        "createdAt": now_iso(),
        "includedFiles": sources,
        "fileHashes": hashes,
        "schemaVersion": "1.0.0",
    }
    manifest["manifestSha256"] = _manifest_hash(manifest)
    with open(os.path.join(target, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return os.path.basename(target)


def _restore_files(book_dir: str, snapshot_dir: str, files: list) -> list:
    restored = []
    for rel in files:
        src = safe_join(snapshot_dir, rel)
        if not os.path.isfile(src):
            raise ValueError(f"快照缺少待恢复文件：{rel}")
        dst = safe_join(book_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        temp = dst + ".rollback-tmp"
        shutil.copy2(src, temp)
        os.replace(temp, dst)
        restored.append(rel)
    return restored


def execute_rollback(book_dir: str, chapter: int, delete_chapters: bool = False,
                     create_recovery: bool = True) -> dict:
    plan = plan_rollback(book_dir, chapter)
    if not plan.get("ok"):
        return plan
    if not create_recovery:
        return {"ok": False, "error": "4.1 回滚必须创建 recovery snapshot"}
    recovery_name = _create_recovery(book_dir)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_root = safe_join(book_dir, "story", "rollback-archive", f"after-{chapter:04d}-{stamp}")
    archived = []
    for rel in plan["files_to_archive"]:
        src = safe_join(book_dir, rel)
        if os.path.isfile(src):
            dst = safe_join(archive_root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.replace(src, dst)
            archived.append(rel)
    restored = _restore_files(book_dir, _snapshot_dir(book_dir, chapter), plan["restore_files"])
    from validate_book import validate
    validation = validate(book_dir)
    if validation.errors:
        recovery_dir = safe_join(book_dir, "story", "snapshots", recovery_name)
        with open(os.path.join(recovery_dir, "manifest.json"), encoding="utf-8") as handle:
            recovery = json.load(handle)
        _restore_files(book_dir, recovery_dir, recovery["includedFiles"])
        return {
            "ok": False,
            "error": "回滚后验证失败，已用 recovery snapshot 恢复",
            "validation_errors": validation.errors,
            "recovery_snapshot": recovery_name,
        }
    return {
        "ok": True,
        "snapshot": plan["snapshot"],
        "recovery_snapshot": recovery_name,
        "archive_dir": os.path.relpath(archive_root, book_dir).replace(os.sep, "/"),
        "restored_files": restored,
        "archived_files": archived,
        "deleted_chapters": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="回滚书籍到指定章节；默认只展示计划")
    parser.add_argument("book_dir")
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = execute_rollback(args.book_dir, args.chapter) if args.execute else plan_rollback(args.book_dir, args.chapter)
    if not args.execute:
        result["dry_run"] = True
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get("ok"):
        print("[OK] " + ("回滚完成" if args.execute else "回滚计划验证通过"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[FAIL] {result.get('error', '未知错误')}", file=sys.stderr)
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
