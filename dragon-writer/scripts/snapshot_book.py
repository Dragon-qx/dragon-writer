#!/usr/bin/env python3
"""snapshot_book - 创建书籍状态快照。

默认支持 dry-run。验证所有目标路径都位于当前书根目录。
禁止覆盖已有快照。支持验证快照哈希。快照文件清单来自 file-contract.json（_contract）。
"""

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sys

import _contract
from _contract import file_sha256, now_iso, safe_join

SNAPSHOT_VERSION = "2.0.0"


def _manifest_hash(manifest: dict) -> str:
    body = dict(manifest)
    body.pop("manifestSha256", None)
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _snapshot_sources(book_dir: str, chapter: int) -> list:
    result = list(_contract.resolve_snapshot_files(book_dir))
    for rel in ("book.json",):
        if rel not in result:
            result.append(rel)
    for path in glob.glob(os.path.join(book_dir, "chapters", "*.md")):
        match = re.match(r"^(\d+)_", os.path.basename(path))
        if match and int(match.group(1)) <= chapter:
            rel = os.path.relpath(path, book_dir).replace(os.sep, "/")
            if rel not in result:
                result.append(rel)
    runtime = os.path.join(book_dir, "story", "runtime")
    for path in glob.glob(os.path.join(runtime, "chapter-*")):
        match = re.match(r"^chapter-(\d+)", os.path.basename(path))
        if (match and int(match.group(1)) <= chapter and ".superseded-" not in path
                and ".work-packet." not in path and os.path.isfile(path)):
            rel = os.path.relpath(path, book_dir).replace(os.sep, "/")
            if rel not in result:
                result.append(rel)
    return sorted(result)


def create_snapshot(book_dir: str, chapter: int, dry_run: bool = False,
                    force: bool = False, snapshot_type: str = "closed") -> dict:
    """创建快照。"""
    snapshots_dir = os.path.join(book_dir, "story", "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)

    snap_name = f"{chapter:04d}" if snapshot_type == "closed" else f"{snapshot_type}-{chapter:04d}"
    snap_dir = safe_join(snapshots_dir, snap_name)

    if os.path.exists(snap_dir) and not force:
        return {
            "ok": False,
            "error": f"快照 {snap_name} 已存在，使用 --force 覆盖（禁止静默覆盖）",
        }

    # 收集文件（清单来自 _contract.resolve_snapshot_files(book_dir)，
    # 支持 story/roles/** glob；非通配路径缺失时计入 missing）
    included_files = []
    file_hashes = {}
    missing = []
    for fpath in _snapshot_sources(book_dir, chapter):
        src = os.path.join(book_dir, fpath)
        if os.path.isfile(src):
            included_files.append(fpath)
            file_hashes[fpath] = file_sha256(src)
        else:
            missing.append(fpath)

    manifest = {
        "snapshotVersion": SNAPSHOT_VERSION,
        "snapshotType": snapshot_type,
        "chapter": chapter,
        "createdAt": now_iso(),
        "includedFiles": included_files,
        "fileHashes": file_hashes,
        "skillVersion": _contract.skill_version(),
        "schemaVersion": "1.0.0",
    }
    manifest["manifestSha256"] = _manifest_hash(manifest)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "snapshot_dir": snap_name,
            "included_files": included_files,
            "missing_files": missing,
        }

    if os.path.isdir(snap_dir) and force:
        shutil.rmtree(snap_dir)
    # 创建快照目录，按书根相对路径保留结构（story/... 与 chapters/...）
    for fpath in included_files:
        src = os.path.join(book_dir, fpath)
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


def verify_snapshot(book_dir: str, chapter: int, compare_current: bool = False) -> dict:
    """验证快照完整性；封板时还要证明快照与当前工作区完全一致。"""
    snap_name = f"{chapter:04d}"
    snap_dir = os.path.join(book_dir, "story", "snapshots", snap_name)
    manifest_path = os.path.join(snap_dir, "manifest.json")

    if not os.path.isfile(manifest_path):
        return {"ok": False, "error": f"快照 {snap_name} 缺少 manifest.json"}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if manifest.get("chapter") != chapter:
        return {"ok": False, "error": "快照 manifest 章号与目录不一致"}
    included = manifest.get("includedFiles")
    hashes = manifest.get("fileHashes")
    if not isinstance(included, list) or not included or not isinstance(hashes, dict):
        return {"ok": False, "error": "快照 manifest 缺少非空 includedFiles/fileHashes"}
    if set(included) != set(hashes):
        return {"ok": False, "error": "快照 includedFiles 与 fileHashes 不一致"}
    if manifest.get("snapshotVersion") == SNAPSHOT_VERSION:
        if manifest.get("manifestSha256") != _manifest_hash(manifest):
            return {"ok": False, "error": "快照 manifest 自身哈希不匹配"}
    if compare_current:
        if manifest.get("snapshotVersion") != SNAPSHOT_VERSION or manifest.get("snapshotType") != "closed":
            return {"ok": False, "error": "封板必须使用当前协议的 closed 快照"}
        required = {"book.json", "chapters/index.json"}
        finals = [path for path in included if re.match(rf"^chapters/{chapter:04d}_.+\.md$", path)]
        if not required.issubset(set(included)) or len(finals) != 1:
            return {"ok": False, "error": "closed 快照缺少 book/index/本章唯一正式正文"}

    mismatches = []
    missing = []
    current_mismatches = []
    for fpath, expected_hash in manifest.get("fileHashes", {}).items():
        full = os.path.join(snap_dir, fpath)
        if not os.path.isfile(full):
            missing.append(fpath)
        else:
            actual = file_sha256(full)
            if actual != expected_hash:
                mismatches.append({"file": fpath, "expected": expected_hash, "actual": actual})
        if compare_current:
            current = safe_join(book_dir, fpath)
            if not os.path.isfile(current):
                current_mismatches.append({"file": fpath, "reason": "工作区文件缺失"})
            elif file_sha256(current) != expected_hash:
                current_mismatches.append({"file": fpath, "reason": "工作区文件已变化"})

    return {
        "ok": not mismatches and not missing and not current_mismatches,
        "snapshot_dir": snap_name,
        "mismatches": mismatches,
        "missing": missing,
        "current_mismatches": current_mismatches,
        "manifest_sha256": file_sha256(manifest_path),
    }


def main():
    parser = argparse.ArgumentParser(description="创建/验证书籍快照")
    parser.add_argument("book_dir", help="书籍根目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--dry-run", action="store_true", help="默认支持 dry-run")
    parser.add_argument("--force", action="store_true", help="强制覆盖已有快照")
    parser.add_argument("--type", choices=["prewrite", "closed", "recovery"], default="closed",
                        help="快照角色；封板只接受 closed")
    parser.add_argument("--verify", action="store_true", help="验证快照哈希而非创建")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    if args.verify:
        result = verify_snapshot(args.book_dir, args.chapter)
    else:
        result = create_snapshot(
            args.book_dir, args.chapter, dry_run=args.dry_run, force=args.force,
            snapshot_type=args.type,
        )

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
