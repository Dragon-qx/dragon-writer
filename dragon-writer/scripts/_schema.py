#!/usr/bin/env python3
"""Dragon Writer 使用的零依赖 JSON Schema 子集验证器。

Schema 文件保持 Draft 2020-12 格式。本模块只实现仓库 Schema 实际使用的
关键字；遇到未知关键字会忽略注解类字段，但不假装支持复杂条件逻辑。
"""

import json
import os
import re
from typing import Any, Dict, List


SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(SKILL_ROOT, "schemas")

SUPPORTED_KEYWORDS = {
    "$schema", "$id", "$ref", "$defs", "title", "description", "default", "examples",
    "type", "required", "properties", "additionalProperties", "const", "enum",
    "minLength", "pattern", "minimum", "items", "minItems", "uniqueItems",
}


def load_schema(name: str) -> dict:
    path = os.path.join(SCHEMA_DIR, name)
    with open(path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)
    _check_schema_keywords(schema)
    return schema


def _check_schema_keywords(node: Any, path: str = "$") -> None:
    """对未实现的约束 fail closed，避免 Schema 看似生效、实际被静默忽略。"""
    if not isinstance(node, dict):
        return
    unknown = sorted(set(node) - SUPPORTED_KEYWORDS)
    if unknown:
        raise ValueError(f"{path} 含校验器不支持的 JSON Schema 关键字：{', '.join(unknown)}")
    for key, value in node.get("properties", {}).items():
        _check_schema_keywords(value, f"{path}.properties.{key}")
    if isinstance(node.get("items"), dict):
        _check_schema_keywords(node["items"], f"{path}.items")
    for key, value in node.get("$defs", {}).items():
        _check_schema_keywords(value, f"{path}.$defs.{key}")


def _resolve_ref(root: dict, ref: str) -> dict:
    if not ref.startswith("#/"):
        raise ValueError(f"只支持本地 JSON Pointer $ref：{ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_instance(instance: Any, schema: dict, root: dict = None, path: str = "$") -> List[str]:
    root = root or schema
    if "$ref" in schema:
        return validate_instance(instance, _resolve_ref(root, schema["$ref"]), root, path)
    errors: List[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path} 必须等于 {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path} 必须是 {schema['enum']} 之一")
    expected_type = schema.get("type")
    if expected_type and not _type_ok(instance, expected_type):
        return [f"{path} 类型必须是 {expected_type}"]
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}.{key} 为必填字段")
        properties: Dict[str, dict] = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{path}.{key} 是未声明字段")
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate_instance(value, properties[key], root, f"{path}.{key}"))
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path} 至少需要 {schema['minItems']} 项")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in instance]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path} 不允许重复项")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(instance):
                errors.extend(validate_instance(item, item_schema, root, f"{path}[{index}]"))
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path} 长度不足")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path} 不符合格式 {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path} 不得小于 {schema['minimum']}")
    return errors


def validate_document(instance: Any, schema_name: str) -> List[str]:
    schema = load_schema(schema_name)
    return validate_instance(instance, schema, schema)
