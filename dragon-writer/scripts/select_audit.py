#!/usr/bin/env python3
"""select_audit — 根据叙事技法、章节标签和风险选择激活的审计维度。

输入 genre、chapter tags、fanfic mode、chapter length 和 risk flags。
输出激活维度、severity、激活原因、缺失输入和跳过原因。
题材只用于技法适配，不限制创作范围；未知或混合题材使用通用清单。
尽量只依赖 Python 标准库。
"""

import argparse
import json
import sys
from typing import Dict, List, Optional


# 技法适配矩阵（与 audit-dimensions.md 同步）
GENRE_MATRIX: Dict[str, dict] = {
    "仙侠": {
        "enabled": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 21, 22, 25, 26, 27, 32, 33, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {38: "critical", 39: "critical"},
        "activation_reason": "体裁默认 + 架空前提(12)",
    },
    "修真": {
        "enabled": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 21, 22, 25, 26, 27, 32, 33, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {38: "critical", 39: "critical"},
        "activation_reason": "体裁默认 + 架空前提(12)",
    },
    "升级流": {
        "enabled": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 21, 22, 25, 26, 27, 32, 33, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {38: "critical", 39: "critical"},
        "activation_reason": "体裁默认 + 架空前提(12)",
    },
    "现代": {
        "enabled": [1, 2, 3, 7, 8, 9, 10, 11, 13, 14, 16, 17, 18, 19, 21, 22, 25, 26, 27, 32, 33, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {39: "critical", 40: "critical", 41: "critical"},
        "activation_reason": "体裁默认",
    },
    "都市": {
        "enabled": [1, 2, 3, 7, 8, 9, 10, 11, 13, 14, 16, 17, 18, 19, 21, 22, 25, 26, 27, 32, 33, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {39: "critical", 40: "critical", 41: "critical"},
        "activation_reason": "体裁默认",
    },
    "日常": {
        "enabled": [1, 2, 3, 7, 8, 9, 10, 11, 13, 14, 16, 17, 18, 19, 21, 22, 25, 26, 27, 32, 33, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {39: "critical", 40: "critical", 41: "critical"},
        "activation_reason": "体裁默认",
    },
}

# 同人模式矩阵
FANFIC_MATRIX: Dict[str, dict] = {
    "canon": {
        "enabled": [1, 2, 3, 6, 7, 8, 9, 10, 16, 17, 19, 21, 22, 25, 26, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {1: "critical", 34: "critical", 35: "critical", 37: "critical"},
        "activation_reason": "同人 canon 模式",
    },
    "ooc": {
        "enabled": [1, 2, 3, 6, 7, 8, 9, 10, 16, 17, 19, 21, 22, 25, 26, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {1: "info", 34: "info", 35: "warning", 36: "warning", 37: "info", 40: "critical", 41: "critical"},
        "activation_reason": "同人 OOC 模式",
    },
    "cp": {
        "enabled": [1, 2, 3, 6, 7, 8, 9, 10, 16, 17, 19, 21, 22, 25, 26, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {1: "warning", 34: "warning", 35: "warning", 36: "critical", 37: "info"},
        "activation_reason": "同人 CP 模式",
    },
    "au": {
        "enabled": [1, 2, 3, 6, 7, 8, 9, 10, 16, 17, 19, 21, 22, 25, 26, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
        "severity_overrides": {1: "warning", 34: "critical", 35: "info", 36: "warning", 37: "info"},
        "activation_reason": "同人 AU 模式",
    },
}

# 始终激活的维度（题材无关）
ALWAYS_ENABLED = [9, 27, 32, 33, 42, 43]

DEFAULT_SEVERITIES = {
    2: "warning",
    3: "critical",
    9: "critical",
    27: "critical",
    42: "critical",
}

# 章节标签激活的维度
TAG_ACTIVATIONS = {
    "空间": [38],
    "战斗": [4, 38],
    "道具": [39],
    "感情": [36],
    "同人": [34, 35, 36, 37],
    "时代": [12],
    "穿越": [29],
    "重生": [29],
    "番外": [28, 29, 30, 31],
}

RISK_ACTIVATIONS = {
    "信息揭示": [9],
    "秘密": [9],
    "多视角": [9, 19],
    "关系跃迁": [27],
    "初识": [27],
    "长时间跨度": [2, 7, 17],
    "多时间线": [2, 19],
    "跨章重复": [42],
    "复盘": [9, 42],
}

# 维度名称映射
DIMENSION_NAMES = {
    1: "OOC 检查", 2: "叙事时间与章节切分", 3: "设定冲突", 4: "战力崩坏", 5: "数值检查",
    6: "伏笔检查", 7: "节奏检查", 8: "文风检查", 9: "信息获知链", 10: "词汇疲劳",
    11: "利益链断裂", 12: "年代考据", 13: "配角降智", 14: "配角工具人化",
    15: "爽点虚化", 16: "台词失真", 17: "流水账", 18: "知识库污染",
    19: "视角一致性", 20: "段落等长", 21: "套话密度", 22: "公式化转折",
    23: "列表式结构", 24: "支线停滞", 25: "弧线平坦", 26: "节奏单调",
    27: "关系熟悉度与权限", 28: "正传事件冲突", 29: "未来信息泄露", 30: "世界规则跨书一致性",
    31: "番外伏笔隔离", 32: "读者期待管理", 33: "章节备忘偏离", 34: "角色还原度",
    35: "世界规则遵守", 36: "关系动态", 37: "正典事件一致性", 38: "空间一致性",
    39: "道具追踪", 40: "服装外貌与随身物件", 41: "常识检查",
    42: "跨章重复检测", 43: "去 AI 味检查",
}

# 冷读者只判断正文症状。8/16/19 还需主代理对照风格、角色声音与 POV 契约；
# 42 还需主代理核对近章事实层，因此这些维度拆分执行。
COLD_READ_DIMENSIONS = {7, 8, 10, 13, 14, 16, 17, 19, 20, 21, 22, 23, 25, 26, 32, 43}
SHARED_DIMENSIONS = {8, 16, 19, 42}


def audit_executor(dimension: int) -> str:
    if dimension in SHARED_DIMENSIONS:
        return "split"
    if dimension in COLD_READ_DIMENSIONS:
        return "cold_reader"
    return "main_agent"


def select_audit(genre: str, chapter_tags: Optional[List[str]] = None,
                 fanfic_mode: Optional[str] = None, chapter_length: int = 3000,
                 risk_flags: Optional[List[str]] = None) -> dict:
    """选择激活的审计维度。"""
    chapter_tags = chapter_tags or []
    risk_flags = risk_flags or []

    # 确定基础清单
    if fanfic_mode and fanfic_mode in FANFIC_MATRIX:
        matrix = FANFIC_MATRIX[fanfic_mode]
        enabled = set(matrix["enabled"])
        severity_overrides = dict(matrix["severity_overrides"])
        activation_reasons = {d: matrix["activation_reason"] for d in enabled}
    elif genre in GENRE_MATRIX:
        matrix = GENRE_MATRIX[genre]
        enabled = set(matrix["enabled"])
        severity_overrides = dict(matrix["severity_overrides"])
        activation_reasons = {d: matrix["activation_reason"] for d in enabled}
    else:
        # 未知或混合题材使用通用清单，不限制创作范围
        enabled = set(ALWAYS_ENABLED + [1, 2, 3, 6, 7, 9])
        severity_overrides = {}
        activation_reasons = {d: "未知 / 混合题材通用策略" for d in enabled}

    # 始终激活
    for d in ALWAYS_ENABLED:
        if d not in enabled:
            enabled.add(d)
            activation_reasons[d] = "始终激活"

    # 章节标签激活
    for tag in chapter_tags:
        for d in TAG_ACTIVATIONS.get(tag, []):
            if d not in enabled:
                enabled.add(d)
                activation_reasons[d] = f"章节标签：{tag}"

    # 风险标记激活
    for flag in risk_flags:
        for d in RISK_ACTIVATIONS.get(flag, []):
            if d not in enabled:
                enabled.add(d)
                activation_reasons[d] = f"风险标记：{flag}"

    # 短篇裁剪
    skipped = {}
    if chapter_length < 3000:
        # 短篇可跳过 info 级维度
        for d in list(enabled):
            if d in (20, 23, 10, 21) and d not in ALWAYS_ENABLED:
                skipped[d] = "短篇（<3000 字）跳过 info 级"

    # 构建结果
    dimensions = []
    for d in sorted(enabled):
        if d in skipped:
            continue
        dimensions.append({
            "dimension": d,
            "name": DIMENSION_NAMES.get(d, f"维度 {d}"),
            "severity": severity_overrides.get(d, DEFAULT_SEVERITIES.get(d, "warning")),
            "activation_reason": activation_reasons.get(d, "默认激活"),
            "executor": audit_executor(d),
        })

    # 缺失输入
    missing_inputs = []
    if not genre:
        missing_inputs.append("genre（题材）")

    return {
        "genre": genre,
        "fanfic_mode": fanfic_mode,
        "chapter_tags": chapter_tags,
        "risk_flags": risk_flags,
        "chapter_length": chapter_length,
        "activated_count": len(dimensions),
        "dimensions": dimensions,
        "main_agent_dimensions": [
            item["dimension"] for item in dimensions if item["executor"] in ("main_agent", "split")
        ],
        "cold_read_dimensions": [
            item["dimension"] for item in dimensions if item["executor"] in ("cold_reader", "split")
        ],
        "skipped": [{"dimension": d, "name": DIMENSION_NAMES.get(d, f"维度 {d}"), "reason": r}
                     for d, r in skipped.items()],
        "missing_inputs": missing_inputs,
    }


def main():
    parser = argparse.ArgumentParser(description="选择激活的审计维度")
    parser.add_argument("--genre", default="", help="题材")
    parser.add_argument("--tags", nargs="*", default=[], help="章节标签")
    parser.add_argument("--fanfic-mode", choices=["canon", "ooc", "cp", "au"], help="同人模式")
    parser.add_argument("--chapter-length", type=int, default=3000, help="章节字数")
    parser.add_argument("--risk-flags", nargs="*", default=[], help="风险标记")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    result = select_audit(
        genre=args.genre,
        chapter_tags=args.tags,
        fanfic_mode=args.fanfic_mode,
        chapter_length=args.chapter_length,
        risk_flags=args.risk_flags,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"激活维度（共 {result['activated_count']} 维）：")
        for d in result["dimensions"]:
            print(
                f"  [{d['dimension']:2d}] {d['name']} ({d['severity']}, {d['executor']})"
                f" — {d['activation_reason']}"
            )
        if result.get("skipped"):
            print(f"\n跳过维度（{len(result['skipped'])} 维）：")
            for s in result["skipped"]:
                print(f"  [{s['dimension']:2d}] {s['name']} — {s['reason']}")
        if result.get("missing_inputs"):
            print(f"\n缺失输入：{', '.join(result['missing_inputs'])}")


if __name__ == "__main__":
    main()
