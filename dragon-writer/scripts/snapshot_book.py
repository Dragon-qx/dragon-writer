#!/usr/bin/env python3
"""snapshot_book — 创建书籍状态快照。

默认支持 dry-run。验证所有目标路径都位于当前书根目录。
禁止覆盖已有快照。支持验证快照哈希。
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone


SNAPSHOT_VERSION = "1.0.0"

# 快照必须包含的文件
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


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def safe_join(base: str, *paths: str) -> str:
    """安全拼接路径，防止目录遍历。"""
    target = os.path.normpath(os.path.join(base, *paths))
    if not target.startswith(os.path.normpath(base) + os.sep) and target != os.path.normpath(base):
        raise ValueError(f"路径越界：{paths}")
    return target


def next_snapshot_dir(book_dir: str) -> str:
    """确定下一个快照目录编号。"""
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


def create_snapshot(book_dir: str, chapter: int, dry_run: bool = False,
                    force: bool = False) -> dict:
    """创建快照。"""
    # 验证所有目标路径都位于当前书根目录
    snapshots_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR, "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)

    snap_name = f"{chapter:04d}"
    snap_dir = safe_join(snapshots_dir, snap_name)

    if os.path.exists(snap_dir) and not force:
        return {
            "ok": False,
            "error": f"快照 {snap_name} 已存在，使用 --force 覆盖（禁止静默覆盖）",
        }

    # 收集文件
    src_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR)
    included_files = []
    file_hashes = {}
    missing = []

    for fpath in SNAPSHOT_FILES:
        src = os.path.join(src_dir, fpath)
        if os.path.isfile(src):
            included_files.append(fpath)
            file_hashes[fpath] = file_sha256(src)
        else:
            missing.append(fpath)

    manifest = {
        "snapshotVersion": SNAPSHOT_VERSION,
        "chapter": chapter,
        "createdAt": now_iso(),
        "includedFiles": included_files,
        "fileHashes": file_hashes,
        "skillVersion": "1.0.0",
        "schemaVersion": "1.0.0",
    }

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "snapshot_dir": snap_name,
            "included_files": included_files,
            "missing_files": missing,
        }

    # 创建快照目录
    os.makedirs(snap_dir, exist_ok=True)
    for fpath in included_files:
        src = os.path.join(src_dir, fpath)
        dst = safe_join(snap_dir, fpath)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    # 写 manifest
    with open(os.path.join(snap_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return {
        "ok": True,
        "snapshot_dir": snap_name,
        "included_files": included_files,
        "missing_files": missing,
    }


def verify_snapshot(book_dir: str, chapter: int) -> dict:
    """验证快照哈希。"""
    snap_name = f"{chapter:04d}"
    snap_dir = os.path.join(book_dir, SNAPSHOT_REL_DIR, "snapshots", snap_name)
    manifest_path = os.path.join(snap_dir, "manifest.json")

    if not os.path.isfile(manifest_path):
        return {"ok": False, "error": f"快照 {snap_name} 缺少 manifest.json"}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    mismatches = []
    missing = []
    for fpath, expected_hash in manifest.get("fileHashes", {}).items():
        full = os.path.join(snap_dir, fpath)
        if not os.path.isfile(full):
            missing.append(fpath)
        else:
            actual = file_sha256(full)
            if actual != expected_hash:
                mismatches.append({"file": fpath, "expected": expected_hash, "actual": actual})

    return {
        "ok": not mismatches and not missing,
        "snapshot_dir": snap_name,
        "mismatches": mismatches,
        "missing": missing,
    }


def main():
    parser = argparse.ArgumentParser(description="创建/验证书籍快照")
    parser.add_argument("book_dir", help="书籍根目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--dry-run", action="store_true", help="默认支持 dry-run")
    parser.add_argument("--force", action="store_true", help="强制覆盖已有快照")
    parser.add_argument("--verify", action="store_true", help="验证快照哈希而非创建")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    if args.verify:
        result = verify_snapshot(args.book_dir, args.chapter)
    else:
        result = create_snapshot(args.book_dir, args.chapter, dry_run=args.dry_run, force=args.force)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result["ok"]:
            print(f"[FAIL] 失败：{result.get('error', '未知错误')}", file=sys.stderr)
            sys.exit(1)
        if args.verify:
            print(f"[OK] 快照 {result['snapshot_dir']} 验证通过")
            for m in result.get("mismatches", []):
                print(f"  [哈希不匹配] {m['file']}")
            for m in result.get("missing", []):
                print(f"  [文件缺失] {m}")
        else:
            action = "（dry-run）" if result.get("dry_run") else ""
            print(f"[OK] 快照 {result['snapshot_dir']} 创建成功 {action}")
            print(f"  包含文件：{', '.join(result['included_files'])}")
            if result.get("missing_files"):
                print(f"  缺失文件：{', '.join(result['missing_files'])}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
