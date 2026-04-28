---
name: aidlc
description: "AI Development Lifecycle — standardized, version-driven workflow for AI agents developing on codebases. Two modes: (1) Assisted: human drives each phase decision. (2) Autonomous: agent self-directs (declare in task context). On first use, agent analyzes project and generates OPERATIONS.md at root. Each task follows 7 phases: orientation (mandatory summary), design, scratch validation, implementation, testing, documentation, commit. Progress tracked in version log. Use when starting any coding task, refactoring, or bugfix on a codebase."
---

# AIDLC — AI Development Lifecycle

A standardized, version-driven development workflow for AI agents working on codebases.

> Version: 2.3.1

## Core Philosophy

**版本驱动开发 (Version-Driven Development)**

Every development task starts with a version declaration — a version number and a one-line description of what this version delivers. This declaration becomes the anchor for the entire workflow: progress is tracked against it, phases are recorded under it, and the task is not complete until the version is committed.

The version log serves as a living history of the project's evolution, readable by both humans and agents.

## Operating Modes

**Assisted mode** (default): Human drives each phase — version number, descriptions, and approval. Agent executes and reports.

**Autonomous mode**: Agent self-directs when human context is unavailable (e.g. heartbeat-triggered tasks). Agent determines version based on change scope, proceeds without waiting for human input at each phase. Declare in task context: `mode: autonomous`.

## Cross-Session Memory

AI agent conversations are ephemeral — context resets on every new session. AIDLC solves this with two mechanisms:

### Design Notes (`design/todo.md`)

A **private, per-agent** gitignored file that persists **discussion conclusions, design decisions, deferred ideas, and next steps** across sessions. Each agent maintains its own copy — not shared between agents. Multi-agent collaboration uses shared workspaces (e.g. `/tmp/acp-public`) instead.

- Agent **reads** this file in Phase 0 (Orientation) — every new session starts by catching up
- Agent **writes** to this file when preserving context or when a discussion produces decisions worth remembering
- Format: date-stamped sections with tagged items (✅ decided, ⬜ todo, ❌ rejected)

```markdown
## YYYY-MM-DD <topic>

- ✅ Decided to keep X because Y
- ⬜ Refactor Z into shared module
- ❌ Rejected approach A — tested, doesn't work because B
```

### Context Preservation (保护现场)

When the human says **「保护现场」**, **「save context」**, **「先存一下」**, or similar — the agent immediately:

1. **Save code changes**: `git stash` or `git add -A && git commit -m "WIP: <current task>"` — whichever is appropriate
2. **Save discussion context**: append to `design/todo.md` with:
   - Conclusions reached in this session
   - Decisions made and their reasoning
   - Unfinished work and next steps
   - Open questions
3. **Confirm**: report what was saved (stash/commit hash + todo.md summary)

### Setup

On first run, AIDLC adds `design/` to `.gitignore` alongside `OPERATIONS.md` and `versions/`. These are local working files, not committed to the repository.

## First Run

When this skill is activated for the first time on a project:

1. Detect whether this is an **existing project** or a **new (empty) project**
2. Follow the appropriate path below
3. Generate `OPERATIONS.md` at the project root using the template (all 3 parts) → see [references/operations-template.md](references/operations-template.md)
4. Create the `version_log_dir` directory (default: `versions/`)
5. Create `design/` directory with an empty `todo.md`
6. Add `OPERATIONS.md`, `version_log_dir`, and `design/` to `.gitignore`
7. On subsequent tasks, read `OPERATIONS.md` and follow the 7 phases

> `OPERATIONS.md` and `versions/` are local to each developer/agent. They must not be committed unless `version_log_committed: true` is set in OPERATIONS.md Part 1.

### Path A: Existing Project

Analyze the codebase and fill in the template based on what exists.

### Path B: New Project

When the project root is empty (or only has a README / LICENSE):

1. **Ask human** for: project name, language/framework, and purpose (one sentence)
2. Scaffold the minimum viable structure:
   - Package manifest (e.g. `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`)
   - Entry point (e.g. `main.py`, `src/index.ts`)
   - Test directory + one placeholder test
   - `.gitignore` (language-appropriate)
   - `scratch_dir` (gitignored)
   - `versions/` directory (gitignored)
3. Fill `OPERATIONS.md` with the scaffolded paths
4. Commit the scaffold as `v0.1.0: initial scaffold`

> After scaffold, all 7 phases apply normally. The first real task starts at Phase 1.

### Analysis Checklist

When analyzing a project, the agent MUST investigate:

- **Entry point**: what starts the program
- **Version source**: where the canonical version lives
- **Test infrastructure**: runner command, test directory, existing test count/style
- **Build/deploy**: Dockerfile, CI config, Makefile
- **Core modules**: files that >50% of the codebase depends on (these become Protected Files)
- **Infrastructure files**: test helpers, shared utilities, base classes
- **Version sync points**: all files that embed the version string
- **Scratch directory**: existing or conventional location for throwaway code (must be gitignored)
- **Sensitive patterns**: project-specific secrets beyond the defaults

## Version Log System

Each development task produces a version log file in the `version_log_dir` (default: `versions/`).

For format, rules, and lifecycle details → see [references/version-log.md](references/version-log.md)

### Rules

- One file per version, named `v<VERSION>.md`
- Agent creates the file at Phase 1 and updates it at each phase transition
- When Phase 7 completes, status changes to `✅ Committed`, fill in `Completed` timestamp
- If a task is abandoned, status changes to `❌ Abandoned` with reason; uncommitted changes should be reverted or stashed
- `OPERATIONS.md` always reflects the current version being worked on
- **Single-version lock**: only one version may be `in-progress` at a time. Multiple agents must coordinate on the same version, not open parallel versions

## The 7 Phases

```
Phase 0  Orientation        Read OPERATIONS.md, output mandatory summary, review version history
Phase 1  Design & Declare   Declare version + description, plan, create version log
Phase 2  Scratch            Validate MVP in scratch_dir (not committed)
Phase 3  Implement          Minimal code, no side effects
Phase 4  Formal Test        Promote to real tests, full regression
Phase 5  Documentation      Update docs, bump version, sync version
Phase 6  Pre-commit         Tests + build + version sync + secrets scan
Phase 7  Commit & Push      Ship it, close version log
```

### Phase 0: Orientation

Read the project. Understand before you change.

1. Read `OPERATIONS.md` — review project profile, architecture, and read order
2. Read files listed in **Must Read**
3. Check `version_file` — confirm current version
4. Browse `test_dir` — understand existing coverage
5. Check `version_log_dir` — review recent version history for context
6. Read `design/todo.md` — catch up on pending tasks and decisions from previous sessions

**Mandatory output before proceeding to Phase 1:**

```
## Orientation Summary
- Current version: <x.y.z>
- Architecture: <one sentence>
- Protected Files: <list>
- Active version in progress: <version or "none">
```

> Agent MUST output this summary. Cannot proceed to Phase 1 without it.

**Rule: 先读后写，不懂不动。**

### Phase 1: Design — Version Declaration

> **This is where every task begins.** No code without a version.

#### [Optional] Requirement Grill

Before declaring a version, check whether the requirement needs clarification.

**Trigger** (any one):
- User explicitly says "grill me", "clarify task", or similar
- User message is < 20 characters and mentions no specific file or function
- User message contains hedging words (e.g. "大概", "可能", "maybe", "not sure", "看看")

**Skip**: requirement mentions specific files/functions AND the version bump is obvious.

If triggered, ask these 3 questions **one at a time**, give a recommended answer for each:

1. **Scope**: What exactly changes, and what doesn't? (list files + explicit exclusions)
2. **Success criterion**: How do we know this is done? (must be concrete and verifiable)
3. **Risks**: What could go wrong or what edge cases exist?

After answers, output a **complete Phase 1 declaration** (version number, description, file list, Protected Files check, plan) and ask: "Ready to proceed?"
Once confirmed, **skip to step 6 below** (create version log).

If Grill is skipped, follow steps 1–7 normally:

1. **Declare version**: ask human (or determine from context) the target version number
   - patch (x.y.Z): bug fix, config change, docs-only
   - minor (x.Y.0): new feature, non-breaking change
   - major (X.0.0): breaking change, architectural shift
   - when in doubt, ask human
2. **Declare description**: one-line summary of what this version delivers
3. List files to modify
4. Check against **Protected Files** → if hit, **STOP, ask human**
5. Present plan to human
6. **Create version log**: write `<version_log_dir>/v<VERSION>.md` → format in [references/version-log.md](references/version-log.md)
7. **Update Part 2** of `OPERATIONS.md`: version, description, status `in-progress`, current_phase, log_file

### Phase 2: Scratch Validation

Write throwaway code in `scratch_dir` to prove the idea works.

```bash
mkdir -p <scratch_dir>
# write: <scratch_dir>/try_<feature>.sh (or .py, .ts, etc.)
# run:   bash <scratch_dir>/try_<feature>.sh
```

`scratch_dir` is gitignored. Nothing here gets committed.

Goals: prove feasibility, discover integration issues, fail fast.

> **Skip condition (fixed rules only)**:
> - docs-only change (no code modified)
> - single config field change
> - one-line bugfix with obvious cause
>
> Any other change MUST go through Phase 2. Note "Phase 2: skipped — <reason>" in version log.

✏️ Update version log and `OPERATIONS.md` Part 2 current_phase.

### Phase 3: Implement

Minimal code to make it work.

- Only code that directly serves the requirement
- No drive-by refactors
- No test modifications unless human requests
- Keep validating with scratch scripts

✏️ Update version log and `OPERATIONS.md` Part 2 current_phase.

### Phase 4: Formal Test

Promote scratch tests to real tests.

1. Create/update test files in `test_dir` (match existing style)
2. Register in test runner if needed
3. Run full suite — no regressions:
   ```bash
   <test_runner>
   ```
4. If `build_cmd` is set, verify build still works
5. New code failures → fix. Pre-existing flaky → document, don't block.

✏️ Update version log and `OPERATIONS.md` Part 2 current_phase.

### Phase 5: Documentation

1. Update files in `docs` list
2. Update `version_file`
3. Sync version to all `version_sync` files
4. No secrets in any committed file

✏️ Update version log and `OPERATIONS.md` Part 2 current_phase.

### Phase 6: Pre-commit Checklist

All must pass before commit:

```bash
# 1. Full test suite
<test_runner>

# 2. Build (if applicable)
<build_cmd>

# 3. Version consistency
V=$(cat <version_file> | tr -d '[:space:]')
for f in <version_sync>; do
  grep -q "$V" "$f" && echo "✅ $f" || echo "❌ $f"
done

# 4. Secrets scan (built-in defaults + project patterns)
git diff --cached | grep -iE 'token=.{8,}|api[_.]?key=.{8,}|password=|secret=|Bearer .{20,}|<project_sensitive_patterns>' && echo "❌ SECRETS" || echo "✅ Clean"
```

> Built-in sensitive patterns: `token=`, `api_key=`, `api.key=`, `password=`, `secret=`, `Bearer <long>`.
> Add project-specific patterns to `sensitive_patterns` in OPERATIONS.md Part 1.

- [ ] All tests pass
- [ ] Build succeeds (if applicable)
- [ ] Version file updated
- [ ] Version consistent across sync files
- [ ] No secrets in diff
- [ ] `git diff` — no unintended changes

✏️ Update version log and `OPERATIONS.md` Part 2 status to `pre-commit`.

### Phase 7: Commit & Push

```bash
git add -A
git commit -m "v<VERSION>: <description per commit_convention>"
git push
```

After successful push:
1. Version log: status → `✅ Committed`, fill in `Completed` timestamp
2. `OPERATIONS.md` Part 2: reset all fields to empty, status back to `idle`

✏️ Version closed. Next task starts fresh from Phase 0.
