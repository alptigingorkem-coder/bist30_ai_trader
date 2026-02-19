#!/usr/bin/env python3
"""Find unused Python files in the project.

This script scans all Python files in the project and identifies files that are
not imported by any other file. It helps identify dead code and opportunities
for cleanup.

Usage:
    python scripts/maintenance/find_unused_files.py [--root PATH] [--json OUTPUT]
    
Examples:
    # Scan current directory
    python scripts/maintenance/find_unused_files.py
    
    # Scan specific directory
    python scripts/maintenance/find_unused_files.py --root scripts/
    
    # Export results to JSON
    python scripts/maintenance/find_unused_files.py --json unused_files.json
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.maintenance.core import (
    CleanupConfig,
    FileScanner,
    UnusedFileDetector
)


def format_unused_file(file_info, index):
    """Format an unused file for console output."""
    lines = []
    lines.append(f"\n{index + 1}. {file_info.path}")
    lines.append(f"   Lines: {file_info.lines} (code: {file_info.code_lines})")
    lines.append(f"   Last modified: {file_info.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if file_info.functions:
        lines.append(f"   Functions: {', '.join(file_info.functions[:5])}")
        if len(file_info.functions) > 5:
            lines.append(f"              ... and {len(file_info.functions) - 5} more")
    
    if file_info.classes:
        lines.append(f"   Classes: {', '.join(file_info.classes[:5])}")
        if len(file_info.classes) > 5:
            lines.append(f"            ... and {len(file_info.classes) - 5} more")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Find unused Python files in the project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--root',
        type=Path,
        default=Path.cwd(),
        help='Root directory to scan (default: current directory)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to cleanup configuration file'
    )
    
    parser.add_argument(
        '--json',
        type=Path,
        help='Export results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Create scanner and detector
    scanner = FileScanner(config)
    detector = UnusedFileDetector(config, scanner)
    
    # Find unused files
    print(f"Scanning for unused files in: {args.root}")
    print()
    
    result = detector.find_unused_files(args.root)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"UNUSED FILE DETECTION RESULTS")
    print(f"{'='*80}")
    print(f"Total files scanned: {len(result.import_graph)}")
    print(f"Special files (excluded): {len(result.special_files)}")
    print(f"Unused files found: {len(result.unused_files)}")
    
    if result.unused_files:
        percentage = (len(result.unused_files) / len(result.import_graph)) * 100
        print(f"Percentage unused: {percentage:.1f}%")
        
        print(f"\n{'='*80}")
        print(f"UNUSED FILES")
        print(f"{'='*80}")
        
        for i, file_info in enumerate(result.unused_files):
            print(format_unused_file(file_info, i))
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Found {len(result.unused_files)} unused files")
        print(f"\nRecommendation: Review these files to determine if they can be")
        print(f"safely removed or if they serve a purpose not detected by import analysis.")
        print(f"\nNote: Files like __init__.py, __main__.py, setup.py, and top-level")
        print(f"scripts are automatically excluded as they serve special purposes.")
    else:
        print("\nNo unused files found! All Python files are imported somewhere.")
    
    # Export to JSON if requested
    if args.json:
        detector.export_json(result, args.json)
        print(f"\nResults exported to: {args.json}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
