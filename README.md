# Omnigento

Omnigento is a setup kit for keeping AI coding-agent instructions consistent across tools.

If your project already has instruction files for Cursor, Claude, Copilot, Codex, `AGENTS.md`, or older agent tools, Omnigento helps an AI agent migrate them into one canonical instruction system and keep every provider view in sync after that.

The user workflow is intentionally simple:

```text
Read and follow omnigento/docs/setup.md.
```

You give that instruction to a filesystem-capable coding agent. The agent reads the project, runs the Omnigento scripts, migrates or creates the canonical instruction files, regenerates the provider-specific files, and verifies consistency.

You review the diff. You do not manually copy rules between five different AI tools.

## What Problem It Solves

AI coding tools all want their own instruction format:

- GitHub Copilot uses `.github/copilot-instructions.md`
- Cursor uses `.cursor/rules/*.mdc`
- Claude Code uses `CLAUDE.md`, `.claude/rules/*.md`, and `.claude/skills/*/SKILL.md`
- Codex and other tools read `AGENTS.md`
- Older setups may have `.cursorrules`, `GEMINI.md`, `.windsurfrules`, `.clinerules`, `.roo/rules/**`, or `.cody/**`

Without a system, the same project rule gets copied everywhere. Then one copy changes, another does not, and your agents start receiving contradictory instructions.

Omnigento fixes that by making `.github/instructions/` the canonical source of truth.

```text
.github/instructions/*.instructions.md        canonical project rules
.github/instructions/skills/*.instructions.md canonical on-request workflows
```

Everything else becomes generated:

```text
AGENTS.md
CLAUDE.md
.github/copilot-instructions.md
.cursor/rules/*.mdc
.claude/rules/*.md
.claude/skills/*/SKILL.md
```

The provider files are no longer hand-maintained. They are regenerated from the canonical `.github/instructions/` folder.

## What Happens When You Use It

For an existing project, Omnigento helps your AI agent:

1. Find existing AI instruction files.
2. Decide whether the project needs a fresh setup, a migration, or a repair.
3. Extract useful project rules from old provider-specific files.
4. Remove provider boilerplate and stale source-of-truth claims.
5. Create or update canonical `.github/instructions/*.instructions.md` files.
6. Add the Omnigento instruction rules that teach future agents how to maintain the system.
7. Regenerate Copilot, Cursor, Claude, Codex, and `AGENTS.md` views from the canonical files.
8. Run checks so generated files cannot silently drift.

That is the main value: Omnigento does the messy migration and leaves behind a maintainable instruction system.

## After Setup

After Omnigento is installed, future instruction changes should happen in `.github/instructions/`.

You can still use an AI agent for this. Tell it what behavior you want added or changed, and it should update the canonical instruction files first. Then it runs Omnigento's sync script to regenerate every provider view from the canonical source.

That means the human workflow is:

```text
"Add instructions for how this repo handles deployments."
```

The agent workflow is:

```text
edit .github/instructions/...
run ./omnigento/bin/sync_ai_instructions.py --write
run ./omnigento/bin/sync_ai_instructions.py --check
```

The important part for the user is that consistency is maintained automatically by the generated provider views. You do not need to remember how Cursor, Claude, Copilot, and `AGENTS.md` each want the same rule formatted.

## Install

Add Omnigento to your project:

```bash
git submodule add https://github.com/rugovitGejming/omnigento.git omnigento
```

Then ask your coding agent:

```text
Read and follow omnigento/docs/setup.md.
```

The setup file is the migration playbook. It tells the agent when to bootstrap, when to normalize existing instructions, and when to repair generated drift.

## What Omnigento Adds To Your Project

Omnigento plants and maintains a canonical instruction structure:

```text
.github/instructions/
  ai-behavior.instructions.md
  documentation-rules.instructions.md
  instruction-style.instructions.md
  omnigento.instructions.md
  ...
  skills/
    <workflow>.instructions.md
```

The `omnigento.instructions.md` and `instruction-style.instructions.md` files are especially important. They teach future agents that:

- canonical instructions live in `.github/instructions/`
- generated provider files should not be edited by hand
- new instructions should be added to the canonical layer first
- provider views should be regenerated from canonical files
- drift checks should be run before finishing

This is what makes the setup durable instead of a one-time migration.

## For Maintainers

Most users should interact with Omnigento through their AI agent. The scripts exist so the agent has deterministic tools instead of improvising.

Core scripts:

| Script | What it is for |
|---|---|
| `bin/plant.py` | Adds Omnigento baseline files and missing provider entry points. |
| `bin/normalize_legacy_instructions.py` | Inventories and migrates existing provider-specific instruction files into canonical files. |
| `bin/sync_ai_instructions.py --write` | Regenerates provider files from `.github/instructions/`. |
| `bin/sync_ai_instructions.py --check` | Fails if generated provider files drift from canonical output. |
| `bin/sync_ai_instructions.py --audit` | Finds broken generated surfaces, orphan rules, dangling links, and scaffold residue. |

## Verification

Omnigento has a zero-dependency regression suite:

```bash
python3 tests/run_normalizer_regression.py
```

The tests use temporary projects and do not modify real project instruction files.

## Status

Omnigento is intentionally file-based. It does not require a service, database, editor plugin, or hosted account. It is meant to make AI instruction systems reviewable, portable, and consistent across tools.

See [docs/README.md](docs/README.md) for the detailed technical reference.
