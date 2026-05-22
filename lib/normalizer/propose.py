"""Proposal rendering for canonical instruction files."""

from __future__ import annotations

import json
from dataclasses import asdict

from .artifacts import load_merged_rules, update_manifest, utc_now, write_json
from .models import MergedRule, ProposedFile


def topic_stem(value: str) -> str:
    stem = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    stem = "-".join(part for part in stem.split("-") if part)
    return stem or "migrated-instructions"


def normalized_scope(scope: str) -> str:
    value = scope.strip().lower().replace("_", "-")
    aliases = {
        "file": "file-scoped",
        "file-scoped-rule": "file-scoped",
        "path-scoped": "file-scoped",
        "topic": "topic-based",
        "topic-rule": "topic-based",
        "skill": "on-request",
        "onrequest": "on-request",
        "on-request-skill": "on-request",
        "root": "root-only",
        "root-only-rule": "root-only",
    }
    return aliases.get(value, value)


def quote_frontmatter(value: str) -> str:
    return json.dumps(value)


def title_from_stem(stem: str) -> str:
    return " ".join(part.capitalize() for part in stem.split("-") if part) or "Migrated Instructions"


def rule_section_name(kind: str) -> str:
    names = {
        "safety": "Safety",
        "workflow": "Workflow",
        "style": "Style",
        "command": "Commands",
        "commands": "Commands",
        "architecture": "Architecture",
        "config": "Config",
        "provider": "Provider Notes",
    }
    normalized = kind.strip().lower().replace("_", "-")
    return names.get(normalized, title_from_stem(normalized))


def description_for(topic: str, scope: str, rules: list[MergedRule]) -> str:
    kinds = sorted({rule_section_name(rule.kind).lower() for rule in rules})
    stem_title = title_from_stem(topic_stem(topic))
    if kinds:
        summary = ", ".join(kinds)
        return f"{stem_title}: migrated {summary} instructions from legacy AI provider files."
    return f"{stem_title}: migrated instructions from legacy AI provider files."


def source_notes(rules: list[MergedRule]) -> list[str]:
    sources = sorted({source for rule in rules for source in rule.sources})
    if not sources:
        return []
    return [f"- Sources: {', '.join(sources)}"]


def render_canonical(topic: str, scope: str, rules: list[MergedRule], apply_to: str | None) -> str:
    description = description_for(topic, scope, rules)
    frontmatter = ["---", f"description: {quote_frontmatter(description)}"]
    if apply_to:
        frontmatter.append(f"applyTo: {quote_frontmatter(apply_to)}")
    frontmatter.extend(["---", ""])

    stem = topic_stem(topic)
    lines = frontmatter + [f"# {title_from_stem(stem)} Instructions", ""]
    lines.extend(
        [
            "> Migrated proposal. Review wording, scope, and duplicates before applying to canonical instructions.",
            "",
        ]
    )

    section_order = ["Safety", "Workflow", "Architecture", "Style", "Commands", "Config", "Provider Notes"]
    rules_by_section: dict[str, list[MergedRule]] = {}
    for rule in rules:
        rules_by_section.setdefault(rule_section_name(rule.kind), []).append(rule)

    ordered_sections = [section for section in section_order if section in rules_by_section]
    ordered_sections.extend(sorted(section for section in rules_by_section if section not in ordered_sections))

    for section in ordered_sections:
        lines.extend([f"## {section}", ""])
        for rule in sorted(rules_by_section[section], key=lambda item: item.text):
            lines.append(f"- {rule.text}")
        lines.append("")

    notes = source_notes(rules)
    if notes:
        lines.extend(["## Source Notes", ""])
        lines.extend(notes)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def group_rules_for_files(rules: list[MergedRule]) -> tuple[dict[tuple[str, str], list[MergedRule]], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[MergedRule]] = {}
    unsupported: list[dict[str, object]] = []
    scopes_by_topic: dict[str, set[str]] = {}

    for rule in rules:
        scope = normalized_scope(rule.scope)
        scopes_by_topic.setdefault(topic_stem(rule.topic), set()).add(scope)

    mixed_topics = {
        topic
        for topic, scopes in scopes_by_topic.items()
        if len(scopes.intersection({"file-scoped", "topic-based", "on-request"})) > 1
    }

    for rule in rules:
        stem = topic_stem(rule.topic)
        scope = normalized_scope(rule.scope)
        if stem in mixed_topics:
            unsupported.append(
                {
                    "rule": asdict(rule),
                    "reason": "mixed canonical scopes for the same topic require human review",
                }
            )
            continue
        if scope == "root-only":
            unsupported.append({"rule": asdict(rule), "reason": "root-only rules are not written automatically"})
            continue
        if scope == "discard":
            continue
        if scope not in {"file-scoped", "topic-based", "on-request"}:
            unsupported.append({"rule": asdict(rule), "reason": f"unsupported scope: {rule.scope}"})
            continue
        if scope == "file-scoped" and not rule.glob:
            unsupported.append({"rule": asdict(rule), "reason": "file-scoped rule is missing glob"})
            continue
        grouped.setdefault((stem, scope), []).append(rule)

    return grouped, unsupported


def proposed_output_path(stem: str, scope: str) -> str:
    if scope == "on-request":
        return f".github/instructions/skills/{stem}.instructions.md"
    return f".github/instructions/{stem}.instructions.md"


def propose_run(run_id: str):
    run_dir, rules = load_merged_rules(run_id)
    grouped, unsupported = group_rules_for_files(rules)
    proposed_root = run_dir / "proposed"
    proposed_root.mkdir(parents=True, exist_ok=True)
    proposed_files: list[ProposedFile] = []

    for (stem, scope), group in sorted(grouped.items()):
        output_rel = proposed_output_path(stem, scope)
        output_path = proposed_root / output_rel
        output_path.parent.mkdir(parents=True, exist_ok=True)
        apply_to = None
        if scope == "file-scoped":
            apply_to = ",".join(sorted({rule.glob or "" for rule in group if rule.glob}))
        output_path.write_text(render_canonical(stem, scope, group, apply_to), encoding="utf-8")
        proposed_files.append(
            ProposedFile(
                path=output_rel,
                topic=stem,
                scope=scope,
                rule_count=len(group),
                sources=sorted({source for rule in group for source in rule.sources}),
            )
        )

    write_json(proposed_root / "proposed-files.json", [asdict(item) for item in proposed_files])
    write_json(proposed_root / "unsupported-rules.json", unsupported)
    update_manifest(
        run_dir,
        status="proposed",
        proposed_file_count=len(proposed_files),
        unsupported_rule_count=len(unsupported),
        proposed_at=utc_now(),
    )
    return run_dir
