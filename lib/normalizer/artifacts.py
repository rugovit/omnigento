"""Run artifact paths and JSON persistence for the normalizer."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    ClassificationResult,
    DiscardedRule,
    ExtractedRule,
    InventoryRecord,
    MergedRule,
    ProposedFile,
)


PACKAGE_DIR = Path(__file__).resolve().parent
LIB_DIR = PACKAGE_DIR.parent
SEED_ROOT = LIB_DIR.parent
REPO_ROOT = SEED_ROOT.parent
TMP_ROOT = SEED_ROOT / ".tmp" / "normalize"
SAFE_RUN_ID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def repo_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_artifact_name(path: str) -> str:
    name = path.replace("/", "__").replace("\\", "__")
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in name)


def run_dir_for(run_id: str) -> Path:
    if not run_id or any(char not in SAFE_RUN_ID_CHARS for char in run_id):
        raise ValueError("run id may contain only letters, digits, '.', '_', and '-'")
    if run_id in {".", ".."}:
        raise ValueError("run id cannot be '.' or '..'")
    return TMP_ROOT / run_id


def load_seed_version() -> str:
    version = SEED_ROOT / "meta" / "VERSION"
    if not version.exists():
        return "unknown"
    return version.read_text(encoding="utf-8").strip() or "unknown"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_inventory_run(records: list[InventoryRecord], run_id: str, command: list[str]) -> Path:
    run_dir = run_dir_for(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "created_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "omnigento_version": load_seed_version(),
        "command": command,
        "status": "inventory",
        "record_count": len(records),
    }
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "inventory.json", [asdict(record) for record in records])
    return run_dir


def load_inventory(run_id: str) -> tuple[Path, list[InventoryRecord]]:
    run_dir = run_dir_for(run_id)
    inventory_path = run_dir / "inventory.json"
    if not inventory_path.exists():
        raise ValueError(f"inventory not found for run id {run_id!r}: {repo_rel(inventory_path)}")
    raw = read_json(inventory_path)
    if not isinstance(raw, list):
        raise ValueError(f"inventory artifact must be a list: {repo_rel(inventory_path)}")
    return run_dir, [InventoryRecord(**item) for item in raw]


def load_classifications(run_id: str) -> tuple[Path, list[ClassificationResult]]:
    run_dir = run_dir_for(run_id)
    classify_dir = run_dir / "classifications" / "by-file"
    if not classify_dir.exists():
        raise ValueError(f"classifications not found for run id {run_id!r}: {repo_rel(classify_dir)}")

    results: list[ClassificationResult] = []
    for path in sorted(classify_dir.glob("*.json")):
        raw = read_json(path)
        if not isinstance(raw, dict):
            raise ValueError(f"classification artifact must be an object: {repo_rel(path)}")
        durable_rules = [ExtractedRule(**item) for item in raw.get("durable_rules", [])]
        discarded = [DiscardedRule(**item) for item in raw.get("discarded", [])]
        results.append(
            ClassificationResult(
                source_path=raw["source_path"],
                surface_id=raw["surface_id"],
                owner=raw["owner"],
                surface_kind=raw["surface_kind"],
                source_sha256=raw["source_sha256"],
                runtime=raw["runtime"],
                status=raw["status"],
                durable_rules=durable_rules,
                discarded=discarded,
                conflicts=list(raw.get("conflicts", [])),
                notes=list(raw.get("notes", [])),
            )
        )
    return run_dir, results


def load_merged_rules(run_id: str) -> tuple[Path, list[MergedRule]]:
    run_dir = run_dir_for(run_id)
    merged_path = run_dir / "merge" / "merged-rules.json"
    if not merged_path.exists():
        raise ValueError(f"merged rules not found for run id {run_id!r}: {repo_rel(merged_path)}")
    raw = read_json(merged_path)
    if not isinstance(raw, list):
        raise ValueError(f"merged rules artifact must be a list: {repo_rel(merged_path)}")
    return run_dir, [MergedRule(**item) for item in raw]


def load_proposed(run_id: str) -> tuple[Path, list[ProposedFile], list[dict[str, object]]]:
    run_dir = run_dir_for(run_id)
    proposed_root = run_dir / "proposed"
    proposed_path = proposed_root / "proposed-files.json"
    unsupported_path = proposed_root / "unsupported-rules.json"
    if not proposed_path.exists():
        raise ValueError(f"proposed files not found for run id {run_id!r}: {repo_rel(proposed_path)}")
    if not unsupported_path.exists():
        raise ValueError(f"unsupported rules not found for run id {run_id!r}: {repo_rel(unsupported_path)}")
    proposed_raw = read_json(proposed_path)
    unsupported_raw = read_json(unsupported_path)
    if not isinstance(proposed_raw, list):
        raise ValueError(f"proposed files artifact must be a list: {repo_rel(proposed_path)}")
    if not isinstance(unsupported_raw, list):
        raise ValueError(f"unsupported rules artifact must be a list: {repo_rel(unsupported_path)}")
    return run_dir, [ProposedFile(**item) for item in proposed_raw], unsupported_raw


def update_manifest(run_dir: Path, **updates: object) -> None:
    manifest_path = run_dir / "manifest.json"
    manifest: dict[str, object] = {}
    if manifest_path.exists():
        raw = read_json(manifest_path)
        if isinstance(raw, dict):
            manifest = raw
    manifest.update(updates)
    write_json(manifest_path, manifest)
