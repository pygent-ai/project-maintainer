#!/usr/bin/env python3
"""Compute stable source fingerprints for project-maintainer symbols."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def normalize_hash(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    text = str(value)
    return text if text.startswith("sha256:") else f"sha256:{text}"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _python_node(tree: ast.Module, record: dict[str, Any]) -> ast.AST | None:
    kind = record.get("kind")
    name = record.get("name")
    class_name = record.get("class")
    for node in tree.body:
        if kind == "function" and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
        if kind == "class" and isinstance(node, ast.ClassDef) and node.name == name:
            return node
        if kind == "method" and isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == name:
                    return child
    return None


def _python_fingerprint(path: Path, text: str, record: dict[str, Any]) -> tuple[str, str] | None:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return None
    node = _python_node(tree, record)
    if node is None:
        return None
    normalized = ast.dump(node, annotate_fields=True, include_attributes=False)
    return sha256_bytes(normalized.encode("utf-8")), "python_ast_semantic"


def _source_range_fingerprint(text: str, record: dict[str, Any]) -> tuple[str, str] | None:
    line = record.get("line")
    end_line = record.get("end_line")
    if not isinstance(line, int) or not isinstance(end_line, int) or line < 1 or end_line < line:
        return None
    lines = text.splitlines(keepends=True)
    if end_line > len(lines):
        return None
    return sha256_bytes("".join(lines[line - 1 : end_line]).encode("utf-8")), "source_range"


def symbol_fingerprint(path: Path, record: dict[str, Any], text: str | None = None) -> tuple[str, str]:
    """Return a symbol-level hash and the strategy used to compute it.

    Python symbols use a location-independent semantic AST hash. Other languages
    use a source-range hash when a reliable range is available and otherwise
    conservatively fall back to the whole-file hash.
    """

    if text is None:
        text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".py":
        result = _python_fingerprint(path, text, record)
        if result is not None:
            return result
        return file_hash(path), "file_fallback"
    result = _source_range_fingerprint(text, record)
    if result is not None:
        return result
    return file_hash(path), "file_fallback"
