# Omnigento

Omnigento is a small compiler-backed system for keeping AI coding-agent instructions consistent across providers.

The core idea is simple: write durable rules once in `.github/instructions/`, then generate provider-specific views for tools such as GitHub Copilot, Cursor, Claude Code, Codex, and any agent that reads `AGENTS.md`.

## Philosophy

AI instructions rot when every provider file becomes its own source of truth. Cursor wants `.mdc`, Claude wants `CLAUDE.md` and skills, Copilot reads `.github/copilot-instructions.md`, and agent-markdown tools read `AGENTS.md`. If those files are edited by hand, they drift.

Omnigento rejects that model.

Canonical instructions live in one place:

```text
.github/instructions/*.instructions.md
.github/instructions/skills/*.instructions.md
```

Everything else is a generated view. Generated files may inline canonical content for deterministic loading, but they do not own the rule. If a generated provider file is wrong, fix the canonical instruction or the compiler, then regenerate.

## Bundle Layout

The portable kit keeps only `HOW_TO_RUN.md` at the `omnigento/` root:

```text
omnigento/
  HOW_TO_RUN.md
  bin/      executable CLIs
  docs/     setup workflow, README, and canonical Omnigento templates
  lib/      normalizer library and instruction surface registry
  meta/     version metadata
  tests/    regression tests
```

## What This Solves

- Provider drift: the same rule no longer needs to be manually copied into Cursor, Claude, Copilot, Codex, and nested agent files.
- Loading determinism for file-scoped rules: Cursor `globs`, Claude `paths`, and nested `AGENTS.md` files all come from the same `applyTo`.
- On-request action discovery: skill-style tasks live under `.github/instructions/skills/` and generate Claude skills plus Cursor agent-requested rules.
- Safe maintenance: generated files are marked, and stale generated files can be removed without deleting unknown hand-written files.
- Honest topic handling: topic-based rules stay compact by default. There is no fake promise of universal determinism for broad topics.

## Instruction Forms

Omnigento covers several instruction forms, but it does not pretend they all work the same way.

| Form | Trigger | Best for | Determinism |
|------|---------|----------|-------------|
| Hub / root instructions | Always or near-always loaded by provider | Global project facts, safety rules, navigation | Highest, but limited space |
| File-scoped rules | Matching edited/read file path | Directory constraints, coding standards, never-edit zones | Strong when provider respects paths/globs |
| Topic-based rules | Conversation relevance | Broad references, tools, policies, operational context | Medium/weak; model-mediated |
| On-request skills | User intent/task type | Repeatable workflows that produce artifacts | Strong in Claude, medium in Cursor, weak in Copilot/Agent Markdown |
| Prompts | Manually copied or invoked | One-time migrations, setup protocols, complex bounded tasks | Only as deterministic as the invocation |
| Generated provider views | Provider-specific loading mechanism | Delivery format for canonical rules | Depends on provider |
| Runtime/tool config | Tool availability, MCP, connectors | Giving AI access to tools/data | Not an instruction form |
| Local project docs | Agent reads docs while working | Intent near code, gotchas, design history | Opportunistic |
| Inline chat/task instructions | Current user/developer message | Immediate task-specific direction | Strong for the current session |

Coverage today:

| Form | Covered by Omnigento? | Current state |
|------|------------------------------|---------------|
| Canonical durable rules | Yes | Strong. `.github/instructions/**/*.instructions.md` is the source of truth. |
| Hub/root instructions | Yes | Strong. Generates/updates `AGENTS.md`, `CLAUDE.md`, and the Copilot generated table. |
| File-scoped rules | Yes | Strong. `applyTo` generates Cursor globs, Claude paths, and nested `AGENTS.md`. |
| Topic-based rules | Yes | Intentional compact discovery. Not deterministic auto-load. |
| On-request skills | Yes | Canonical `skills/` generates Claude skills, Cursor agent-requested rules, Agent Markdown entries, and hub rows. |
| Generated provider views | Yes | Strong. Compiler owns generated files/blocks with markers. |
| Provider drift checking | Yes | Strong. `sync_ai_instructions.py --check`. |
| Prompts | Partly | `setup.md` is the filesystem-agent setup protocol. `HOW_TO_RUN.md` is only a pointer. |
| Runtime/tool config | Deliberately separate | Mentioned as out of scope. Do not mix MCP/tool config into instruction sync. |
| Local docs as AI context | Partly | Covered through project documentation rules, but not compiled as provider instructions. |
| Inline chat/task instructions | No | Session-level behavior; not something the repo can compile. |
| CI/pre-commit enforcement | Optional | Documented as optional. Projects can wire `--check` themselves. |

Use this mental model:

```text
Rules = durable behavior
File-scoped = path-triggered rules
Topics = discoverable reference
Skills = intent-triggered workflows
Prompts = manually invoked procedures
Runtime config = tool availability
Project docs = local context
```

## Instruction Classes

Instruction class is determined by location and frontmatter.

| Class | Canonical location | Frontmatter | Generated surfaces |
|-------|--------------------|-------------|--------------------|
| File-scoped | `.github/instructions/<topic>.instructions.md` | `description` + `applyTo` | Cursor rule, Claude rule, hub row, nested `AGENTS.md` when the glob maps to a clean directory |
| Topic-based | `.github/instructions/<topic>.instructions.md` | `description` only | Compact topic indexes, root `AGENTS.md`, hub row |
| On-request | `.github/instructions/skills/<topic>.instructions.md` | `description` only | Claude skill, Cursor agent-requested rule, root `AGENTS.md`, hub row |

Skills must not have `applyTo`. Top-level file-scoped instructions must have a non-empty `applyTo`.

## Topic-Based Rules

Topic-based rules are discovery entries, not hard enforcement.

In Omnigento projects, topic-based canonical files live at:

```text
.github/instructions/<topic>.instructions.md
```

They have `description` frontmatter but no `applyTo`.

Provider behavior differs:

| Provider surface | How topic-based rules work |
|------------------|----------------------------|
| GitHub Copilot | The hub table in `.github/copilot-instructions.md` lists the topic. Do not assume Copilot reads every topic description and auto-loads the best match. |
| Cursor | `.cursor/rules/topic-index.mdc` lists compact topic entries. The model must decide to read the relevant canonical file. |
| Claude Code | `.claude/rules/topic-index.md` lists compact topic entries. The model must decide to read the relevant canonical file. |
| Agent Markdown | Root `AGENTS.md` lists topic-based topics. This is discoverability, not path-scoped loading. |

Use topic-based rules for broad operational context: deployment policy, live-data tools, server health tools, environment references, and AI behavior rules.

Do not use topic-based rules for critical path constraints such as "never edit this directory" or "all files under this path must follow X." Those belong in file-scoped rules with `applyTo`.

## On-Request Skills

Skills are intent-triggered workflows. They are not path rules.

In Omnigento projects, canonical skills live at:

```text
.github/instructions/skills/<skill>.instructions.md
```

They have `description` frontmatter and no `applyTo`. The description should be phrased around user intent, because providers use it as the discovery trigger.

Generated provider behavior differs:

| Provider surface | How skills work |
|------------------|-----------------|
| Claude Code | `.claude/skills/<skill>/SKILL.md` is the strongest native skill surface. Claude can match the user request to skill metadata and load the generated skill body. |
| Cursor | `.cursor/rules/<skill>.mdc` with `description:` and no `globs:` acts as an agent-requested rule. Cursor may apply it when user intent matches. |
| Agent Markdown | Root `AGENTS.md` lists the skill under On-request actions. Agents must choose to use it. |
| GitHub Copilot | The hub table marks the skill as `On-request`. This is discoverability, not a strong native skill mechanism. |

Generated skill views may inline the canonical body so the workflow is present when the provider loads the skill. The canonical skill file still owns the rule.

## Generated Files

Fully generated files contain:

```md
<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->
```

Files that keep manual content, such as `.github/copilot-instructions.md`, use a generated block:

```md
<!-- BEGIN GENERATED INSTRUCTIONS -->
...
<!-- END GENERATED INSTRUCTIONS -->
```

Do not manually edit generated provider files. Edit canonical instructions and run the sync compiler.

## Daily Workflow

After changing any canonical instruction:

```bash
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
```

To preview changes first:

```bash
./omnigento/bin/sync_ai_instructions.py --diff
```

`--check` exits non-zero when generated files drift from canonical output. Projects may put it in CI or pre-commit, but that is optional.

## Setup Workflow

For filesystem-capable AI agents, the user-facing instruction is intentionally one line:

```text
Read and follow omnigento/docs/setup.md.
```

`setup.md` is the single agent entrypoint. It tells the agent to plant Omnigento, choose bootstrap/normalize/steady-state repair, run deterministic scripts, inspect staged artifacts, and finish with sync/check/audit.

For manual terminal use, start with:

```bash
./omnigento/bin/plant.py
```

`plant.py` only plants Omnigento files and missing scaffolds; it does not run an AI migration by itself. After planting, continue with `omnigento/docs/setup.md`.

## Legacy Normalization CLI

`bin/normalize_legacy_instructions.py` is the staged migration pipeline for projects that already have AI instructions from one or more providers. It does not replace the sync compiler. Its job is to turn legacy provider files into proposed canonical `.github/instructions/**/*.instructions.md` files.

Pipeline:

```text
inventory -> classify -> merge -> propose -> apply -> sync
```

Implementation layout:

| Module | Responsibility |
|--------|----------------|
| `bin/normalize_legacy_instructions.py` | CLI compatibility wrapper |
| `lib/normalizer/models.py` | Artifact and classifier data contracts |
| `lib/normalizer/inventory.py` | Surface scanning and file role classification |
| `lib/normalizer/classify.py` | Classifier runtime boundary and output validation |
| `lib/normalizer/merge.py` | Deterministic rule dedupe and proposal tables |
| `lib/normalizer/propose.py` | Canonical `.instructions.md` proposal rendering |
| `lib/normalizer/apply.py` | Guarded canonical file apply and backups |
| `lib/normalizer/artifacts.py` | Run directories, JSON artifacts, manifest updates |

For a smoke test, run classification with `mock`; it extracts no real rules:

```bash
./omnigento/bin/normalize_legacy_instructions.py --inventory --run-id <id>
./omnigento/bin/normalize_legacy_instructions.py --classify --run-id <id> --runtime mock
./omnigento/bin/normalize_legacy_instructions.py --merge --run-id <id>
./omnigento/bin/normalize_legacy_instructions.py --propose --run-id <id>
```

For a real migration, use the command classifier boundary:

```bash
./omnigento/bin/normalize_legacy_instructions.py --inventory --run-id <id>
./omnigento/bin/normalize_legacy_instructions.py --classify \
  --run-id <id> \
  --runtime command \
  --classifier-command 'python3 path/to/classifier_adapter.py'
./omnigento/bin/normalize_legacy_instructions.py --merge --run-id <id>
./omnigento/bin/normalize_legacy_instructions.py --propose --run-id <id>
./omnigento/bin/normalize_legacy_instructions.py --apply --run-id <id>
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
```

All intermediate output is staged under:

```text
omnigento/.tmp/normalize/<run-id>/
```

The `.tmp` directory is ignored by Git. Staged runs are audit artifacts: keep them while reviewing a migration, delete them when no longer needed.

### Inventory

Inventory is deterministic. It scans known instruction surfaces from `lib/instruction_surfaces.py`, labels each discovered file, hashes it, and records whether it is canonical, generated, scaffolded, or a legacy input.

```bash
./omnigento/bin/normalize_legacy_instructions.py --inventory --run-id migrate-001
```

The scanner recognizes current generated markers and generated blocks, so existing Omnigento outputs are not treated as fresh legacy truth.

Important outputs:

```text
manifest.json
inventory.json
```

### Classification

Classification consumes only records marked `legacy_input`. Generated provider views and canonical Omnigento files are skipped.

The default runtime is `mock`:

```bash
./omnigento/bin/normalize_legacy_instructions.py --classify --run-id migrate-001 --runtime mock
```

`mock` validates the pipeline shape but extracts no rules. Use it for smoke tests.

For real classification, use the provider-agnostic command runtime:

```bash
./omnigento/bin/normalize_legacy_instructions.py --classify \
  --run-id migrate-001 \
  --runtime command \
  --classifier-command 'python3 path/to/classifier_adapter.py'
```

The external classifier receives one `ClassificationTask` JSON object on stdin and must return one `ClassificationResult` JSON object on stdout. The normalizer validates that `source_path`, `surface_id`, and `source_sha256` match the task before accepting output.

Classifier output is treated as untrusted input. The normalizer validates status, scope, kind, confidence, non-empty rule fields, file-scoped glob usage, and source attribution before writing classification artifacts.

Task JSON is also persisted for debugging:

```text
classifications/tasks/<source>.task.json
```

Classification results are written to:

```text
classifications/by-file/<source>.json
classifications/classification-index.json
```

Classifier output contract:

```json
{
  "source_path": "CLAUDE.md",
  "surface_id": "claude-root",
  "owner": "claude",
  "surface_kind": "root",
  "source_sha256": "<same as task>",
  "runtime": "command",
  "status": "classified",
  "durable_rules": [
    {
      "text": "Never deploy directly to production.",
      "topic": "server-access",
      "scope": "topic-based",
      "glob": null,
      "kind": "safety",
      "confidence": "high",
      "sources": ["CLAUDE.md"],
      "source_quote": "Never deploy directly to production."
    }
  ],
  "discarded": [
    {
      "text": "Read this file first.",
      "reason": "provider boilerplate",
      "source_quote": "Read this file first."
    }
  ],
  "conflicts": [],
  "notes": []
}
```

Supported rule scopes:

| Scope | Meaning |
|-------|---------|
| `file-scoped` | Writes `.github/instructions/<topic>.instructions.md` with `applyTo`. Requires `glob`. |
| `topic-based` | Writes `.github/instructions/<topic>.instructions.md` without `applyTo`. |
| `on-request` | Writes `.github/instructions/skills/<topic>.instructions.md`. |
| `root-only` | Not applied automatically. Quarantined for human review. |
| `discard` | Ignored by proposal writer. |

Supported rule kinds:

```text
safety, workflow, style, command, architecture, config, provider
```

### Merge

Merge is deterministic:

```bash
./omnigento/bin/normalize_legacy_instructions.py --merge --run-id migrate-001
```

It deduplicates identical rules, aggregates sources and source quotes, carries classifier conflicts forward, and keeps the lowest confidence when duplicate rules disagree.

Important outputs:

```text
merge/merged-rules.json
merge/discarded.json
merge/conflicts.json
merge/merge-proposal.json
merge/migration-table.md
```

### Propose

Propose renders staged canonical instruction files but does not touch real `.github/instructions`:

```bash
./omnigento/bin/normalize_legacy_instructions.py --propose --run-id migrate-001
```

Outputs:

```text
proposed/.github/instructions/*.instructions.md
proposed/.github/instructions/skills/*.instructions.md
proposed/proposed-files.json
proposed/unsupported-rules.json
```

The proposal writer is intentionally conservative. It quarantines:

- `root-only` rules
- unsupported scopes
- file-scoped rules without a glob
- mixed canonical scopes for the same topic

Review `unsupported-rules.json` before applying.

### Apply

Apply is the only normalization step that writes to real canonical files:

```bash
./omnigento/bin/normalize_legacy_instructions.py --apply --run-id migrate-001
```

Safety guards:

- only canonical paths under `.github/instructions/` ending in `.instructions.md` can be applied
- unsupported rules block apply unless `--allow-unsupported` is passed
- existing canonical files are not overwritten unless `--overwrite` is passed
- overwritten files are backed up under `applied/backups/`
- generated provider views are never written by `--apply`

After apply, always run:

```bash
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
```

### Regression Tests

The normalizer has a zero-dependency regression runner:

```bash
python3 omnigento/tests/run_normalizer_regression.py
```

Expected success output:

```text
PASS normalized_project_noop
PASS legacy_overlap_pipeline
PASS invalid_classifier_status_rejected
PASS apply_rejects_symlink_source
PASS run_id_traversal_rejected
PASS 5 regression tests
```

It creates temporary mini projects and verifies:

- already-normalized projects are no-ops
- generated provider views are not re-imported as legacy input
- legacy `GEMINI.md` and `.windsurfrules` files are inventoried as legacy inputs
- command-runtime classification is accepted only through the JSON contract
- overlapping rules are merged, conflicts are preserved, unsupported root-only rules are quarantined
- apply refuses unresolved unsupported rules, then applies only canonical proposal files when explicitly allowed
- invalid classifier status values are rejected
- symlinked proposed source files are rejected during apply
- unsafe run ids cannot escape the normalize artifact directory

The runner uses `tempfile.TemporaryDirectory`, copies only the required Omnigento scripts into each mini project, and deletes those projects when the run exits. It should not create or modify real project instruction files.

To sanity-check that the test harness really fails, temporarily break one assertion. For example, change the expected legacy input count in `test_legacy_overlap_pipeline` from `2` to `999`, then run:

```bash
python3 omnigento/tests/run_normalizer_regression.py
```

Expected failure:

```text
FAIL legacy_overlap_pipeline: legacy overlap input count: expected 999, got 2
```

Restore the assertion to `2` and rerun the test. It must pass again before committing.

## Compiler Contract

`bin/sync_ai_instructions.py`:

- reads canonical `.instructions.md` files
- validates required `description` frontmatter
- validates `applyTo` usage by class
- generates provider views from canonical content
- writes generated markers
- updates the generated Reference Docs block in `.github/copilot-instructions.md`
- removes stale generated provider files when a canonical stem disappears
- does not delete unmarked unknown files

It deliberately does not create runtime config such as `.codex/config.toml`, MCP configs, editor settings, API keys, or secrets. Instruction sync and runtime/tool config sync are separate problems.

## Why Inline Some Views

Pointer-only provider files are fragile in this repo. Some agents reliably load path-scoped files but do not always chase secondary links before acting. For file-scoped and on-request rules, generated views inline the canonical body so the provider sees the rule at load time.

That does not mean every rule should be globally inlined everywhere. Topic-based rules are broad and conversation-triggered. Inlining all of them globally creates bloat and weakens signal. The default is compact discovery indexes for topic-based rules, with deterministic loading focused on path-scoped and on-request surfaces.

## What To Tell Another AI

Use this instruction when asking another AI to change the instruction system:

```text
Edit only canonical instruction files under .github/instructions/**/*.instructions.md.
Do not manually edit generated provider views.
After changing canonical instructions, run:
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
```

If the AI edits `AGENTS.md`, `.cursor/rules/`, `.claude/rules/`, `.claude/skills/`, `CLAUDE.md`, or the generated block in `.github/copilot-instructions.md` directly, it is editing the wrong layer.
