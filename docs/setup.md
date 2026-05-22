# Omnigento Setup

You are setting up Omnigento in this project.

You have filesystem access. Do not ask the user to paste more prompts. Read this file, run the local scripts, inspect their output, and complete the setup directly unless a real safety conflict requires approval.

## Rules

- Keep durable instructions in `.github/instructions/**/*.instructions.md`.
- Treat provider files as generated views, not sources of truth.
- Do not manually edit generated provider files; fix canonical instructions or compiler code, then regenerate.
- Do not create runtime config, MCP config, editor settings, dependencies, secrets, `.codex/config.toml`, or `.codex/rules/`.
- Do not run `git commit`, `git push`, `git reset`, or destructive git commands.

## Start

From the project root, run:

```bash
./omnigento/bin/plant.py
./omnigento/bin/sync_ai_instructions.py --audit
```

Use the `plant.py` output and the audit findings to choose one path:

- **bootstrap**: no meaningful existing AI instructions beyond Omnigento scaffolds.
- **normalize**: existing Claude, Cursor, Agent Markdown, Gemini, Windsurf, Cline, Roo, Cody, or older Omnigento files contain useful project rules.
- **steady-state repair**: canonical instructions already exist and generated views only need sync/audit cleanup.

## Bootstrap

Use this path for projects with no meaningful existing AI instructions.

1. Inspect the project structure, languages, frameworks, build/test commands, deployment flow, docs, services, config files, and safety constraints.
2. Create or update canonical topics in `.github/instructions/`.
3. Include the core Omnigento topics when missing: `instruction-style` and `omnigento`.
4. If `omnigento/custom-instructions/` exists, apply every `*.instructions.md` template under it after adapting any `<ADAPT:...>` placeholders to this project.
5. Use `applyTo` only for real file or directory scopes. Put broad operational context in topic-based instructions.
6. Keep project-specific facts concrete: commands, paths, ports, environment files, services, release flow, and local gotchas.

## Normalize

Use this path when existing provider instruction files contain useful rules.

1. Start a run:

```bash
RUN_ID="migrate-$(date -u +%Y%m%d-%H%M%SZ)"
./omnigento/bin/normalize_legacy_instructions.py --inventory --run-id "$RUN_ID"
```

2. Prefer the staged normalizer when a classifier adapter is available:

```bash
./omnigento/bin/normalize_legacy_instructions.py --classify \
  --run-id "$RUN_ID" \
  --runtime command \
  --classifier-command '<classifier command>'
./omnigento/bin/normalize_legacy_instructions.py --merge --run-id "$RUN_ID"
./omnigento/bin/normalize_legacy_instructions.py --propose --run-id "$RUN_ID"
```

3. If no classifier adapter exists, manually inspect `inventory.json` and migrate durable rules into canonical `.github/instructions/**/*.instructions.md` files.
4. Preserve safety rules, commands, paths, ports, services, deployment flows, naming conventions, and local gotchas.
5. If `omnigento/custom-instructions/` exists, apply every `*.instructions.md` template under it after adapting any `<ADAPT:...>` placeholders to this project.
6. Discard provider boilerplate, duplicate redirects, generic AI advice already covered by core or custom topics, and obsolete source-of-truth claims.
7. If staged proposals were generated, review `merge/migration-table.md`, `proposed/`, and `proposed/unsupported-rules.json` before applying:

```bash
./omnigento/bin/normalize_legacy_instructions.py --apply --run-id "$RUN_ID"
```

Use `--allow-unsupported` only when you intentionally accept leaving unsupported rules out of automatic apply. Use `--overwrite` only after reviewing the backup behavior.

## Steady-State Repair

Use this path when canonical instructions already exist.

1. Fix canonical instructions or compiler logic, not generated output.
2. Remove scaffold-only content by replacing it with generated views.
3. Let the sync compiler remove stale generated provider files.

## Verify

Always finish with:

```bash
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
./omnigento/bin/sync_ai_instructions.py --audit
```

Also run the regression suite when changing Omnigento itself:

```bash
python3 omnigento/tests/run_normalizer_regression.py
```

## Report

Finish with a concise report:

- protocol chosen
- audit findings repaired or intentionally left for review
- files created, updated, or deleted
- project facts preserved
- boilerplate discarded
- conflicts and assumptions
- verification commands and results
