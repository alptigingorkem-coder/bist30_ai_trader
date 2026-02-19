#!/usr/bin/env python3
"""Find large files across the project.

This script scans all Python files in the project and identifies files
with more than 500 lines of code (configurable threshold). Large files
may be candidates for splitting to improve maintainability.

Usage:
    python scripts/maintenance/find_large_files.py [--root PATH] [--json OUTPUT]
    
Examples:
    # Scan current directory
    python scripts/maintenance/find_large_files.py
    
    # Scan specific directory
    python scripts/maintenance/find_large_files.py --root scripts/
    
    # Export results to JSON
    python scripts/maintenance/find_large_files.py --json large_files.json
    
    # Use custom threshold
    python scripts/maintenance/find_large_files.py --threshold 600
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


def format_large_file(file_info, analyzer):
    """Format a large file entry for console output."""
    lines = []
    lines.append(f"\n{'-'*80}")
    lines.append(f"File: {file_info.path}")
    lines.append(f"Size: {file_info.code_lines} lines of code ({file_info.lines} total lines)")
    lines.append(f"Last modified: {file_info.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get split point suggestions
    split_points = analyzer.suggest_split_points(file_info)
    
    if split_points:
        lines.append(f"\nSuggested split points (line numbers):")
        for i, line_num in enumerate(split_points, 1):
            lines.append(f"  Split {i}: Line {line_num}")
        
        # Calculate approximate sizes if split
        all_points = [1] + split_points + [file_info.lines]
        segment_sizes = []
        for i in range(len(all_points) - 1):
            size = all_points[i + 1] - all_points[i]
            segment_sizes.append(size)
        
        lines.append(f"\nApproximate segment sizes after split:")
        for i, size in enumerate(segment_sizes, 1):
            lines.append(f"  Segment {i}: ~{size} lines")
    else:
        lines.append(f"\nNo clear split points identified.")
        lines.append(f"Consider manually reviewing the file structure.")
    
    # Show file structure summary
    if file_info.classes or file_info.functions:
        lines.append(f"\nFile structure:")
        if file_info.classes:
            lines.append(f"  Classes: {len(file_info.classes)} ({', '.join(file_info.classes[:5])}" + 
                        (f", ..." if len(file_info.classes) > 5 else "") + ")")
        if file_info.functions:
            lines.append(f"  Functions: {len(file_info.functions)} ({', '.join(file_info.functions[:5])}" + 
                        (f", ..." if len(file_info.functions) > 5 else "") + ")")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Find large Python files that may be candidates for splitting',
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
        help='Large file threshold in lines (default from config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Override threshold if specified
    if args.threshold is not None:
        if args.threshold <= 0:
            print("Error: Threshold must be positive", file=sys.stderr)
            return 1
        config._config['thresholds']['large_file_lines'] = args.threshold
    
    # Create scanner and analyzer
    scanner = FileScanner(config)
    analyzer = FileSizeAnalyzer(config, scanner)
    
    # Analyze file sizes
    print(f"Scanning for large files in: {args.root}")
    print(f"Large file threshold: {config.large_file_threshold} lines")
    print()
    
    result = analyzer.analyze_sizes(args.root)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"LARGE FILE DETECTION RESULTS")
    print(f"{'='*80}")
    print(f"Total large files found: {len(result.large_files)}")
    print(f"Average file size: {result.average_size:.1f} lines")
    print(f"Median file size: {result.median_size:.1f} lines")
    
    if result.large_files:
        # Sort by size (largest first)
        sorted_files = sorted(result.large_files, key=lambda f: f.code_lines, reverse=True)
        
        print(f"\nLarge files (sorted by size):")
        print(f"{'='*80}")
        
        for file_info in sorted_files:
            print(format_large_file(file_info, analyzer))
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Found {len(result.large_files)} large files")
        
        # Calculate statistics
        total_lines = sum(f.code_lines for f in result.large_files)
        avg_large_size = total_lines / len(result.large_files)
        largest_file = sorted_files[0]
        
        print(f"Total lines in large files: {total_lines}")
        print(f"Average large file size: {avg_large_size:.1f} lines")
        print(f"Largest file: {largest_file.path} ({largest_file.code_lines} lines)")
        
        print(f"\nRecommendation: Consider splitting large files at the suggested")
        print(f"split points to improve maintainability. Each split should create")
        print(f"cohesive modules with clear responsibilities.")
    else:
        print("\nNo large files found! All files are within the size threshold.")
    
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
