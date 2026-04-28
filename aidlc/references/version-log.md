# Version Log System

Each development task produces a version log file in the `version_log_dir` (default: `versions/`).

By default `versions/` is gitignored. Set `version_log_committed: true` in OPERATIONS.md Part 1 to commit version logs to the repository (recommended for teams and open source projects).

## Directory Structure

```
versions/
├── v1.2.0.md        # completed
├── v1.2.1.md        # completed
└── v1.3.0.md        # in progress (current)
```

## Version Log File Format

Created at Phase 1 (Design), updated as each phase completes:

```markdown
# v<VERSION> — <one-line description>

- Started: <timestamp>
- Completed: <timestamp or ->
- Status: 🔄 In Progress | ✅ Committed | ❌ Abandoned

## Plan

- Files to modify: <list>
- Risk: <protected files hit? Y/N>
- Phase 2 skip: <yes — reason | no>

## Progress

- [x] Phase 0: Orientation — <timestamp>
- [x] Phase 1: Design — <timestamp>
- [ ] Phase 2: Scratch — <timestamp or "skipped: <reason>">
- [ ] Phase 3: Implement
- [ ] Phase 4: Test
- [ ] Phase 5: Docs
- [ ] Phase 6: Pre-commit
- [ ] Phase 7: Commit

## Notes

<anything noteworthy during development — blockers, decisions, deviations>
```

## Rules

- One file per version, named `v<VERSION>.md`
- Agent creates the file at Phase 1 and updates it at each phase transition
- When Phase 7 completes, status changes to `✅ Committed`, fill in `Completed` timestamp
- If a task is abandoned, status changes to `❌ Abandoned` with reason in Notes; uncommitted changes should be reverted or stashed
- `OPERATIONS.md` always reflects the current version being worked on
- **Single-version lock**: only one version may be `in-progress` at a time. Multiple agents must coordinate on the same version — no parallel versions on the same branch
- Phase 2 skip must be recorded explicitly in the version log with the rule that applies

## Version Log Lifecycle

```
Phase 1 ──→ CREATE version log (status: 🔄 In Progress)
            ↓
Phase 2-6 → UPDATE progress checkboxes + timestamps
            ↓
Phase 7 ──→ CLOSE version log (status: ✅ Committed)
            ↓
         ──→ RESET OPERATIONS.md Part 2 to idle
            ↓
         ──→ if version_log_committed: git add versions/vX.Y.Z.md && commit --amend
```
