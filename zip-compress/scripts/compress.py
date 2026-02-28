#!/usr/bin/env python3
"""
Compress files and directories into a ZIP archive.

Usage:
    python3 compress.py <source> <output.zip> [--exclude pattern1,pattern2]

Arguments:
    source      - File or directory to compress
    output      - Output ZIP file path
    --exclude   - Comma-separated patterns to exclude (e.g., "*.log,.git,node_modules")
"""

import argparse
import sys
import zipfile
from pathlib import Path
import fnmatch

def should_exclude(path, exclude_patterns):
    """Check if path matches any exclude pattern."""
    if not exclude_patterns:
        return False
    
    path_str = str(path)
    for pattern in exclude_patterns:
        # Match against filename
        if fnmatch.fnmatch(path.name, pattern):
            return True
        # Match against full path
        if fnmatch.fnmatch(path_str, pattern):
            return True
        # Match against path parts (e.g., ".git" in path)
        if pattern in path.parts:
            return True
    
    return False

def compress_path(source, output, exclude_patterns=None):
    """Compress a file or directory to ZIP."""
    source_path = Path(source).resolve()
    output_path = Path(output).resolve()
    
    # Validate source exists
    if not source_path.exists():
        print(f"Error: Source not found: {source}", file=sys.stderr)
        return False
    
    # Prevent compressing into itself
    if output_path.parent == source_path or output_path == source_path:
        print(f"Error: Cannot compress directory into itself", file=sys.stderr)
        return False
    
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if source_path.is_file():
                # Compress single file
                if should_exclude(source_path, exclude_patterns):
                    print(f"Skipping excluded file: {source_path.name}", file=sys.stderr)
                    return False
                
                zipf.write(source_path, source_path.name)
                print(f"✓ Compressed: {source_path.name}")
                
            elif source_path.is_dir():
                # Compress directory recursively
                file_count = 0
                excluded_count = 0
                
                for item in source_path.rglob('*'):
                    if should_exclude(item, exclude_patterns):
                        excluded_count += 1
                        continue
                    
                    # Get relative path from source
                    arcname = item.relative_to(source_path)
                    
                    if item.is_file():
                        zipf.write(item, arcname)
                        file_count += 1
                    elif item.is_dir():
                        # Add empty directories
                        zipf.write(item, arcname)
                
                print(f"✓ Compressed: {file_count} files from {source_path.name}/")
                if excluded_count > 0:
                    print(f"  Excluded: {excluded_count} items")
        
        # Show output file size
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✓ Created: {output_path} ({size_mb:.2f} MB)")
        return True
        
    except Exception as e:
        print(f"Error compressing: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Compress files/directories to ZIP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 compress.py myfile.txt archive.zip
  python3 compress.py myproject/ project.zip
  python3 compress.py src/ backup.zip --exclude "*.log,.git,node_modules"
        """
    )
    parser.add_argument('source', help='File or directory to compress')
    parser.add_argument('output', help='Output ZIP file')
    parser.add_argument('--exclude', help='Comma-separated exclude patterns')
    
    args = parser.parse_args()
    
    # Parse exclude patterns
    exclude_patterns = None
    if args.exclude:
        exclude_patterns = [p.strip() for p in args.exclude.split(',')]
        print(f"Exclude patterns: {', '.join(exclude_patterns)}")
    
    # Compress
    success = compress_path(args.source, args.output, exclude_patterns)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
