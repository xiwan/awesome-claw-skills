---
name: zip-compress
description: Compress files and directories into ZIP archives. Use when the user asks to compress, zip, or archive files or folders. Supports excluding patterns like .git, node_modules, or specific file types.
---

# ZIP Compress

Compress files and directories into ZIP archives with optional exclude patterns.

## Quick Start

Compress a single file:

```bash
python3 scripts/compress.py document.pdf archive.zip
```

Compress a directory:

```bash
python3 scripts/compress.py myproject/ project.zip
```

Compress with exclusions:

```bash
python3 scripts/compress.py src/ backup.zip --exclude "*.log,.git,node_modules"
```

## Parameters

- `source` (required): File or directory path to compress
- `output` (required): Output ZIP file path
- `--exclude` (optional): Comma-separated patterns to exclude

## Exclude Patterns

The `--exclude` option accepts multiple patterns separated by commas:

### Pattern Types

1. **Exact names**: `node_modules`, `.git`, `.DS_Store`
2. **Wildcards**: `*.log`, `*.tmp`, `test_*`
3. **Path patterns**: `**/cache/*`, `build/*`

### Common Examples

**Development projects:**
```bash
--exclude ".git,node_modules,__pycache__,*.pyc,.venv"
```

**Build artifacts:**
```bash
--exclude "dist,build,target,*.o,*.class"
```

**Temporary files:**
```bash
--exclude "*.tmp,*.log,*.cache,temp,tmp"
```

**macOS/system files:**
```bash
--exclude ".DS_Store,.Spotlight-V100,.Trashes"
```

## Common Patterns

### User wants to compress a directory

When the user says "compress this folder" or "zip this project":
1. Determine the source directory
2. Generate output filename (e.g., `{dirname}.zip` or `archive.zip`)
3. Ask if they want to exclude common patterns (node_modules, .git, etc.)

### User wants to compress specific files

For "zip these files," collect all file paths and use a directory that contains them, or compress them individually.

### Exclude patterns needed

When compressing development projects, proactively suggest excluding build artifacts and dependencies unless user explicitly wants them.

## Output

The script reports:
- Number of files compressed (for directories)
- Number of items excluded (if any)
- Output file path and size

Example output:
```
Exclude patterns: *.log, .git, node_modules
✓ Compressed: 127 files from myproject/
  Excluded: 3,482 items
✓ Created: /path/to/myproject.zip (2.34 MB)
```

## Error Handling

**Source not found**: Verify the path exists before calling the script.

**Cannot compress into itself**: Ensure output path is not inside the source directory.

**Permission denied**: Check file/directory permissions.

## Technical Details

- Uses Python's `zipfile` with `ZIP_DEFLATED` compression
- Preserves directory structure
- Includes empty directories
- Cross-platform compatible (Windows/Linux/macOS)
- No external dependencies (Python 3 standard library only)
