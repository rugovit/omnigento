---
description: "Omnigento: provider-agnostic AI instruction architecture, bootstrap, normalization, Codex/Copilot/Claude/Cursor outputs, and evolution protocols."
---

# Omnigento

> Portable core of the AI instruction system. Copy the `omnigento/` bundle into any project, run `./omnigento/bin/plant.py`, then ask a filesystem-capable AI agent to read and follow `omnigento/docs/setup.md`.
> This file stays in the project permanently - it drives setup, migration, and ongoing evolution.
> **Exception to the 120-line rule** - the Omnigento kit must be self-contained for portability.

---

## S0 Operating Principle

**Canonical schema wins.** Existing provider-specific instruction files are input material; the normalized output lives in the Omnigento schema.

**Project facts survive.** Commands, paths, ports, services, safety constraints, deployment flows, and local conventions are preserved unless they conflict with Omnigento architecture.

**Provider boilerplate does not survive.** Claims like "this Claude file is source of truth" are discarded when normalizing into the Omnigento schema.

**`bin/plant.py` is deterministic.** It plants versioned Omnigento files and missing provider entry points; it never runs an AI prompt.

**Setup has one agent entrypoint.** `HOW_TO_RUN.md` is only a human-facing pointer. Filesystem-capable agents read `omnigento/docs/setup.md` and run the local scripts directly. Users should not paste multi-step prompts.

**Audit before transform.** Every protocol begins with the Integrity Audit Checklist (end of S1). Repair dangling references, orphan pointers, scaffold residue, and frontmatter drift as part of completion - never leave a half-fix.

**Git is rollback.** Prefer a coherent normalized rewrite over fragile partial patching, then let the user inspect and revert with Git if needed.

---

## S1 Architecture

### Canonical Layers

| Layer | Location | Purpose |
|-------|----------|---------|
| **Content** (shared) | `.github/instructions/*.instructions.md` | Provider-agnostic rules - one topic per file |
| **Root hub** | `.github/copilot-instructions.md` | Project overview, AI behavior, reference docs table, quick reference |
| **Cursor view** | `.cursor/rules/*.mdc` | Cursor project rules with `globs:` or `description:` frontmatter |
| **Claude Code view** | `CLAUDE.md`, `.claude/rules/*.md`, `.claude/skills/*/SKILL.md` | Generated Claude view; path/request rules inline canonical bodies |
| **Agent Markdown view** | `AGENTS.md`, nested `<dir>/AGENTS.md` | Shared agent instructions for tools that read this convention, including Cursor and Codex. Root lists global discovery topics; nested files inline directory-scoped canonical bodies |

### Root Entry Points

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | Hub for all providers; not Copilot-only despite the filename |
| `AGENTS.md` | Shared agent-markdown root provider file: pointer to the hub + topic/action discovery map |
| `CLAUDE.md` | Claude root pointer to the hub + topic index |

### Loading Strategy

| Topic class | Canonical location + frontmatter | Provider output |
|-------------|----------------------------------|-----------------|
| File-scoped | `.github/instructions/<n>.instructions.md` with `applyTo: "glob"` + `description` | Cursor `.mdc` with `globs:`, Claude `.md` with `paths:`, hub Reference Docs row, nested `<dir>/AGENTS.md` for clean/concrete directory scopes. Generated path-scoped views inline canonical bodies |
| Topic-based | `.github/instructions/<n>.instructions.md` with `description` only | Topic indexes in Cursor (`topic-index.mdc`), Claude (`topic-index.md`), root `AGENTS.md` Topic-based section, Copilot hub Reference Docs row |
| On-request (skills) | `.github/instructions/skills/<n>.instructions.md` with `description` only | Claude skill (`.claude/skills/<n>/SKILL.md`), Cursor agent-requested rule (`.cursor/rules/<n>.mdc` with `description:` only, no `globs:`), root `AGENTS.md` On-request actions section, hub Reference Docs row marked `On-request`. Generated request views inline canonical bodies. NOT listed in topic-indexes. |

**Class discriminator is canonical location.** Files at top level of `.github/instructions/` are file-scoped or topic-based (per frontmatter). Files under `.github/instructions/skills/` are on-request. No new frontmatter key — the subfolder is the marker.

**Why on-request is separate.** Topic-based loading is passive (the model decides to read the topic-index when conversation matches). On-request loading is active — the provider's discovery loop matches the user's intent and surfaces the topic. Claude skills and Cursor agent-requested rules are first-class provider features for this.

**AGENTS.md loading model.** `AGENTS.md` is the shared markdown view for agents that read this convention, including Cursor and Codex. It cannot express Cursor `.mdc` frontmatter or Claude skill metadata. Root `AGENTS.md` carries topic-based and on-request discovery; nested `<dir>/AGENTS.md` files carry file-scoped routing for clean/concrete directory scopes.

**Topic-based reality.** Topic-based rules are discoverability, not guaranteed auto-loading. GitHub Copilot should be expected to read the hub table, not every topic description in every canonical file. Cursor, Claude, and Agent Markdown topic indexes are compact maps that rely on the model choosing the relevant canonical file.

**Skill reality.** Skills are intent-triggered workflows, not file path rules. Claude Code has the strongest native skill surface. Cursor agent-requested rules are model-mediated. Agent Markdown and GitHub Copilot skill entries are discovery surfaces, not strict triggers.

### Instruction Forms

Omnigento covers multiple instruction forms, but they have different triggers and reliability:

| Form | Trigger | Covered? | Notes |
|------|---------|----------|-------|
| Hub/root instructions | Provider startup/global load | Yes | `AGENTS.md`, `CLAUDE.md`, and the Copilot hub orient the agent. Keep these concise. |
| File-scoped rules | Matching path/glob | Yes | Strongest durable routing. Use for directory constraints and coding standards. |
| Topic-based rules | Conversation relevance | Yes | Compact discovery only; not guaranteed auto-loading. |
| On-request skills | User intent/task type | Yes | Strong in Claude, decent in Cursor, discovery-only in Copilot/Agent Markdown. |
| Prompts | Manual invocation | Partly | `setup.md` is the filesystem-agent setup protocol. `HOW_TO_RUN.md` only points to it. |
| Generated provider views | Provider loading mechanism | Yes | Compiler output; do not hand-edit. |
| Runtime/tool config | Tool availability | No | Separate from instructions. Do not create MCP/Codex/editor config during instruction sync. |
| Local project docs | Agent reads docs while working | Partly | Useful context, but not provider instruction output. |
| Inline chat/task instructions | Current conversation | No | Session-level override, outside repo compilation. |

**Mental model:** durable rules live in canonical instructions; file-scoped rules are path-triggered; topics are discoverable references; skills are intent-triggered workflows; prompts are manually invoked procedures; runtime config controls tool availability; project docs provide local context.

**Runtime config boundary.** Bootstrap, Normalize, and Evolution protocols do not generate or normalize `.codex/config.toml`, `.codex/rules/`, MCP JSON, API keys, editor settings, or local secrets as instruction content. Runtime/tool config parity is handled only by the optional S9 protocol after instruction setup is complete.

### Generated Provider Templates

Provider files are generated views, not canonical sources. The canonical source remains `.github/instructions/**/*.instructions.md`.

After editing any canonical instruction file, run:

```bash
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
```

Projects may add `./omnigento/bin/sync_ai_instructions.py --check` to CI or pre-commit for drift enforcement, but it is optional.

Generated path-scoped and on-request views may inline canonical content for deterministic loading. Topic-based rules are different: compact discovery indexes are the default because universal topic inlining creates global bloat rather than real determinism.

**Cursor** (`.cursor/rules/<name>.mdc`):

~~~
---
globs: "<matching glob>"
alwaysApply: false
---
<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/<name>.instructions.md`

<full canonical body>
~~~

**Claude Code** (`.claude/rules/<name>.md`) - inline the full canonical body:

~~~
---
paths:
  - "<matching glob>"
---

<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/<name>.instructions.md`

<full canonical body>
~~~

**Agent Markdown root** (`AGENTS.md`) - lists global discovery topics:

~~~
# <Project>

Read and follow `.github/copilot-instructions.md` - it is the single source of truth for all project rules.

Detailed topic rules live in `.github/instructions/*.instructions.md`. Generated provider views may inline canonical content; canonical source remains `.github/instructions/`.

`AGENTS.md` is the shared agent-markdown view for tools that read this convention, including Cursor and Codex. File-scoped routing lives in provider path metadata and nested `AGENTS.md` files.

## Topic-based topics

- **<Keyword group>** -> `.github/instructions/<topic>.instructions.md`

## On-request actions

- **<Keyword group>** -> `.github/instructions/skills/<topic>.instructions.md`
~~~

**Agent Markdown scoped view** (`<directory>/AGENTS.md`) - generate one for each file-scoped topic whose `applyTo` maps cleanly to a directory subtree. Multi-root globs may generate multiple nested files for their concrete directory roots; extension-only fragments stay hub/provider-native. When two file-scoped topics overlap on the same subtree, inline both applicable canonical bodies in one nested file.

~~~
# <Directory> Agent Rules

<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `<relative path to repo root>/.github/instructions/<topic>.instructions.md`

<full applicable canonical body>
~~~

**Claude Code skill** (`.claude/skills/<name>/SKILL.md`) - emitted for canonical files under `.github/instructions/skills/`. Generated trigger view with inline canonical body:

~~~
---
name: <name>
description: <trigger phrase from canonical description>
---

# <Topic>

<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/skills/<name>.instructions.md`

<full canonical body>
~~~

**Cursor agent-requested** (`.cursor/rules/<name>.mdc`) - emitted for canonical files under `.github/instructions/skills/`. Description-only, no `globs:`:

~~~
---
description: "<trigger phrase>"
alwaysApply: false
---
<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/skills/<name>.instructions.md`

<full canonical body>
~~~

**Topic indexes.** `.cursor/rules/topic-index.mdc` and `.claude/rules/topic-index.md` list topic-based files as `**Keywords** -> <filename>.instructions.md`. Root `AGENTS.md` carries the same topic-based list under its "Topic-based topics" section, plus an "On-request actions" section. On-request files under `instructions/skills/` do NOT appear in topic indexes - they have their own provider discovery surface (skill / agent-requested rule).

### Integrity Audit Checklist

The schema is healthy when **all** of the following hold. Bootstrap (S4), Normalize (S5), and Evolution Audit (S6) each end by walking this list.

- **No dangling references.** Every link from `.github/copilot-instructions.md`, `.cursor/rules/topic-index.mdc`, `.claude/rules/topic-index.md`, root `AGENTS.md`, and `CLAUDE.md` resolves to a file that exists.
- **Provider stem parity.** Every `.cursor/rules/<stem>.mdc`, `.claude/rules/<stem>.md`, and `.claude/skills/<stem>/SKILL.md` stem matches an existing canonical at `.github/instructions/<stem>.instructions.md` (file-scoped/topic-based) or `.github/instructions/skills/<stem>.instructions.md` (on-request). A pointer whose body links to a real canonical file but whose own filename diverges is **orphan** and must be renamed. Renamed or removed topics leave no provider pointer behind.
- **No scaffold residue.** No file in the project still contains the marker `<!-- omnigento scaffold -->`.
- **Hub completeness.** Every `.github/instructions/**/*.instructions.md` topic appears as a row in the hub Reference Docs table. On-request topics show their `skills/` path and are marked `On-request` in the Auto-loads column.
- **Provider parity.** File-scoped topics have both Cursor `.mdc` (with `globs:`) and Claude `.md` (with `paths:`) generated inline views, plus nested `AGENTS.md` generated inline views for clean/concrete directory scopes. Topic-based topics appear in Cursor, Claude, and Agent Markdown (root `AGENTS.md`) compact topic indexes. On-request topics have a Claude skill, a Cursor agent-requested generated inline rule (no `globs:`), and a root `AGENTS.md` On-request actions entry.
- **On-request exclusion from topic indexes.** Topics under `.github/instructions/skills/` do NOT appear in `.cursor/rules/topic-index.mdc`, `.claude/rules/topic-index.md`, or the root `AGENTS.md` Topic-based section. Their discovery surface is the dedicated provider file (skill / agent-requested rule) and the On-request actions section.
- **Skill body discipline.** Every `.claude/skills/<n>/SKILL.md` and Cursor agent-requested `.mdc` body is generated from canonical and may inline the full canonical body. Manual edits are drift and must be overwritten by the sync compiler.
- **AGENTS.md coverage.** Root `AGENTS.md` lists topic-based topics and on-request actions in two clearly-labeled sections. File-scoped topics are surfaced through the hub, Cursor/Claude path metadata, and nested `AGENTS.md` files.
- **Nested `AGENTS.md` completeness.** Every file-scoped topic whose `applyTo` maps cleanly to a directory subtree has a nested `<dir>/AGENTS.md` generated inline view. Multi-root globs generate nested views for their concrete directory roots where practical; extension-only fragments stay hub/provider-native. Stale generated nested `AGENTS.md` whose canonical was renamed or removed has been updated or deleted.
- **Frontmatter validity.** `.cursor/rules/topic-index.mdc` uses `alwaysApply: false` only - never an empty `globs: ""`. `.claude/rules/topic-index.md` needs no frontmatter. File-scoped Cursor generated views carry a non-empty `globs:` matching the canonical `applyTo:`.
- **Index wording parity.** Each topic carries one canonical one-line summary; the same wording appears in every topic index (Cursor, Claude, Agent Markdown) and the hub row. No drift.
- **No source-of-truth drift.** No provider file (CLAUDE.md, AGENTS.md, GEMINI.md, .windsurfrules, .clinerules) claims to be the source of truth; supported root provider files point at the hub.
- **No provider-only rules.** Generated provider files may inline canonical rules, but no durable project rule may live only in a provider file - everything durable is reflected in `.github/instructions/`.
- **No runtime/config output during instruction sync.** Bootstrap, Normalize, and Evolution do not create `.codex/config.toml`, `.codex/rules/`, MCP config, editor settings, or secrets.
- **Workspace hygiene.** If `.gitignore` exists, it ignores `.DS_Store` and `Thumbs.db`. (`bin/plant.py` enforces this; the audit re-checks.)

---

## S2 Core And Custom Topics

**Core Omnigento topics are limited to instruction-system maintenance.** Core topics tell future agents where canonical instructions live, how provider views are generated, and how to keep the instruction system consistent. They must not impose project-specific coding, documentation, communication, testing, or deployment preferences.

**Always keep these core topics:**

- `omnigento.instructions.md`
- `instruction-style.instructions.md`

**Optional custom instructions are user-owned.** If `omnigento/custom-instructions/` exists, treat every `*.instructions.md` file under it as an opt-in reusable instruction template. During bootstrap or normalization, copy or adapt those templates into `.github/instructions/` before generating provider views.

Custom instructions are where users can keep personal or company preferences such as AI interaction style, strict documentation rules, review posture, testing habits, or deployment rituals. These are useful, but they are not universal Omnigento defaults.

**Custom instruction rules:**

- Preserve the filename when copying into `.github/instructions/`.
- Preserve frontmatter unless it contains `<ADAPT:...>` placeholders.
- Adapt `<ADAPT:...>` placeholders to real project paths or omit the file and report why.
- Do not apply a custom instruction if it conflicts with explicit project rules.
- Report every custom instruction applied, skipped, or adapted.

---

## S3 Setup Entrypoint

**Human-facing pointer:** `omnigento/HOW_TO_RUN.md`.

**Agent-facing workflow:** `omnigento/docs/setup.md`.

**The workflow is intentionally stored once.** Do not duplicate it in this file or `plant.py`; update `setup.md` when the agent setup procedure changes. Keep `HOW_TO_RUN.md` as a minimal pointer.

---

## S4 Bootstrap Protocol

**When:** Setting up the instruction system in a project with no meaningful existing AI instructions.

**Trigger:** User says to execute Bootstrap Protocol, or `bin/plant.py` reports no existing instructions.

### Step 1 - Discover

Scan the project: languages, frameworks, build tools, directory structure, existing configs, CI/CD, deployment scripts, external integrations, databases, documentation, tests, and release workflow.

### Step 2 - Propose

Present a topic table to the user:

- **Core topics:** `instruction-style`, `omnigento`
- **Custom topics:** any `*.instructions.md` files under `omnigento/custom-instructions/`, if the folder exists
- **Discovered topics:** 3-8 project-specific topics based on discovery
- **For each topic:** filename, one-line description, file-scoped vs topic-based, glob pattern if file-scoped, source evidence

**Interactive mode:** Wait for user approval before generating files.

**Filesystem-agent mode:** Generate directly after discovery, then report assumptions and conflicts.

### Step 3 - Generate Canonical Content

For each approved topic:

1. Create `.github/instructions/<topic>.instructions.md` following `instruction-style`.
2. Use `applyTo` only for natural file scopes.
3. Keep durable project rules in `.github/instructions/`, not provider files.
4. Apply custom instruction templates from `omnigento/custom-instructions/` when present, adapting `<ADAPT:...>` markers to the project.

### Step 4 - Generate Provider Views

1. Create/update `.github/copilot-instructions.md` as the hub.
2. Create/update `.cursor/rules/*.mdc` and `.cursor/rules/topic-index.mdc`.
3. Create/update `CLAUDE.md`, `.claude/rules/*.md`, and `.claude/rules/topic-index.md`.
4. Create/update `AGENTS.md`; add nested `AGENTS.md` for clean directory-scoped rules.

### Step 5 - Verify and Report

Walk the **Integrity Audit Checklist** (end of S1). Every item must hold before reporting completion. Report files created/updated, audit findings repaired, and any assumptions.

---

## S5 Normalize Existing Instructions Protocol

**When:** A project already has AI instruction files from any provider or an older Omnigento version.

**Trigger:** User says normalize/migrate/upgrade instructions, or `bin/plant.py` reports existing instructions.

**Goal:** Convert any existing instruction ecosystem into the Omnigento schema while preserving useful project facts.

### Step 1 - Inventory

Find instruction-like files, excluding `.git`, dependencies, build outputs, virtualenvs, vendored code, generated artifacts, and accidental provider outputs inside the `omnigento/` kit.

| Source | Examples |
|--------|----------|
| Omnigento/Copilot | `.github/instructions/**`, `.github/copilot-instructions.md` |
| Agent Markdown | `AGENTS.md`, nested `<dir>/AGENTS.md` |
| Claude | `CLAUDE.md`, nested `CLAUDE.md`, `.claude/rules/**` |
| Cursor | `.cursor/rules/**` |
| Other AI tools | `GEMINI.md`, `.windsurfrules`, `.clinerules`, `.roo/rules/**`, `.cody/**` |
| Project docs | `CONTRIBUTING.md`, `DEVELOPMENT.md`, `docs/**` only when clearly instruction-like |

### Step 2 - Extract Durable Rules

Extract only useful rules and facts:

- **Safety:** destructive actions, production access, secrets, data mutation, approvals
- **Workflow:** build, test, deploy, release, review, issue tracking
- **Architecture:** services, modules, ownership boundaries, data flow, naming
- **Style:** coding conventions, formatting, documentation, comments
- **Commands:** exact commands, arguments, working directories, environment files
- **Scopes:** globs, directories, file types, topic triggers
- **Provider gotchas:** only if they still matter after normalization

Discard:

- **Provider boilerplate:** "read this file", "this provider file is source of truth", duplicate redirects
- **Generic AI advice:** not a project fact unless it came from explicit project instructions or an opted-in custom instruction
- **Obsolete layout claims:** anything that conflicts with the Omnigento schema
- **Duplicated wording:** preserve the strongest rule once, not every copy

### Step 3 - Classify

For each extracted rule, record:

| Field | Meaning |
|-------|---------|
| `topic` | Proposed canonical topic filename |
| `scope` | File-scoped, topic-based, root-only, or discard |
| `glob` | File pattern if file-scoped |
| `source` | Original file path(s) |
| `kind` | Safety, workflow, style, command, architecture, config, provider |
| `confidence` | High when explicit; low when inferred |

### Step 4 - Merge

Apply this priority order:

1. **Omnigento schema** wins for file locations, provider layout, sync rules, and source-of-truth claims.
2. **Safety restrictions** win over convenience or speed.
3. **Project-specific facts** survive when not contradicted by safety or schema.
4. **More specific scopes** win over broad scopes.
5. **Existing provider wording** is used only when it expresses a project rule better than Omnigento.
6. **Inferred rules** are weakest and should be proposed, not silently asserted.

**Overlap rule:** If an existing rule overlaps with a core Omnigento rule, use the Omnigento wording and preserve only project-specific additions. If an existing rule overlaps with a custom instruction, preserve the explicit project rule and report the custom conflict.

**Conflict rule:** Resolve obvious conflicts by the priority table; list meaningful unresolved conflicts in the proposal before writing.

### Step 5 - Propose Migration

Before generating, present a concise migration table:

| Topic | Output file | Scope | Sources | Merge notes |
|-------|-------------|-------|---------|-------------|

Include:

- **Preserved facts:** commands, paths, ports, services, deploy/test flows
- **Discarded boilerplate:** provider-only redirects and obsolete source-of-truth claims
- **Conflicts:** what was resolved automatically and what needs user choice

**Interactive mode:** Wait for user approval unless the user explicitly asked for automatic normalization.

**Filesystem-agent mode:** Generate directly after resolving obvious overlaps by Omnigento priority, then report assumptions and conflicts.

### Step 6 - Generate Canonical Schema

After approval:

1. Regenerate `.github/instructions/*.instructions.md` as canonical topic files.
2. Regenerate `.github/copilot-instructions.md` as the hub.
3. Regenerate Cursor, Claude, and Agent Markdown provider views from canonical topics.
4. Do not write `.codex/config.toml`, `.codex/rules/`, MCP config, secrets, or editor runtime settings.
5. Keep old provider files only if they are part of the supported schema; otherwise archive/delete only with explicit user approval.

### Step 7 - Verify

Walk the **Integrity Audit Checklist** (end of S1). Every item must hold before reporting completion. In addition, for normalization specifically:

- Nested `AGENTS.md` files exist when they cleanly map to a directory scope and do not exist for multi-root, extension-only, or ambiguous globs.
- Discarded provider boilerplate is genuinely gone, not relocated under a different name.

### Step 8 - Report

Report:

- **Created/updated:** files changed
- **Preserved:** key project facts kept from older instructions
- **Discarded:** boilerplate/duplicates removed
- **Conflicts:** unresolved items and recommended decision
- **Rollback:** remind that Git can revert the normalization if the result is not right

---

## S6 Evolution Protocol

**Same pattern at every scale:** DISCOVER -> PROPOSE -> APPROVE -> GENERATE -> SYNC.

### Add a Topic

1. Identify what needs its own instruction file or re-scan the project.
2. Propose name, description, and class: **file-scoped** (with glob), **topic-based**, or **on-request** (skill).
3. Create canonical at `.github/instructions/<topic>.instructions.md` (file-scoped/topic-based) or `.github/instructions/skills/<topic>.instructions.md` (on-request).
4. Run `./omnigento/bin/sync_ai_instructions.py --write` to generate provider views by class:
   - File-scoped: `.cursor/rules/<topic>.mdc` (with `globs:`), `.claude/rules/<topic>.md` (with `paths:`), nested `<dir>/AGENTS.md` for clean/concrete directory scopes.
   - Topic-based: entry in `.cursor/rules/topic-index.mdc`, `.claude/rules/topic-index.md`, and root `AGENTS.md` Topic-based section.
   - On-request: `.claude/skills/<topic>/SKILL.md`, `.cursor/rules/<topic>.mdc` (no `globs:`, agent-requested), entry in root `AGENTS.md` On-request actions section.
5. Run `./omnigento/bin/sync_ai_instructions.py --check` and inspect the generated diff.

### Edit a Topic

1. Edit canonical (`.github/instructions/<topic>.instructions.md` or `.github/instructions/skills/<topic>.instructions.md`) as the single source of truth.
2. Run `./omnigento/bin/sync_ai_instructions.py --write`.
3. Run `./omnigento/bin/sync_ai_instructions.py --check`.
4. If class changed (e.g., topic-based -> on-request), verify stale generated provider files from the old class were removed.

### Remove a Topic

1. Delete canonical (`.github/instructions/<topic>.instructions.md` or `.github/instructions/skills/<topic>.instructions.md`).
2. Run `./omnigento/bin/sync_ai_instructions.py --write`.
3. Run `./omnigento/bin/sync_ai_instructions.py --check`.
4. Verify stale generated provider files were removed and unmarked unknown files were not deleted.

### Audit

Walk the **Integrity Audit Checklist** (end of S1). The same checklist used during Bootstrap and Normalize is the steady-state health check; if any item fails, repair it before continuing other work.

---

## S7 Versioning

**Omnigento version source:** `omnigento/meta/VERSION` in the portable kit.

**Applied version marker:** `bin/plant.py` writes `.github/instructions/omnigento.version` in the target project.

**Legacy projects:** Missing version marker means `legacy-unversioned`; normalize by content, not by guessing version history.

**Version bump policy:**

| Change | Version bump |
|--------|--------------|
| Typo or wording clarification | Patch |
| New provider support, protocol step, or core/custom topic handling improvement | Minor |
| Breaking schema/location change | Major |

**Authority:** Version helps migration diagnostics; the canonical schema in this file remains the authority.

---

## S8 Port Back to Omnigento

When you improve a core topic, custom-topic handling, or protocol during project work:

1. Update the template text in this file.
2. Update `instruction-style.instructions.md` if provider sync/style rules changed.
3. Bump `meta/VERSION` according to S7.
4. Copy the updated `omnigento/` kit to future projects.

**Omnigento is a living normalizer.** It gets better every time it absorbs a real project cleanly.

---

## S9 Optional Provider Runtime Config Sync

**When:** After instruction setup is complete and the user explicitly asks to sync provider runtime/tool config.

**Separation rule:** Runtime config sync is not part of Bootstrap, Normalize, or Evolution. Keep instruction normalization and MCP/tool config transfer as separate user-visible flows.

**Source baseline:** Use GitHub/Copilot-side project config as the baseline:

- `.github/copilot-instructions.md` and `.github/instructions/*.instructions.md` for instruction intent.
- `.vscode/mcp.json` when present for MCP server definitions.
- `.mcp.json` when present for generic MCP server definitions.

**Provider targets:** Compare and sync repo-local provider runtime config:

| Provider | Runtime config |
|----------|----------------|
| VS Code / GitHub | `.vscode/mcp.json`, `.mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude | `.claude/settings.json`, `.claude/settings.local.json` |
| Codex | `codex mcp list`, user-local `~/.codex/config.toml` |

**Codex rule:** Prefer generating or running `codex mcp add <name> -- <command...>` for Codex MCP parity. Do not directly edit `~/.codex/config.toml` unless the user explicitly requests it.

**Merge rules:**

- Same server name + same transport/command/args/env = match.
- Same server name + different command, args, env, or transport = drift; report before changing.
- Keep prod/test variants separate; never merge names like `service` and `service_test`.
- Preserve SSH args, env vars, paths, server names, and inline credentials exactly unless the user approves a change.
- Report secrets, inline credentials, SSH targets, and production access clearly.

**Completion criteria:**

- Source MCP servers listed.
- Provider coverage table reported for VS Code/GitHub, Cursor, Claude, and Codex.
- Repo-local config files updated when missing/drifted, or conflicts reported.
- Codex commands needed or run are listed.
- Instruction provider files are not polluted with runtime config.
