#!/usr/bin/env python3
"""Find duplicate code across the project.

This script scans all Python files in the project and identifies functions
with identical or near-identical implementations. It helps identify opportunities
for code consolidation and shared utility creation.

Usage:
    python scripts/maintenance/find_duplicate_code.py [--root PATH] [--json OUTPUT]
    
Examples:
    # Scan current directory
    python scripts/maintenance/find_duplicate_code.py
    
    # Scan specific directory
    python scripts/maintenance/find_duplicate_code.py --root scripts/
    
    # Export results to JSON
    python scripts/maintenance/find_duplicate_code.py --json duplicates.json
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.maintenance.core import (
    CleanupConfig,
    FileScanner,
    DuplicateCodeDetector
)


def format_duplicate_group(group, index):
    """Format a duplicate group for console output."""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"Duplicate Group #{index + 1}: {group.function_name}")
    lines.append(f"{'='*80}")
    lines.append(f"Similarity: {group.similarity:.2%}")
    lines.append(f"Instances: {len(group.locations)}")
    lines.append(f"\nLocations:")
    
    for file_path, line_num in group.locations:
        lines.append(f"  - {file_path}:{line_num}")
    
    lines.append(f"\nSuggested shared location: {group.suggested_location}")
    lines.append(f"\nCode snippet:")
    lines.append("-" * 80)
    lines.append(group.code_snippet)
    lines.append("-" * 80)
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Find duplicate code across Python files',
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
        type=float,
        help='Similarity threshold (0.0-1.0, default from config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Override threshold if specified
    if args.threshold is not None:
        if not (0.0 <= args.threshold <= 1.0):
            print("Error: Threshold must be between 0.0 and 1.0", file=sys.stderr)
            return 1
        config._config['thresholds']['duplicate_similarity'] = args.threshold
    
    # Create scanner and detector
    scanner = FileScanner(config)
    detector = DuplicateCodeDetector(config, scanner)
    
    # Find duplicates
    print(f"Scanning for duplicate code in: {args.root}")
    print(f"Similarity threshold: {config.duplicate_similarity:.2%}")
    print()
    
    result = detector.find_duplicates(args.root)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"DUPLICATE CODE DETECTION RESULTS")
    print(f"{'='*80}")
    print(f"Total duplicate groups found: {len(result.duplicate_groups)}")
    print(f"Total duplicate instances: {result.total_duplicates}")
    
    if result.duplicate_groups:
        print(f"\nDuplicate groups:")
        for i, group in enumerate(result.duplicate_groups):
            print(format_duplicate_group(group, i))
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Found {len(result.duplicate_groups)} groups of duplicate code")
        print(f"Total of {result.total_duplicates} duplicate function instances")
        print(f"\nRecommendation: Consider consolidating these duplicates into")
        print(f"shared utility functions at the suggested locations.")
    else:
        print("\nNo duplicate code found! Your codebase is well-organized.")
    
    # Export to JSON if requested
    if args.json:
        detector.export_json(result, args.json)
        print(f"\nResults exported to: {args.json}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
