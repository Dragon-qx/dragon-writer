#!/usr/bin/env python3
"""从磁盘为单章重建有限、可追溯的主代理工作包。"""

import argparse
import glob
import hashlib
import json
import os
import re

from _contract import chapter_length_limits, file_sha256


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _clip(text: str, limit: int, tail: bool = False) -> str:
    if len(text) <= limit:
        return text
    return ("…\n" + text[-limit:]) if tail else (text[:limit] + "\n…")


def build_work_packet(book_dir: str, chapter: int) -> tuple[str, dict]:
    runtime = os.path.join(book_dir, "story", "runtime")
    intent_path = os.path.join(runtime, f"chapter-{chapter:04d}.intent.json")
    if not os.path.isfile(intent_path):
        raise ValueError("缺少当前章 intent.json")
    intent = json.loads(_read(intent_path))
    if intent.get("chapter") != chapter:
        raise ValueError("intent 章号与工作包章号不一致")
    participants = sorted({
        character
        for beat in intent.get("sceneBeats", [])
        for character in beat.get("participants", [])
    })
    fact_ids = sorted({
        use.get("factId", "")
        for beat in intent.get("sceneBeats", [])
        for use in beat.get("knowledgeUses", [])
        if use.get("factId")
    })
    pair_ids = sorted({
        pair_id
        for beat in intent.get("sceneBeats", [])
        for pair_id in beat.get("relationshipRefs", [])
    })
    sources = [intent_path]
    parts = ["# 当前章主代理工作包", "", "> 由文件重建；不得传给无背景冷读子代理。", ""]
    book_path = os.path.join(book_dir, "book.json")
    book = json.loads(_read(book_path))
    sources.append(book_path)
    minimum, target, maximum = chapter_length_limits(book)
    parts += [f"## 交付契约\n\n- chapter: {chapter}\n- chars: min={minimum}, target={target}, max={maximum}"]
    parts += ["## 权威章节意图", "", "```json", json.dumps(intent, ensure_ascii=False, indent=2), "```"]

    previous = []
    for path in sorted(glob.glob(os.path.join(book_dir, "chapters", "*.md"))):
        match = re.match(r"^(\d+)_", os.path.basename(path))
        if match and int(match.group(1)) < chapter:
            previous.append(path)
    previous = previous[-2:]
    if previous:
        parts += ["## 最近正式章结尾"]
        for path in previous:
            sources.append(path)
            parts += [f"### {os.path.basename(path)}", _clip(_read(path), 1800, tail=True)]

    for rel, limit in (("story/current_focus.md", 3500), ("story/chapter_summaries.md", 4500), ("story/pending_hooks.md", 3500)):
        path = os.path.join(book_dir, rel)
        if os.path.isfile(path):
            sources.append(path)
            parts += [f"## {rel}", _clip(_read(path), limit, tail=("summaries" in rel))]

    state_path = os.path.join(book_dir, "story", "current_state.md")
    if os.path.isfile(state_path):
        sources.append(state_path)
        terms = set(participants + fact_ids + pair_ids)
        relevant = [line for line in _read(state_path).splitlines() if any(term and term in line for term in terms)]
        parts += ["## 本章相关状态", "\n".join(relevant) if relevant else "（未命中稳定 ID；须先补全账本引用）"]

    role_paths = glob.glob(os.path.join(book_dir, "story", "roles", "**", "*.md"), recursive=True)
    for path in sorted(role_paths):
        name = os.path.splitext(os.path.basename(path))[0]
        if name in participants:
            sources.append(path)
            parts += [f"## 角色：{name}", _clip(_read(path), 3000)]

    packet = "\n\n".join(parts).rstrip() + "\n"
    manifest_sources = [{
        "path": os.path.relpath(path, book_dir).replace(os.sep, "/"),
        "sha256": file_sha256(path),
    } for path in sources]
    manifest = {
        "schemaVersion": "4.1",
        "chapter": chapter,
        "participants": participants,
        "factIds": fact_ids,
        "pairIds": pair_ids,
        "sources": manifest_sources,
        "packetSha256": "sha256:" + hashlib.sha256(packet.encode("utf-8")).hexdigest(),
    }
    return packet, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="重建当前章主代理工作包")
    parser.add_argument("book_dir")
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    packet, manifest = build_work_packet(args.book_dir, args.chapter)
    runtime = os.path.join(args.book_dir, "story", "runtime")
    output = args.output or os.path.join(runtime, f"chapter-{args.chapter:04d}.work-packet.md")
    if not os.path.isabs(output):
        output = os.path.join(args.book_dir, output)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    temp = output + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write(packet)
    os.replace(temp, output)
    manifest_path = os.path.splitext(output)[0] + ".json"
    with open(manifest_path + ".tmp", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(manifest_path + ".tmp", manifest_path)
    print(json.dumps({"ok": True, "output": output, "manifest": manifest_path}, ensure_ascii=False))


if __name__ == "__main__":
    main()
