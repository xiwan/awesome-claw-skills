---
name: aidlc
description: "AI Development Lifecycle — standardized, version-driven workflow for AI agents developing on codebases. On first use, agent analyzes the project and generates OPERATIONS.md at project root. Each development task begins with a version declaration, tracked through 7 phases: orientation, design, scratch validation, implementation, testing, documentation, and commit. Progress is recorded in a dedicated version log directory."
---

# AIDLC — AI Development Lifecycle

A standardized, version-driven development workflow for AI agents working on codebases.

> Version: 2.1.0

## Core Philosophy

**版本驱动开发 (Version-Driven Development)**

Every development task starts with a version declaration — a version number and a one-line description of what this version delivers. This declaration becomes the anchor for the entire workflow: progress is tracked against it, phases are recorded under it, and the task is not complete until the version is committed.

The version log serves as a living history of the project's evolution, readable by both humans and agents.

## Cross-Session Memory

AI agent conversations are ephemeral — context resets on every new session. AIDLC solves this with two mechanisms:

### Design Notes (`design/todo.md`)

A gitignored file that persists **discussion conclusions, design decisions, deferred ideas, and next steps** across sessions. This is the agent's long-term memory for the project.

- Agent **reads** this file in Phase 0 (Orientation) — every new session starts by catching up
- Agent **writes** to this file when preserving context (see below) or when a discussion produces decisions worth remembering
- Format: date-stamped sections with tagged items (✅ decided, ⬜ todo, ❌ rejected)

```markdown
## YYYY-MM-DD <topic>

- ✅ Decided to keep X because Y
- ⬜ Refactor Z into shared module
- ❌ Rejected approach A — tested, doesn't work because B
```

### Context Preservation (保护现场)

When the human says **"保护现场"**, **"save context"**, **"先存一下"**, or similar — the agent immediately:

1. **Save code changes**: `git stash` or `git add -A && git commit -m "WIP: <current task>"` — whichever is appropriate
2. **Save discussion context**: append to `design/todo.md` with:
   - Conclusions reached in this session
   - Decisions made and their reasoning
   - Unfinished work and next steps
   - Open questions
3. **Confirm**: report what was saved (stash/commit hash + todo.md summary)

This ensures nothing is lost when a session ends unexpectedly, the human switches tasks, or context window fills up.

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

> `OPERATIONS.md` and `versions/` are local to each developer/agent. They must not be committed.

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

- **Entry point**: what starts the program (`main.py`, `src/index.ts`, `cmd/main.go`, etc.)
- **Version source**: where the canonical version lives (`VERSION`, `package.json:version`, `Cargo.toml`, `pyproject.toml`, etc.)
- **Test infrastructure**: runner command, test directory, existing test count/style
- **Build/deploy**: Dockerfile, CI config, Makefile — anything that breaks if code changes
- **Core modules**: files that >50% of the codebase depends on (these become Protected Files)
- **Infrastructure files**: test helpers, shared utilities, base classes — breakage cascades silently
- **Version sync points**: all files that embed the version string (README changelog, skill files, pyproject.toml, etc.)
- **Scratch directory**: existing or conventional location for throwaway code (must be gitignored)
- **Sensitive patterns**: project-specific secrets beyond the defaults (API keys, tokens, credentials)

## Version Log System

Each development task produces a version log file in the `version_log_dir` (default: `versions/`).

For format, rules, and lifecycle details → see [references/version-log.md](references/version-log.md)

### Directory Structure

```
versions/
├── v1.2.0.md        # completed
├── v1.2.1.md        # completed
└── v1.3.0.md        # in progress (current)
```

### Rules

- One file per version, named `v<VERSION>.md`
- Agent creates the file at Phase 1 and updates it at each phase transition
- When Phase 7 completes, status changes to `✅ Committed`, fill in `Completed` timestamp
- If a task is abandoned (human says stop, or approach is unviable), status changes to `❌ Abandoned` with a reason in Notes; any uncommitted changes should be reverted or stashed
- `OPERATIONS.md` always reflects the current version being worked on
- **Single-version lock**: only one version may be `in-progress` at a time. To start a new version, the current one must be committed or abandoned first

## The 7 Phases

```
Phase 0  Orientation        Read OPERATIONS.md, understand context, review version history
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
6. Read `design/todo.md` — catch up on pending tasks, decisions, and deferred ideas from previous sessions

> **Hot start**: if the previous version was just committed in this session, steps 1–4 can be skimmed rather than fully re-read.

**Rule: 先读后写，不懂不动。**

### Phase 1: Design — Version Declaration

> **This is where every task begins.** No code without a version.

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

> **Skip condition**: trivial changes (one-line fix, docs-only, config tweak) may skip this phase. Note "Phase 2: skipped (trivial)" in version log.

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
4. If `build_cmd` is set, verify build still works:
   ```bash
   <build_cmd>
   ```
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

# 4. Secrets scan
git diff --cached | grep -iE '<sensitive_patterns>' && echo "❌ SECRETS" || echo "✅ Clean"
```

- [ ] All tests pass
- [ ] Build succeeds (if applicable)
- [ ] Version file updated
- [ ] Version consistent across sync files
- [ ] No secrets in diff
- [ ] `git diff` — no unintended changes

✏️ Update version log, set `OPERATIONS.md` Part 2 status to `pre-commit`.

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

## Version Log Lifecycle

```
Phase 1 ──→ CREATE version log (status: 🔄 In Progress)
            ↓
Phase 2-6 → UPDATE progress checkboxes + timestamps
            ↓
Phase 7 ──→ CLOSE version log (status: ✅ Committed)
            ↓
         ──→ RESET OPERATIONS.md Part 2 to idle
```
