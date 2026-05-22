"""Data contracts for legacy instruction normalization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryRecord:
    path: str
    surface_id: str
    surface_display: str
    owner: str
    surface_kind: str
    registry_role: str
    role: str
    generated_marker: bool
    scaffold_marker: bool
    size_bytes: int
    sha256: str
    matched_pattern: str
    reason: str
    can_scan_legacy: bool
    can_generate: bool
    parser_hint: str


@dataclass(frozen=True)
class ExtractedRule:
    text: str
    topic: str
    scope: str
    glob: str | None
    kind: str
    confidence: str
    sources: list[str]
    source_quote: str


@dataclass(frozen=True)
class DiscardedRule:
    text: str
    reason: str
    source_quote: str


@dataclass(frozen=True)
class ClassificationResult:
    source_path: str
    surface_id: str
    owner: str
    surface_kind: str
    source_sha256: str
    runtime: str
    status: str
    durable_rules: list[ExtractedRule]
    discarded: list[DiscardedRule]
    conflicts: list[str]
    notes: list[str]


@dataclass(frozen=True)
class ClassificationTask:
    source_path: str
    surface_id: str
    surface_display: str
    owner: str
    surface_kind: str
    source_sha256: str
    parser_hint: str
    content: str
    instructions: list[str]
    output_contract: dict[str, object]


@dataclass(frozen=True)
class MergedRule:
    text: str
    topic: str
    scope: str
    glob: str | None
    kind: str
    confidence: str
    sources: list[str]
    source_quotes: list[str]


@dataclass(frozen=True)
class MergeProposal:
    run_id: str
    status: str
    merged_rules: list[MergedRule]
    discarded: list[DiscardedRule]
    conflicts: list[str]
    notes: list[str]


@dataclass(frozen=True)
class ProposedFile:
    path: str
    topic: str
    scope: str
    rule_count: int
    sources: list[str]


@dataclass(frozen=True)
class AppliedFile:
    path: str
    action: str
    backup_path: str | None
