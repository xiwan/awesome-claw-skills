---
name: aidlc
description: "AI Development Lifecycle — standardized workflow for AI agents developing on codebases. Covers orientation, design, scratch validation, implementation, testing, documentation, and commit. Drop into any project. Agent auto-fills project-specific config on first run."
---

# AIDLC — AI Development Lifecycle

A standardized development workflow for AI agents working on codebases.

> Version: 1.0.0

## How to Use

1. Copy this `SKILL.md` to your project (e.g. `.kiro/skills/aidlc/SKILL.md`)
2. Agent fills in the `<!-- PROJECT -->` sections on first run
3. Agent reads this file at the start of every task

---

<!-- PROJECT: Agent auto-populates on first encounter based on codebase analysis -->
## Project Profile

```yaml
name: ""
version_file: ""              # e.g. VERSION, package.json, Cargo.toml
entry_point: ""               # e.g. main.py, src/index.ts
test_runner: ""               # e.g. bash test/test.sh, npm test, pytest
test_dir: ""                  # e.g. test/, tests/, __tests__/
scratch_dir: ""               # e.g. test/scratch/ (must be gitignored)
docs: []                      # files to update per release
version_sync: []              # files whose version must match version_file
commit_convention: ""         # e.g. conventional, semver-prefix, free-form
```

<!-- PROJECT: Agent auto-populates on first encounter -->
## Read Order

Files to read (in order) to understand the codebase:

```
1.
2.
3.
```

<!-- PROJECT: Agent auto-populates on first encounter -->
## Protected Files

Modifying these requires **human confirmation**:

| File | Reason |
|------|--------|

<!-- PROJECT: Agent may extend with project-specific patterns -->
## Sensitive Patterns

Reject commit if these appear in diff:

```
token=.{8,}
api.key=.{8,}
password=
secret=
```

---

## The 7 Phases

### Phase 0: Orientation

Read the project. Understand before you change.

1. Read files in **Read Order**
2. Check `version_file` — confirm current version
3. Browse `test_dir` — understand existing coverage
4. If **Project Profile** is empty → analyze codebase and fill it in

**Rule: 先读后写，不懂不动。**

### Phase 1: Design

1. One-line description of the feature/fix
2. List files to modify
3. Check against **Protected Files** → if hit, **STOP, ask human**
4. Determine new version number
5. Present plan to human

### Phase 2: Scratch Validation

Write throwaway code in `scratch_dir` to prove the idea works.

```bash
mkdir -p <scratch_dir>
# write: <scratch_dir>/try_<feature>.sh
# run:   bash <scratch_dir>/try_<feature>.sh
```

`scratch_dir` is gitignored. Nothing here gets committed.

Goals: prove feasibility, discover integration issues, fail fast.

### Phase 3: Implement

Minimal code to make it work.

- Only code that directly serves the requirement
- No drive-by refactors
- No test modifications unless human requests
- Keep validating with scratch scripts

### Phase 4: Formal Test

Promote scratch tests to real tests.

1. Create/update test files in `test_dir` (match existing style)
2. Register in test runner if needed
3. Run full suite — no regressions:
   ```bash
   <test_runner>
   ```
4. New code failures → fix. Pre-existing flaky → document, don't block.

### Phase 5: Documentation

1. Update files in `docs` list
2. Update `version_file`
3. No secrets in any committed file

### Phase 6: Pre-commit Checklist

All must pass before commit:

```bash
# 1. Full test suite
<test_runner>

# 2. Version consistency
V=$(cat <version_file> | tr -d '[:space:]')
for f in <version_sync>; do
  grep -q "$V" "$f" && echo "✅ $f" || echo "❌ $f"
done

# 3. Secrets scan
git diff --cached | grep -iE '<sensitive_patterns>' && echo "❌ SECRETS" || echo "✅ Clean"
```

- [ ] All tests pass
- [ ] Version file updated
- [ ] Version consistent across sync files
- [ ] No secrets in diff
- [ ] `git diff` — no unintended changes

### Phase 7: Commit & Push

```bash
git add -A
git commit -m "<message per commit_convention>"
git push
```

---

## Quick Reference

```
Phase 0  Orientation     Read code, understand context
Phase 1  Design          Plan, identify risks, get human approval
Phase 2  Scratch         Validate MVP in scratch_dir (not committed)
Phase 3  Implement       Minimal code, no side effects
Phase 4  Formal Test     Promote to real tests, full regression
Phase 5  Documentation   Update docs, bump version
Phase 6  Pre-commit      Tests + version sync + secrets scan
Phase 7  Commit & Push   Ship it
```
