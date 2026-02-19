#!/usr/bin/env python3
"""Find small files across the project.

This script scans all Python files in the project and identifies files
with fewer than 100 lines of code (configurable threshold). Small files
may be candidates for merging to improve code cohesion.

Usage:
    python scripts/maintenance/find_small_files.py [--root PATH] [--json OUTPUT]
    
Examples:
    # Scan current directory
    python scripts/maintenance/find_small_files.py
    
    # Scan specific directory
    python scripts/maintenance/find_small_files.py --root scripts/
    
    # Export results to JSON
    python scripts/maintenance/find_small_files.py --json small_files.json
    
    # Use custom threshold
    python scripts/maintenance/find_small_files.py --threshold 150
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.maintenance.core import (
    CleanupConfig,
    FileScanner,
    FileSizeAnalyzer
)


def format_directory_group(directory, files):
    """Format a directory group for console output."""
    lines = []
    lines.append(f"\n{directory}/")
    lines.append("-" * 80)
    
    # Sort files by size (smallest first)
    sorted_files = sorted(files, key=lambda f: f.code_lines)
    
    for file_info in sorted_files:
        rel_path = file_info.path.name
        lines.append(f"  {rel_path:50s} {file_info.code_lines:4d} lines")
    
    total_lines = sum(f.code_lines for f in files)
    lines.append(f"\n  Total: {len(files)} files, {total_lines} lines")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Find small Python files that may be candidates for merging',
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
    
    parser.add_argument(
        '--threshold',
        type=int,
        help='Small file threshold in lines (default from config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Override threshold if specified
    if args.threshold is not None:
        if args.threshold <= 0:
            print("Error: Threshold must be positive", file=sys.stderr)
            return 1
        config._config['thresholds']['small_file_lines'] = args.threshold
    
    # Create scanner and analyzer
    scanner = FileScanner(config)
    analyzer = FileSizeAnalyzer(config, scanner)
    
    # Analyze file sizes
    print(f"Scanning for small files in: {args.root}")
    print(f"Small file threshold: {config.small_file_threshold} lines")
    print()
    
    result = analyzer.analyze_sizes(args.root)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"SMALL FILE DETECTION RESULTS")
    print(f"{'='*80}")
    print(f"Total small files found: {len(result.small_files)}")
    print(f"Average file size: {result.average_size:.1f} lines")
    print(f"Median file size: {result.median_size:.1f} lines")
    
    if result.small_files:
        # Group by directory
        grouped = analyzer.group_by_directory(result.small_files)
        
        print(f"\nSmall files grouped by directory:")
        print(f"{'='*80}")
        
        # Sort directories by number of files (most files first)
        sorted_dirs = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
        
        for directory, files in sorted_dirs:
            print(format_directory_group(directory, files))
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Found {len(result.small_files)} small files across {len(grouped)} directories")
        
        # Calculate potential merge candidates
        merge_candidates = sum(1 for files in grouped.values() if len(files) > 1)
        print(f"Directories with multiple small files: {merge_candidates}")
        
        print(f"\nRecommendation: Consider merging related small files in the same")
        print(f"directory to improve code cohesion. Use suggest_merges.py for")
        print(f"detailed merge suggestions.")
    else:
        print("\nNo small files found! All files meet the minimum size threshold.")
    
    # Show size distribution
    print(f"\n{'='*80}")
    print(f"FILE SIZE DISTRIBUTION")
    print(f"{'='*80}")
    for size_range, count in result.size_distribution.items():
        bar = '█' * (count // 2) if count > 0 else ''
        print(f"{size_range:12s} lines: {count:3d} files {bar}")
    
    # Export to JSON if requested
    if args.json:
        analyzer.export_json(result, args.json)
        print(f"\nResults exported to: {args.json}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
