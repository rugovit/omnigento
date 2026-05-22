"""Command-line orchestration for legacy instruction normalization."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .apply import apply_run
from .artifacts import read_json, repo_rel, utc_run_id, write_inventory_run
from .classify import classify_run
from .inventory import inventory
from .merge import merge_run
from .models import InventoryRecord
from .propose import propose_run


def print_inventory_summary(records: list[InventoryRecord], run_dir: Path | None) -> None:
    by_role: dict[str, int] = {}
    by_surface: dict[str, int] = {}
    for record in records:
        by_role[record.role] = by_role.get(record.role, 0) + 1
        by_surface[record.surface_id] = by_surface.get(record.surface_id, 0) + 1

    print(f"inventory records: {len(records)}")
    if run_dir:
        print(f"run directory: {repo_rel(run_dir)}")
    if by_role:
        print("roles:")
        for role, count in sorted(by_role.items()):
            print(f"  {role}: {count}")
    if by_surface:
        print("surfaces:")
        for surface_id, count in sorted(by_surface.items()):
            print(f"  {surface_id}: {count}")


def print_classify_summary(run_dir: Path) -> None:
    index = read_json(run_dir / "classifications" / "classification-index.json")
    if not isinstance(index, dict):
        raise ValueError("classification-index.json must be an object")
    print(f"classified sources: {index['classified_count']}")
    print(f"runtime: {index['runtime']}")
    print(f"run directory: {repo_rel(run_dir)}")


def print_merge_summary(run_dir: Path) -> None:
    proposal = read_json(run_dir / "merge" / "merge-proposal.json")
    if not isinstance(proposal, dict):
        raise ValueError("merge-proposal.json must be an object")
    print(f"merged rules: {len(proposal['merged_rules'])}")
    print(f"conflicts: {len(proposal['conflicts'])}")
    print(f"discarded: {len(proposal['discarded'])}")
    print(f"run directory: {repo_rel(run_dir)}")


def print_propose_summary(run_dir: Path) -> None:
    proposed = read_json(run_dir / "proposed" / "proposed-files.json")
    unsupported = read_json(run_dir / "proposed" / "unsupported-rules.json")
    if not isinstance(proposed, list) or not isinstance(unsupported, list):
        raise ValueError("proposal artifacts must be lists")
    print(f"proposed files: {len(proposed)}")
    print(f"unsupported rules: {len(unsupported)}")
    print(f"run directory: {repo_rel(run_dir)}")


def print_apply_summary(run_dir: Path) -> None:
    applied = read_json(run_dir / "applied" / "applied-files.json")
    if not isinstance(applied, list):
        raise ValueError("applied-files.json must be a list")
    print(f"applied files: {len(applied)}")
    for item in applied:
        detail = item["action"]
        if item.get("backup_path"):
            detail += f"; backup: {item['backup_path']}"
        print(f"  {item['path']} ({detail})")
    print(f"run directory: {repo_rel(run_dir)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Staged legacy AI instruction normalization.")
    parser.add_argument("--inventory", action="store_true", help="scan and write an instruction inventory")
    parser.add_argument("--classify", action="store_true", help="classify legacy inputs from an existing run")
    parser.add_argument("--merge", action="store_true", help="merge classification outputs into a staged proposal")
    parser.add_argument("--propose", action="store_true", help="write staged canonical instruction file proposals")
    parser.add_argument("--apply", action="store_true", help="apply staged canonical proposals to .github/instructions")
    parser.add_argument("--allow-unsupported", action="store_true", help="allow apply when unsupported rules remain")
    parser.add_argument("--overwrite", action="store_true", help="allow apply to overwrite existing canonical files")
    parser.add_argument("--json", action="store_true", help="print inventory JSON to stdout")
    parser.add_argument("--run-id", help="explicit run id for the output directory")
    parser.add_argument("--runtime", default="mock", help="classifier runtime for --classify; default: mock")
    parser.add_argument(
        "--classifier-command",
        help="external classifier command for --runtime command; receives task JSON on stdin",
    )
    parser.add_argument(
        "--classifier-timeout",
        type=int,
        default=300,
        help="seconds to wait for each external classifier command; default: 300",
    )
    parser.add_argument("--no-write", action="store_true", help="do not write omnigento/.tmp output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected_modes = [args.inventory, args.classify, args.merge, args.propose, args.apply]
    if sum(1 for selected in selected_modes if selected) > 1:
        print(
            "error: choose only one mode: --inventory, --classify, --merge, --propose, or --apply",
            file=sys.stderr,
        )
        return 2
    if not any(selected_modes):
        print("error: choose a mode: --inventory, --classify, --merge, --propose, or --apply", file=sys.stderr)
        return 2

    try:
        if args.inventory:
            records = inventory()
            run_dir = None if args.no_write else write_inventory_run(records, args.run_id or utc_run_id(), sys.argv)

            if args.json:
                print(json.dumps([asdict(record) for record in records], indent=2, sort_keys=True))
            else:
                print_inventory_summary(records, run_dir)
            return 0

        if args.no_write:
            print(
                "error: --classify, --merge, --propose, and --apply write outputs and cannot be combined with --no-write",
                file=sys.stderr,
            )
            return 2
        if not args.run_id:
            print("error: --classify, --merge, --propose, and --apply require --run-id", file=sys.stderr)
            return 2

        if args.classify:
            run_dir = classify_run(args.run_id, args.runtime, args.classifier_command, args.classifier_timeout)
            print_classify_summary(run_dir)
        elif args.merge:
            run_dir = merge_run(args.run_id)
            print_merge_summary(run_dir)
        elif args.propose:
            run_dir = propose_run(args.run_id)
            print_propose_summary(run_dir)
        else:
            run_dir = apply_run(args.run_id, args.allow_unsupported, args.overwrite)
            print_apply_summary(run_dir)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
