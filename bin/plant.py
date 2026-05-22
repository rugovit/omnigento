#!/usr/bin/env python3
"""Plant or refresh Omnigento in a project."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


SEED_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = SEED_ROOT / "docs"
VERSION_FILE = SEED_ROOT / "meta" / "VERSION"


COPILOT_SKELETON = """# Project AI Instructions

<!-- omnigento scaffold -->

> Scaffold: run the Bootstrap Protocol or Normalize Existing Instructions Protocol.

## AI Behavior - READ THIS FIRST

**ASK before creating files. VERIFY before suggesting. Be CONCISE.**

-> Full rules: [ai-behavior.instructions.md](.github/instructions/ai-behavior.instructions.md)

---

## Reference Docs

| File | Covers | Auto-loads for |
|------|--------|----------------|
| [instruction-style.instructions.md](.github/instructions/instruction-style.instructions.md) | Instruction file style guide | `.github/instructions/**` |
| [omnigento.instructions.md](.github/instructions/omnigento.instructions.md) | System architecture, bootstrap, normalization, evolution | On-demand |

---

## Quick Reference

| Task | Command / Location |
|------|--------------------|
"""


CLAUDE_SKELETON = """# Project

<!-- omnigento scaffold -->

Read and follow `.github/copilot-instructions.md` - it is the single source of truth for all project rules.

Detailed topic rules live in `.github/instructions/*.instructions.md`. For topic-based rules, read the relevant file when the topic comes up.
"""


AGENTS_SKELETON = """# Project

<!-- omnigento scaffold -->

Read and follow `.github/copilot-instructions.md` - it is the single source of truth for all project rules.

Detailed topic rules live in `.github/instructions/*.instructions.md`. Subdirectory `AGENTS.md` files add scoped agent pointers, but canonical content belongs in `.github/instructions/`.

Omnigento setup is documented in `.github/instructions/omnigento.instructions.md`.
After planting, ask a filesystem-capable AI agent to read and follow `omnigento/docs/setup.md`.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plant Omnigento files and missing provider entry points.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Run from the target project root. If run from the Omnigento directory inside a git "
            "repository, the git root is used. The script plants Omnigento only; after it "
            "finishes, ask a filesystem-capable AI agent to read and follow omnigento/docs/setup.md."
        ),
    )
    return parser.parse_args()


def git_root() -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(SEED_ROOT), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return Path(value).resolve() if value else None


def target_root() -> Path:
    return git_root() or Path(".").resolve()


def read_version() -> str:
    if not VERSION_FILE.exists():
        return "unknown"
    return VERSION_FILE.read_text(encoding="utf-8").strip() or "unknown"


def has_files(path: Path) -> bool:
    return path.is_dir() and any(child.is_file() for child in path.rglob("*"))


def detect_existing_instructions(target: Path) -> bool:
    files = [
        ".github/copilot-instructions.md",
        "CLAUDE.md",
        "AGENTS.md",
        "GEMINI.md",
        ".windsurfrules",
        ".clinerules",
    ]
    if any((target / item).is_file() for item in files):
        return True

    dirs = [
        ".github/instructions",
        ".cursor/rules",
        ".claude/rules",
        ".roo/rules",
    ]
    return any(has_files(target / item) for item in dirs)


def write_if_missing(path: Path, text: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def ensure_gitignore_entry(target: Path, entry: str) -> bool:
    gitignore = target / ".gitignore"
    if not gitignore.exists():
        return False
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    if entry in lines:
        return False
    with gitignore.open("a", encoding="utf-8") as handle:
        handle.write(f"{entry}\n")
    return True


def plant() -> int:
    parse_args()

    target = target_root()
    if not target.is_dir():
        print(f"Error: target directory '{target}' does not exist.", file=sys.stderr)
        return 1

    seed_version = read_version()
    existing = detect_existing_instructions(target)
    next_protocol = "Normalize Existing Instructions Protocol" if existing else "Bootstrap Protocol"

    print("")
    print(f"  Planting Omnigento v{seed_version} in: {target}")
    print("")

    for path in [
        target / ".github" / "instructions",
        target / ".cursor" / "rules",
        target / ".claude" / "rules",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    print("  Ensured directory structure:")
    print("    .github/instructions/  (canonical content layer)")
    print("    .cursor/rules/         (Cursor provider view)")
    print("    .claude/rules/         (Claude Code provider view)")
    print("")

    shutil.copy2(DOCS_DIR / "omnigento.instructions.md", target / ".github" / "instructions")
    shutil.copy2(DOCS_DIR / "instruction-style.instructions.md", target / ".github" / "instructions")
    (target / ".github" / "instructions" / "omnigento.version").write_text(
        f"{seed_version}\n", encoding="utf-8"
    )

    print("  Planted versioned Omnigento files:")
    print("    .github/instructions/omnigento.instructions.md")
    print("    .github/instructions/instruction-style.instructions.md")
    print("    .github/instructions/omnigento.version")
    print("")

    created_roots = []
    root_skeletons = [
        (target / ".github" / "copilot-instructions.md", COPILOT_SKELETON, ".github/copilot-instructions.md"),
        (target / "CLAUDE.md", CLAUDE_SKELETON, "CLAUDE.md"),
        (target / "AGENTS.md", AGENTS_SKELETON, "AGENTS.md"),
    ]
    for path, text, label in root_skeletons:
        if write_if_missing(path, text):
            created_roots.append(label)
            print(f"  Created {label} (scaffold)")

    if not created_roots:
        print("  Root provider files already exist - skipped root scaffolds")

    added_gitignore = [entry for entry in [".DS_Store", "Thumbs.db"] if ensure_gitignore_entry(target, entry)]
    if added_gitignore:
        print(f"  Added to .gitignore: {' '.join(added_gitignore)}")

    print("")
    print("  ================================================")
    print("  Omnigento planted. No AI prompt was run.")
    print("  ================================================")
    print("")
    print(f"  Existing instruction files detected before planting: {str(existing).lower()}")
    print(f"  Recommended protocol: {next_protocol}")
    print("")
    print("  Next step:")
    print("    Ask your filesystem-capable AI agent:")
    print("      Read and follow omnigento/docs/setup.md")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(plant())
