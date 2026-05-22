"""Deterministic merge stage for classified instruction rules."""

from __future__ import annotations

from dataclasses import asdict

from .artifacts import load_classifications, update_manifest, utc_now, write_json
from .models import ClassificationResult, DiscardedRule, ExtractedRule, MergedRule, MergeProposal


def confidence_rank(confidence: str) -> int:
    ranks = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    return ranks.get(confidence.lower(), 0)


def merged_confidence(values: list[str]) -> str:
    if not values:
        return "low"
    return min(values, key=confidence_rank)


def rule_key(rule: ExtractedRule) -> tuple[str, str, str | None, str, str]:
    return (
        rule.topic.strip().lower(),
        rule.scope.strip().lower(),
        rule.glob.strip() if rule.glob else None,
        rule.kind.strip().lower(),
        " ".join(rule.text.split()).lower(),
    )


def build_merge_proposal(run_id: str, results: list[ClassificationResult]) -> MergeProposal:
    grouped: dict[tuple[str, str, str | None, str, str], list[ExtractedRule]] = {}
    discarded: list[DiscardedRule] = []
    conflicts: list[str] = []
    notes: list[str] = []

    for result in results:
        discarded.extend(result.discarded)
        conflicts.extend(f"{result.source_path}: {conflict}" for conflict in result.conflicts)
        notes.extend(f"{result.source_path}: {note}" for note in result.notes)
        for rule in result.durable_rules:
            grouped.setdefault(rule_key(rule), []).append(rule)

    merged_rules: list[MergedRule] = []
    for rules in grouped.values():
        first = rules[0]
        sources = sorted({source for rule in rules for source in rule.sources})
        source_quotes = sorted({rule.source_quote for rule in rules if rule.source_quote})
        confidences = [rule.confidence for rule in rules]
        merged_rules.append(
            MergedRule(
                text=first.text,
                topic=first.topic,
                scope=first.scope,
                glob=first.glob,
                kind=first.kind,
                confidence=merged_confidence(confidences),
                sources=sources,
                source_quotes=source_quotes,
            )
        )

    merged_rules.sort(key=lambda rule: (rule.topic, rule.scope, rule.glob or "", rule.kind, rule.text))
    discarded.sort(key=lambda item: (item.reason, item.text, item.source_quote))
    conflicts = sorted(set(conflicts))
    notes = sorted(set(notes))

    return MergeProposal(
        run_id=run_id,
        status="proposal",
        merged_rules=merged_rules,
        discarded=discarded,
        conflicts=conflicts,
        notes=notes,
    )


def markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def migration_table(proposal: MergeProposal) -> str:
    lines = [
        "# Instruction Migration Proposal",
        "",
        f"Run: `{proposal.run_id}`",
        "",
        "## Proposed Rules",
        "",
        "| Topic | Scope | Glob | Kind | Confidence | Sources | Rule |",
        "|------|-------|------|------|------------|---------|------|",
    ]
    if proposal.merged_rules:
        for rule in proposal.merged_rules:
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_cell(rule.topic),
                        markdown_cell(rule.scope),
                        markdown_cell(rule.glob or ""),
                        markdown_cell(rule.kind),
                        markdown_cell(rule.confidence),
                        markdown_cell(", ".join(rule.sources)),
                        markdown_cell(rule.text),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| _None_ |  |  |  |  |  |  |")

    lines.extend(["", "## Conflicts", ""])
    if proposal.conflicts:
        lines.extend(f"- {item}" for item in proposal.conflicts)
    else:
        lines.append("- None")

    lines.extend(["", "## Discarded", ""])
    if proposal.discarded:
        lines.extend(f"- {item.reason}: {item.text}" for item in proposal.discarded)
    else:
        lines.append("- None")

    lines.extend(["", "## Notes", ""])
    if proposal.notes:
        lines.extend(f"- {item}" for item in proposal.notes)
    else:
        lines.append("- None")
    return "\n".join(lines).rstrip() + "\n"


def merge_run(run_id: str):
    run_dir, results = load_classifications(run_id)
    proposal = build_merge_proposal(run_id, results)
    merge_dir = run_dir / "merge"
    merge_dir.mkdir(parents=True, exist_ok=True)

    write_json(merge_dir / "merged-rules.json", [asdict(rule) for rule in proposal.merged_rules])
    write_json(merge_dir / "discarded.json", [asdict(item) for item in proposal.discarded])
    write_json(merge_dir / "conflicts.json", proposal.conflicts)
    write_json(merge_dir / "merge-proposal.json", asdict(proposal))
    (merge_dir / "migration-table.md").write_text(migration_table(proposal), encoding="utf-8")
    update_manifest(
        run_dir,
        status="merged",
        merged_rule_count=len(proposal.merged_rules),
        conflict_count=len(proposal.conflicts),
        discarded_count=len(proposal.discarded),
        merged_at=utc_now(),
    )
    return run_dir
