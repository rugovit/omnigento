---
description: "Documentation standards: required sections, writing style, every code file needs matching docs. Use when creating or editing documentation."
applyTo: "<ADAPT: set glob for project's code directories, e.g. src/**/*.py,scripts/**/*.sh>"
---

# Documentation Rules

**Document what AI cannot infer from code.** AI reads code instantly - it does not need function descriptions. What it needs is the intent, failed attempts, and gotchas that shaped the solution.

**Every code file MUST have a matching `.md` file.** Same name, same directory. Every code edit MUST update its `.md` file.

| Section | What goes in it | Required? |
|---------|----------------|-----------|
| **Problem & Intent** | What problem this solves, why it was built | Always |
| **Approach & Why** | Brief how-it-works + why this design over alternatives | Always |
| **What Didn't Work** | Rejected approaches, failed attempts, dead ends | Complex modules |
| **Dependencies** | Other files, services, configs, external tools needed | Always |
| **Usage** | Commands, options, examples | Always |
| **Gotchas** | Production lessons, non-obvious edge cases | When applicable |

**Writing style:** Follow `instruction-style.instructions.md`. Delete any sentence that restates what the code says.

**AI workflow:** Read `.md` before editing code. Update `.md` after editing code.
