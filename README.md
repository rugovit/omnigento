# Omnigento

Omnigento migrates and maintains AI coding-agent instructions.

Drop it into a repo, tell a filesystem-capable agent to run the setup, and it turns scattered provider files into one canonical instruction system. After that, it keeps GitHub Copilot, Cursor, Claude Code, Codex, and `AGENTS.md` views in sync.

The important part is not just generation. Omnigento can look at the instruction files you already have, classify the useful rules, merge duplicates, propose canonical files, and regenerate the provider-specific outputs.

## Why This Exists

Most projects do not start clean.

They already have some mix of:

- `.github/copilot-instructions.md`
- `.cursor/rules/*.mdc`
- `CLAUDE.md`
- `.claude/rules/*.md`
- `.claude/skills/*/SKILL.md`
- `AGENTS.md`
- old `.cursorrules`, `GEMINI.md`, `.windsurfrules`, `.clinerules`, `.roo/rules/**`, or `.cody/**`

Those files drift. One rule gets copied five times, then edited in two places, then contradicted by a third. After a few weeks, nobody knows which instruction the agent is actually supposed to trust.

Omnigento gives the project one source of truth:

```text
.github/instructions/*.instructions.md        canonical project rules
.github/instructions/skills/*.instructions.md canonical on-request workflows
```

Everything else becomes generated output:

```text
AGENTS.md                                    generated
CLAUDE.md                                    generated
.cursor/rules/*.mdc                          generated
.claude/rules/*.md                           generated
.claude/skills/*/SKILL.md                    generated
```

Canonical files own the truth. Provider files become disposable views.

## The Fire-and-Forget Setup

For an existing repo, the intended workflow is simple:

```bash
git submodule add https://github.com/rugovitGejming/omnigento.git omnigento
```

Then tell your coding agent:

```text
Read and follow omnigento/docs/setup.md.
```

The setup workflow tells the agent to:

1. Plant Omnigento's baseline files.
2. Detect whether the repo is new, already normalized, or full of legacy provider instructions.
3. Inventory existing AI instruction surfaces.
4. Normalize useful existing rules into `.github/instructions/`.
5. Preserve project-specific facts and discard provider boilerplate.
6. Regenerate Copilot, Cursor, Claude, Codex, and Agent Markdown views.
7. Run drift checks and integrity audits.

You still review the diff before committing. But you do not have to manually copy rules between provider files.

## What It Does

- Migrates existing provider-specific instruction files into a canonical schema.
- Generates provider-specific instruction files from `.github/instructions/`.
- Keeps file-scoped rules aligned across Cursor globs, Claude paths, and nested `AGENTS.md`.
- Supports topic-based discovery without pretending it is deterministic auto-loading.
- Supports on-request skills for repeatable agent workflows.
- Detects drift with `--check`.
- Audits orphan generated files, stale provider pointers, frontmatter drift, dangling links, and scaffold residue.
- Provides a staged normalizer for migrating existing Claude, Cursor, Copilot, Agent Markdown, Gemini, Windsurf, Cline, Roo, or Cody instructions into the canonical schema.

## Manual Quick Start

Add Omnigento to a project as an `omnigento/` directory:

```bash
git submodule add https://github.com/rugovitGejming/omnigento.git omnigento
```

Then from the target project root:

```bash
./omnigento/bin/plant.py
./omnigento/bin/sync_ai_instructions.py --audit
```

If the audit shows existing instruction files that need normalization, use the setup workflow instead of guessing:

```text
Read and follow omnigento/docs/setup.md.
```

That file is the migration playbook.

## Daily Workflow

After editing canonical instruction files:

```bash
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
```

Preview generated changes without writing:

```bash
./omnigento/bin/sync_ai_instructions.py --diff
```

Run the integrity audit:

```bash
./omnigento/bin/sync_ai_instructions.py --audit
```

## Canonical Instruction Format

Topic-based rule:

```md
---
description: "Deployment policy and release safety rules."
---

# Deployment Policy

- Production deploys require explicit human approval.
- Run the test deploy script before production changes.
```

File-scoped rule:

```md
---
description: "Python service conventions."
applyTo: "services/**/*.py"
---

# Python Service Conventions

- Keep service startup side-effect free.
- Prefer explicit environment validation at process startup.
```

On-request skill:

```text
.github/instructions/skills/<skill>.instructions.md
```

Skills use `description` frontmatter and no `applyTo`.

## Commands

| Command | Purpose |
|---|---|
| `bin/plant.py` | Plant Omnigento canonical templates and missing provider entry points. |
| `bin/sync_ai_instructions.py --write` | Generate provider views from canonical instructions. |
| `bin/sync_ai_instructions.py --check` | Fail when generated views drift from canonical output. |
| `bin/sync_ai_instructions.py --diff` | Print the generated diff without writing. |
| `bin/sync_ai_instructions.py --audit` | Check structural integrity of generated instruction surfaces. |
| `bin/normalize_legacy_instructions.py` | Inventory, classify, merge, propose, and apply normalized canonical instructions from legacy provider files. |

## Legacy Normalization

For projects that already have scattered AI instruction files, Omnigento uses a staged pipeline:

```text
inventory -> classify -> merge -> propose -> apply -> sync
```

Example:

```bash
RUN_ID="migrate-$(date -u +%Y%m%d-%H%M%SZ)"

./omnigento/bin/normalize_legacy_instructions.py --inventory --run-id "$RUN_ID"
./omnigento/bin/normalize_legacy_instructions.py --classify --run-id "$RUN_ID" --runtime mock
./omnigento/bin/normalize_legacy_instructions.py --merge --run-id "$RUN_ID"
./omnigento/bin/normalize_legacy_instructions.py --propose --run-id "$RUN_ID"
```

The classifier boundary is explicit so teams can wire in their own model/runtime policy.

## Design Principles

- Canonical instructions beat provider boilerplate.
- Generated files should be marked and disposable.
- File-scoped rules should be deterministic where providers support path metadata.
- Topic-based rules should be discoverable, not oversold as guaranteed context.
- Runtime configuration, MCP setup, editor settings, and secrets are outside the instruction compiler.

## Repository Layout

```text
bin/      command-line tools
docs/     setup workflow and detailed reference docs
lib/      normalizer library and instruction surface registry
meta/     version metadata
tests/    zero-dependency regression suite
```

## Verification

Run:

```bash
python3 tests/run_normalizer_regression.py
```

The test suite uses temporary projects and does not modify real project instruction files.

## Status

Omnigento is intentionally small and file-based. It is suitable for teams that want their AI agent instructions to be explicit, reviewable, and reproducible across providers without adding a service dependency.

See [docs/README.md](docs/README.md) for the full reference.
