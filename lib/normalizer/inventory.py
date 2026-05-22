"""Deterministic inventory of existing AI instruction surfaces."""

from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path
from typing import Iterable

from instruction_surfaces import (
    GENERATED_BLOCK_BEGIN,
    GENERATED_BLOCK_END,
    GENERATED_MARKERS,
    INSTRUCTION_SURFACES,
    SCAFFOLD_MARKERS,
    InstructionSurface,
)

from .artifacts import REPO_ROOT, repo_rel
from .models import InventoryRecord


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "target",
}

EXCLUDED_PREFIXES = (
    "omnigento/",
    "instruction-seed/",
    "logs/",
    "server_archives/",
)


def is_excluded(path: Path) -> bool:
    rel = repo_rel(path)
    if any(rel == prefix.rstrip("/") or rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return True
    return any(part in EXCLUDED_DIRS for part in path.relative_to(REPO_ROOT).parts)


def iter_pattern_matches(pattern: str) -> Iterable[Path]:
    try:
        matches = REPO_ROOT.glob(pattern)
    except ValueError as exc:
        raise ValueError(f"unsupported registry glob {pattern!r}: {exc}") from exc
    for path in matches:
        if not path.is_file() or is_excluded(path):
            continue
        yield path


def pattern_matches(path: Path, pattern: str) -> bool:
    rel = repo_rel(path)
    return fnmatch.fnmatchcase(rel, pattern)


def surface_accepts_path(surface: InstructionSurface, path: Path, pattern: str) -> bool:
    rel = repo_rel(path)
    if surface.id in {"agent-markdown-nested", "claude-nested-root"} and "/" not in rel:
        return False
    if surface.id == "agent-markdown-root" and rel != "AGENTS.md":
        return False
    if surface.id == "claude-root" and rel != "CLAUDE.md":
        return False
    return pattern_matches(path, pattern)


def classify_role(registry_role: str, generated_marker: bool, scaffold_marker: bool) -> str:
    if registry_role == "canonical":
        return "canonical"
    if scaffold_marker:
        return "scaffold"
    if generated_marker:
        return "generated_output"
    if registry_role == "generated_output":
        return "legacy_input"
    return registry_role


def role_priority(role: str) -> int:
    priorities = {
        "canonical": 0,
        "scaffold": 1,
        "generated_output": 2,
        "legacy_input": 3,
    }
    return priorities.get(role, 99)


def read_text_for_markers(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def contains_marker_outside_fence(text: str, marker: str) -> bool:
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            current = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = current
            elif current == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if not in_fence and line.strip() == marker:
            return True
    return False


def make_record(path: Path, surface: InstructionSurface, registry_role: str, pattern: str) -> InventoryRecord:
    data = path.read_bytes()
    text = read_text_for_markers(path)
    generated_marker = any(contains_marker_outside_fence(text, marker) for marker in GENERATED_MARKERS) or (
        contains_marker_outside_fence(text, GENERATED_BLOCK_BEGIN)
        and contains_marker_outside_fence(text, GENERATED_BLOCK_END)
    )
    scaffold_marker = any(contains_marker_outside_fence(text, marker) for marker in SCAFFOLD_MARKERS)
    role = classify_role(registry_role, generated_marker, scaffold_marker)
    effective_registry_role = "legacy_input" if registry_role == "generated_output" and role == "legacy_input" else registry_role
    reason = f"matched {pattern}"
    if generated_marker:
        reason += "; contains Omnigento generated marker"
    elif registry_role == "generated_output":
        reason += "; output path has no Omnigento generated signature"
    if scaffold_marker:
        reason += "; contains Omnigento scaffold marker"

    return InventoryRecord(
        path=repo_rel(path),
        surface_id=surface.id,
        surface_display=surface.display_name,
        owner=surface.owner,
        surface_kind=surface.surface_kind,
        registry_role=effective_registry_role,
        role=role,
        generated_marker=generated_marker,
        scaffold_marker=scaffold_marker,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        matched_pattern=pattern,
        reason=reason,
        can_scan_legacy=surface.can_scan_legacy,
        can_generate=surface.can_generate,
        parser_hint=surface.parser_hint,
    )


def inventory() -> list[InventoryRecord]:
    records_by_path: dict[Path, InventoryRecord] = {}
    for surface in INSTRUCTION_SURFACES:
        for pattern, registry_role in surface.scan_patterns:
            for path in iter_pattern_matches(pattern):
                if not surface_accepts_path(surface, path, pattern):
                    continue
                record = make_record(path, surface, registry_role, pattern)
                existing = records_by_path.get(path)
                if existing is None or role_priority(record.role) < role_priority(existing.role):
                    records_by_path[path] = record

    return sorted(records_by_path.values(), key=lambda record: record.path)
