"""Guarded apply stage for staged canonical instruction proposals."""

from __future__ import annotations

import shutil
from dataclasses import asdict
from pathlib import Path

from .artifacts import REPO_ROOT, load_proposed, repo_rel, update_manifest, utc_now, write_json
from .models import AppliedFile


def ensure_safe_apply_path(path: str) -> None:
    candidate = Path(path)
    if path.startswith("/") or ".." in candidate.parts:
        raise ValueError(f"unsafe proposed path: {path}")
    if not (path.startswith(".github/instructions/") and path.endswith(".instructions.md")):
        raise ValueError(f"refusing to apply non-canonical proposed path: {path}")


def has_symlink_component(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    current = root
    for part in rel.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            return True
    return False


def ensure_within(child: Path, parent: Path, label: str) -> None:
    try:
        child.relative_to(parent)
    except ValueError as exc:
        raise ValueError(f"{label} escapes expected root: {child}") from exc


def safe_source_path(run_dir: Path, item_path: str) -> Path:
    proposed_root = run_dir / "proposed"
    source = proposed_root / item_path
    if not source.exists():
        raise ValueError(f"proposed source file is missing: {repo_rel(source)}")
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"proposed source must be a regular file: {repo_rel(source)}")
    if has_symlink_component(source, proposed_root):
        raise ValueError(f"proposed source path contains a symlink: {repo_rel(source)}")
    ensure_within(source.resolve(strict=True), proposed_root.resolve(strict=True), "proposed source")
    return source


def safe_target_path(item_path: str) -> Path:
    target = REPO_ROOT / item_path
    canonical_root = REPO_ROOT / ".github" / "instructions"
    canonical_root.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.is_symlink():
        raise ValueError(f"refusing to overwrite symlink target: {item_path}")
    if has_symlink_component(target.parent, REPO_ROOT):
        raise ValueError(f"target parent path contains a symlink: {item_path}")
    ensure_within(target.parent.resolve(strict=True), canonical_root.resolve(strict=True), "target path")
    return target


def backup_existing(path: Path, run_dir: Path) -> str | None:
    if not path.exists():
        return None
    backup_root = run_dir / "applied" / "backups"
    backup_path = backup_root / repo_rel(path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    return repo_rel(backup_path)


def apply_run(run_id: str, allow_unsupported: bool, overwrite: bool):
    run_dir, proposed, unsupported = load_proposed(run_id)
    if unsupported and not allow_unsupported:
        raise ValueError(
            f"refusing to apply with {len(unsupported)} unsupported rules; review unsupported-rules.json "
            "or pass --allow-unsupported"
        )

    applied_dir = run_dir / "applied"
    applied_dir.mkdir(parents=True, exist_ok=True)
    applied: list[AppliedFile] = []

    for item in proposed:
        ensure_safe_apply_path(item.path)
        source = safe_source_path(run_dir, item.path)
        target = safe_target_path(item.path)
        if target.exists() and not overwrite:
            raise ValueError(f"refusing to overwrite existing canonical file without --overwrite: {item.path}")
        backup_path = backup_existing(target, run_dir)
        shutil.copy2(source, target)
        applied.append(
            AppliedFile(
                path=item.path,
                action="overwritten" if backup_path else "created",
                backup_path=backup_path,
            )
        )

    write_json(applied_dir / "applied-files.json", [asdict(item) for item in applied])
    update_manifest(
        run_dir,
        status="applied",
        applied_file_count=len(applied),
        applied_at=utc_now(),
    )
    return run_dir
