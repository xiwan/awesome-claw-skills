# Version Log System

Each development task produces a version log file in the `version_log_dir` (default: `versions/`).

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

## Progress

- [x] Phase 0: Orientation
- [x] Phase 1: Design — <timestamp>
- [x] Phase 2: Scratch — <timestamp>
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
- If a task is abandoned (human says stop, or approach is unviable), status changes to `❌ Abandoned` with a reason in Notes; any uncommitted changes should be reverted or stashed
- `OPERATIONS.md` always reflects the current version being worked on
- **Single-version lock**: only one version may be `in-progress` at a time. To start a new version, the current one must be committed or abandoned first

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
