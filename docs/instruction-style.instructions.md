---
description: "Style guide for provider-agnostic AI instruction files: topic shape, normalization, provider parity, Codex/Copilot/Claude/Cursor sync, and what to avoid."
applyTo: ".github/instructions/**"
---

# Writing AI Instructions - Style Guide

**Apply these rules when creating, editing, or normalizing files in `.github/instructions/`.**

## DO

- **Bold keywords** at line start as attention anchors (`**NEVER**`, `**DO NOT**`, `**MANDATORY**`)
- **Tables** for structured data, commands, ports, files, tools, services, and provider parity
- **Flat bullet lists** with one rule per line
- **Code blocks** only for commands/templates the AI will copy
- **One sentence per rule** when possible
- **Source project facts** from actual files, configs, scripts, docs, or existing instructions
- **Use ASCII arrows** for flows: `DISCOVER -> PROPOSE -> APPROVE -> GENERATE -> SYNC`
- **Keep files under 120 lines** where possible; split broad topics instead of bloating one file

## DO NOT

- ASCII box-art diagrams
- Emoji in headers or rules
- Nested bullet lists deeper than 2 levels
- Threat paragraphs like "FAILURE TO..."
- Numbered sub-bullets that repeat the same rule
- Verbose introductions or conclusions
- Provider-specific source-of-truth claims outside the Omnigento schema
- Runtime secrets, API keys, MCP config, or editor-local settings

## Principle

Every token should either **state a rule** or **provide reference data the AI cannot infer**. If a sentence does neither, delete it.

---

## File Structure

**Canonical locations (location is the class discriminator):**

- `.github/instructions/<topic>.instructions.md` - file-scoped (with `applyTo:`) or topic-based (`description:` only).
- `.github/instructions/skills/<topic>.instructions.md` - on-request action (skill). `description:` only, no `applyTo:`.

One file per topic. Filename always ends `.instructions.md`.

**YAML frontmatter is mandatory:**

```yaml
---
description: "Short trigger phrase. Use when <specific scenarios>."
applyTo: "glob/pattern/**"   # optional; omit for topic-based or on-request
---
```

| Pattern | Canonical location | When to use | Example |
|---------|-------------------|-------------|---------|
| `applyTo` + `description` | `.github/instructions/` | Rules naturally scoped to files/directories | Plugin rules -> `**/*.cs,plugins/**` |
| `description` only | `.github/instructions/` | Rules loaded by conversation topic | Deployment, server access, API tools |
| `description` only | `.github/instructions/skills/` | User-action triggers; produces a concrete artifact | Generate ban proclamation, render a release note |

**`description` is the discovery surface.** Include trigger words an AI or provider search will actually match. For on-request topics, the description is also what Claude skills and Cursor agent-requested rules use to auto-trigger - phrase it as a user-intent match ("Use when the user asks to...").

---

## Topic Shape

**Start with rules.** Do not spend the first paragraphs explaining why the file exists.

**Use exact facts.** Prefer `./scripts/deploy.sh -n` over "run the deploy script".

**Separate scopes.** If one topic has unrelated globs or workflows, split it.

**Preserve intent.** Include why a rule exists when future AI cannot infer it from code.

**Avoid code restatement.** Do not document what a function/class plainly says.

---

## Normalization Style

**Instruction-Omnigento schema wins.** Existing provider files are source material, not canonical destinations.

**Project facts survive.** Preserve commands, paths, services, ports, safety rules, deployment flows, and naming conventions.

**Provider boilerplate is discarded.** Do not copy redirect text, "source of truth" claims, or duplicated provider wrappers into canonical topics.

**Resolve overlap with Omnigento wording.** If an existing rule duplicates a core Omnigento rule, keep the Omnigento version and add only project-specific detail. If it conflicts with a custom instruction, preserve the explicit project rule and report the custom conflict.

**Report real conflicts.** Do not silently blend contradictory commands, environments, or safety rules.

---

## Provider Parity

### Copilot / Hub

`.github/copilot-instructions.md` is the provider-neutral hub even though the filename is Copilot-specific.

Provider files are generated views, not canonical sources. Do not manually edit generated provider files; edit `.github/instructions/**/*.instructions.md`, then run:

```bash
./omnigento/bin/sync_ai_instructions.py --write
./omnigento/bin/sync_ai_instructions.py --check
```

Projects may add `./omnigento/bin/sync_ai_instructions.py --check` to CI or pre-commit to enforce drift checks, but this is optional.

Generated provider views may inline canonical content for deterministic loading. This improves path-scoped and on-request surfaces, but it does not make topic-based rules universally deterministic; compact topic indexes remain the default unless an explicit future inline-topic mode is enabled.

Every topic gets a row:

| File | Covers | Auto-loads for |
|------|--------|----------------|
| `[topic.instructions.md](.github/instructions/topic.instructions.md)` | One-line scope | Glob or `On-demand` |

### Cursor

Every `applyTo` file gets `.cursor/rules/<name>.mdc` where `<name>` is the **exact** stem of the canonical file (e.g., `documentation-rules.instructions.md` -> `documentation-rules.mdc`, never `documentation.mdc`):

```md
---
globs: "same/glob/pattern"
alwaysApply: false
---
<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/<name>.instructions.md`

<full canonical body>
```

`globs:` must be non-empty and mirror the canonical `applyTo:` value. An empty `globs: ""` is invalid - Cursor parses it as a no-op rule.

**Stem parity is mandatory.** A pointer whose body links to the right canonical but whose own filename diverges is treated as orphan and must be renamed during normalization. Renaming a canonical topic also renames its Cursor pointer.

Topic-based files are indexed in `.cursor/rules/topic-index.mdc`. The topic-index has **no `globs:` key** because it is not file-scoped:

```md
---
alwaysApply: false
---
Topic-based rules live in `.github/instructions/`. Read the relevant file when the topic comes up:

- **Keywords** -> `.github/instructions/<topic>.instructions.md`
```

**Cursor agent-requested rules (on-request)** — every canonical file under `.github/instructions/skills/` gets `.cursor/rules/<name>.mdc` with `description:` and **no `globs:`**. Cursor auto-loads these when the model judges the user's intent matches the description (Cursor's "agent-requested" rule type):

```md
---
description: "<canonical description - phrased as user-intent match>"
alwaysApply: false
---
<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/skills/<name>.instructions.md`

<full canonical body>
```

Stem parity applies the same way (`ban-proclamation.instructions.md` -> `ban-proclamation.mdc`). On-request rules are NOT listed in `topic-index.mdc` - their description is their discovery surface.

### Claude Code

Every `applyTo` file gets `.claude/rules/<name>.md` where `<name>` matches the canonical stem exactly (same parity rule as Cursor). The body carries the full canonical body inline:

```md
---
paths:
  - "same/glob/pattern"
---

# Topic Rules

<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/<name>.instructions.md`

<full canonical body>
```

Topic-based files are indexed in `.claude/rules/topic-index.md`. The topic-index needs no frontmatter - it is plain markdown listing topics:

```md
Topic-based rules live in `.github/instructions/`. Read the relevant file when the topic comes up:

- **Keywords** -> `.github/instructions/<topic>.instructions.md`
```

### Claude Code (skills)

Every canonical file under `.github/instructions/skills/` gets `.claude/skills/<name>/SKILL.md` where `<name>` matches the canonical stem exactly. Claude Code scans skill `description:` frontmatter at session start and auto-fires the skill when the user's message matches.

```md
---
name: <name>
description: <canonical description - phrased as user-intent match>
---

# <Topic>

<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `.github/instructions/skills/<name>.instructions.md`

<full canonical body>
```

**Skills are generated trigger views with inline canonical bodies.** Inline content is allowed only because the compiler owns the file and rewrites it from canonical on every sync. Do not hand-edit skill bodies.

**Stem parity is mandatory.** A skill whose body links to the right canonical but whose folder name diverges is orphan and must be renamed.

**Skills are NOT listed in `.claude/rules/topic-index.md`** - they have their own discovery loop. Listing the same topic in both is a parity violation.

### Agent Markdown

Agent Markdown provider files are `AGENTS.md` files. This shared view applies to tools that read the convention, including Cursor and Codex. It cannot express Cursor `.mdc` frontmatter or Claude skill metadata.

Root `AGENTS.md` points to `.github/copilot-instructions.md` and lists global discovery topics only: topic-based topics and on-request actions.

```md
## Topic-based topics

- **<Keyword group>** -> `.github/instructions/<topic>.instructions.md`

## On-request actions

- **<Keyword group>** -> `.github/instructions/skills/<topic>.instructions.md`
```

The On-request actions section is the agent-markdown substitute for skills/agent-requested rules. The `skills/` path makes the class visually obvious in the listing.

File-scoped topics are not duplicated in root `AGENTS.md`. Cursor and Claude carry native path metadata, the hub table lists every canonical topic, and nested `AGENTS.md` files carry agent-markdown path scope.

Nested `<dir>/AGENTS.md` is generated for every file-scoped topic whose `applyTo` maps cleanly to a directory subtree. Multi-root globs may produce multiple nested files for their concrete directory roots; extension-only fragments stay hub/provider-native. When two file-scoped topics overlap on the same subtree, inline both applicable canonical bodies in one nested file:

```md
# <Directory> Agent Rules

<!-- GENERATED BY omnigento/bin/sync_ai_instructions.py; DO NOT EDIT DIRECTLY -->

Canonical source: `<relative path to repo root>/.github/instructions/<topic>.instructions.md`

<full applicable canonical body>
```

Do not add durable rules directly to `AGENTS.md`; put them in `.github/instructions/`. Generated nested `AGENTS.md` files may inline canonical rules, but `.github/instructions/` remains the source.

---

## Sync Rule

When adding, editing, or removing a topic:

1. Update canonical: `.github/instructions/<topic>.instructions.md` (file-scoped/topic-based) or `.github/instructions/skills/<topic>.instructions.md` (on-request).
2. Run `./omnigento/bin/sync_ai_instructions.py --write`.
3. Run `./omnigento/bin/sync_ai_instructions.py --check`.
4. Inspect the diff before committing or deploying.

The compiler regenerates `.github/copilot-instructions.md` generated blocks, `.cursor/rules/`, `.claude/rules/`, `.claude/skills/`, root `AGENTS.md`, `CLAUDE.md`, and nested `AGENTS.md` files. It removes stale generated provider files when canonical stems disappear. It does not delete unmarked unknown files.

**`CLAUDE.md` and `AGENTS.md`** are generated provider views pointing to the hub - never independent sources of truth. Cursor-specific scoped rules use `.cursor/rules/*.mdc`.

---

## Runtime Config Sync

Runtime config sync is separate from instruction sync. Do not mix MCP server definitions, API keys, SSH commands, or local editor settings into instruction provider files.

When syncing provider runtime config, use GitHub/Copilot-side project config (`.vscode/mcp.json` or `.mcp.json` when present) as the baseline and render provider-specific adapters from that source.

For Codex MCP parity, prefer `codex mcp add` commands over direct edits to `~/.codex/config.toml` unless the user explicitly requests local config edits.
