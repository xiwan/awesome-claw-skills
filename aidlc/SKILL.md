---
name: aidlc
description: "AI Development Lifecycle — standardized, version-driven workflow for AI agents developing on codebases. On first use, agent analyzes the project and generates OPERATIONS.md at project root. Each development task begins with a version declaration, tracked through 7 phases: orientation, design, scratch validation, implementation, testing, documentation, and commit. Progress is recorded in a dedicated version log directory."
---

# AIDLC — AI Development Lifecycle

A standardized, version-driven development workflow for AI agents working on codebases.

> Version: 2.1.0

## Core Philosophy

**版本驱动开发 (Version-Driven Development)**

Every development task starts with a version declaration — a version number and a one-line description. This declaration anchors the entire workflow: progress is tracked against it, phases are recorded under it, and the task is not complete until the version is committed.

## Cross-Session Memory

### Design Notes (`design/todo.md`)

A gitignored file that persists discussion conclusions, design decisions, deferred ideas, and next steps across sessions.

- Agent **reads** in Phase 0 — every new session starts by catching up
- Agent **writes** when preserving context or when discussions produce decisions worth remembering
- Format: date-stamped sections with tagged items (✅ decided, ⬜ todo, ❌ rejected)

```markdown
## YYYY-MM-DD <topic>

- ✅ Decided to keep X because Y
- ⬜ Refactor Z into shared module
- ❌ Rejected approach A — tested, doesn't work because B
```

### Context Preservation (保护现场)

When the human says **"保护现场"**, **"save context"**, **"先存一下"** — the agent immediately:

1. **Save code**: `git stash` or `git add -A && git commit -m "WIP: <current task>"`
2. **Save context**: append to `design/todo.md` — conclusions, decisions, next steps, open questions
3. **Confirm**: report what was saved (stash/commit hash + todo.md summary)

## First Run

1. Detect **existing project** vs **new (empty) project**
2. Generate `OPERATIONS.md` using template → see [references/operations-template.md](references/operations-template.md)
3. Create `versions/` directory and `design/todo.md`
4. Add `OPERATIONS.md`, `versions/`, `design/` to `.gitignore`

> `OPERATIONS.md` and `versions/` are local to each developer/agent. They must not be committed.

### Path A: Existing Project — analyze codebase, fill template

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

### Analysis Checklist

Agent MUST investigate: entry point, version source, test infrastructure, build/deploy, core modules (→ Protected Files), infrastructure files, version sync points, scratch directory, sensitive patterns.

## The 7 Phases

```
Phase 0  Orientation        Read OPERATIONS.md, design/todo.md, understand context
Phase 1  Design & Declare   Declare version + description, plan, create version log
Phase 2  Scratch            Validate in scratch_dir (skip if trivial)
Phase 3  Implement          Minimal code, no side effects
Phase 4  Formal Test        Promote to real tests, full regression
Phase 5  Documentation      Update docs, bump version, sync version
Phase 6  Pre-commit         Tests + build + version sync + secrets scan
Phase 7  Commit & Push      Ship it, close version log
```

### Phase 0: Orientation

Read the project. **先读后写，不懂不动。**

1. Read `OPERATIONS.md` — profile, architecture, read order
2. Read **Must Read** files
3. Check `version_file` — confirm current version
4. Browse `test_dir` — understand coverage
5. Check `version_log_dir` — recent version history
6. Read `design/todo.md` — catch up from previous sessions

> **Hot start**: if previous version was just committed this session, skim steps 1–4.

### Phase 1: Design — Version Declaration

> **No code without a version.**

1. Declare version (patch/minor/major — when in doubt, ask human)
2. Declare description (one-line)
3. List files to modify
4. Check **Protected Files** → if hit, **STOP, ask human**
5. Present plan to human
6. Create version log → see [references/version-log.md](references/version-log.md)
7. Update `OPERATIONS.md` Part 2: status `in-progress`

✏️ Create version log file.

### Phase 2: Scratch Validation

Write throwaway code in `scratch_dir` to prove the idea works.

```bash
mkdir -p <scratch_dir>
# write: <scratch_dir>/try_<feature>.sh (or .py, .ts, etc.)
# run and verify
```

`scratch_dir` is gitignored. Nothing here gets committed.

> **Skip condition**: trivial changes → note "Phase 2: skipped (trivial)" in version log.

✏️ Update version log: check off Phase 2, add timestamp.

### Phase 3: Implement

Minimal code. No drive-by refactors. No test modifications unless human requests. Keep validating with scratch scripts.

✏️ Update version log: check off Phase 3, add timestamp.

### Phase 4: Formal Test

Promote scratch tests to real tests. Run full suite — no regressions. New failures → fix. Pre-existing flaky → document, don't block.

✏️ Update version log: check off Phase 4, record test results in Notes.

### Phase 5: Documentation

Update docs, `version_file`, sync version to all `version_sync` files. No secrets in committed files.

✏️ Update version log: check off Phase 5.

### Phase 6: Pre-commit Checklist

All must pass: tests ✓ build ✓ version consistency ✓ secrets scan ✓ no unintended changes ✓

✏️ Update version log: check off Phase 6. Set `OPERATIONS.md` Part 2 status to `pre-commit`.

### Phase 7: Commit & Push

Commit, close version log (status → `✅ Committed`), reset `OPERATIONS.md` Part 2 to `idle`.

✏️ Version closed. Next task starts fresh from Phase 0.

## Version Log

One file per version in `versions/v<VERSION>.md`. Single-version lock: only one `in-progress` at a time.

Details and template → [references/version-log.md](references/version-log.md)

## Reference Docs

- [references/operations-template.md](references/operations-template.md) — OPERATIONS.md 完整模板（首次运行时使用）
- [references/version-log.md](references/version-log.md) — 版本日志格式、规则、生命周期
