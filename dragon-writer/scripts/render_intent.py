#!/usr/bin/env python3
"""从权威 chapter intent JSON 单向生成只读 Markdown 视图。"""

import argparse
import json
import os

from _contract import file_sha256
from _schema import validate_document


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def render(source: str, output: str) -> None:
    with open(source, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    errors = validate_document(data, "chapter-intent.schema.json")
    if errors:
        raise ValueError("intent JSON 无效：" + "; ".join(errors))
    digest = file_sha256(source)
    lines = [
        "<!-- GENERATED FILE: DO NOT EDIT",
        f"source: {os.path.basename(source)}",
        f"source_sha256: {digest}",
        "-->",
        f"# Chapter {data['chapter']} Intent",
        "",
        f"- dramatic_question: {data['dramaticQuestion']}",
        f"- pov: {data['pov']}",
        f"- planned_target_chars: {data.get('plannedTargetChars', 'book default')}",
        "",
        "## Time Architecture",
        "",
    ]
    for key, value in data["timeArchitecture"].items():
        if key != "segments":
            lines.append(f"- {key}: {value}")
    for segment in data["timeArchitecture"].get("segments", []):
        lines.append(
            f"- segment {_cell(segment['segmentId'])} [{_cell(segment['mode'])}] "
            f"order={segment['order']}: {_cell(segment['start'])} → {_cell(segment['end'])}; "
            f"purpose={_cell(segment['purpose'])}"
        )
    lines += ["", "## Knowledge Permissions", ""]
    for item in data["knowledgePermissions"]:
        lines.append(
            f"- {_cell(item['character'])}: known={_cell(', '.join(item['knownAtStart']) or 'none')}; "
            f"still_unknown={_cell(', '.join(item['stillUnknown']) or 'none')}"
        )
        for acquired in item["acquiredThisChapter"]:
            lines.append(
                f"  - acquire {_cell(acquired['fact'])} via {_cell(acquired['acquisitionMode'])} "
                f"({ _cell(acquired['eventId']) }): {_cell(acquired['evidencePlan'])}"
            )
    lines += ["", "## Relationship Permissions", ""]
    for item in data["relationshipPermissions"]:
        lines.append(
            f"- {_cell(item['pairId'])}: {_cell(item['stageAtStart'])}; "
            f"allowed={_cell(', '.join(item['allowedFamiliarity']))}; change={_cell(item['plannedChange'])}; "
            f"catalyst={_cell(item['catalystEventId'])}; aftermath={_cell(item['aftermath'])}"
        )
    lines += ["", "## Novelty Delta", "", _cell(data["noveltyDelta"])]
    if data.get("noveltyFingerprint"):
        lines += ["", "```json", json.dumps(data["noveltyFingerprint"], ensure_ascii=False, indent=2), "```"]
    lines += [
        "", "## Required Scene Beats", "",
        "| beat_id | mode | participants | time_segment | dramatic_function | goal_or_pressure | conflict_or_turn | required_result | time_space_anchor | description_obligation |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for beat in data["sceneBeats"]:
        values = [
            beat["beatId"], beat["mode"], ", ".join(beat.get("participants", [])),
            beat.get("timeSegmentId", ""), beat["dramaticFunction"], beat["goalOrPressure"],
            beat["conflictOrTurn"], beat["requiredResult"], beat["timeSpaceAnchor"],
            beat["descriptionObligation"],
        ]
        lines.append("| " + " | ".join(_cell(value) for value in values) + " |")
    lines += ["", "## Draft Evidence Map", "", "| beat_id | paragraph_refs | evidence_quote | status |", "| --- | --- | --- | --- |"]
    for item in data["evidence"]:
        lines.append(
            f"| {_cell(item['beatId'])} | P{item['paragraphStart']}-P{item['paragraphEnd']} | "
            f"{_cell(item['quote'])} | {_cell(item['status'])} |"
        )
    temp = output + ".tmp"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.replace(temp, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="从 intent JSON 生成 Markdown 视图")
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    render(args.source, args.output)


if __name__ == "__main__":
    main()
