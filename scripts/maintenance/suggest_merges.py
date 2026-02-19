#!/usr/bin/env python3
"""Suggest merge opportunities for small related files.

This script analyzes small Python files (under 100 lines) and suggests merge
opportunities based on functional similarity. It helps improve code cohesion
by consolidating related small files into more substantial modules.

Usage:
    python scripts/maintenance/suggest_merges.py [--root PATH] [--json OUTPUT]
    
Examples:
    # Scan current directory
    python scripts/maintenance/suggest_merges.py
    
    # Scan specific directory
    python scripts/maintenance/suggest_merges.py --root scripts/
    
    # Export results to JSON
    python scripts/maintenance/suggest_merges.py --json merge_suggestions.json
    
    # Use custom similarity threshold
    python scripts/maintenance/suggest_merges.py --threshold 0.6
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.maintenance.core import (
    CleanupConfig,
    FileScanner,
    FileSizeAnalyzer,
    MergeSuggester
)


def format_merge_suggestion(suggestion, index):
    """Format a merge suggestion for console output."""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"Merge Suggestion #{index + 1}")
    lines.append(f"{'='*80}")
    lines.append(f"Functional Similarity: {suggestion.functional_similarity:.2%}")
    lines.append(f"Estimated Merged Size: {suggestion.estimated_size} lines")
    lines.append(f"\nSource Files ({len(suggestion.source_files)}):")
    
    for file_info in suggestion.source_files:
        lines.append(f"  - {file_info.path} ({file_info.code_lines} lines)")
    
    lines.append(f"\nTarget File: {suggestion.target_file}")
    
    if suggestion.required_import_updates:
        lines.append(f"\nRequired Import Updates ({len(suggestion.required_import_updates)}):")
        # Show first 5 import updates
        for file_path, old_import, new_import in suggestion.required_import_updates[:5]:
            lines.append(f"  - {file_path}")
            lines.append(f"    {old_import} → {new_import}")
        
        if len(suggestion.required_import_updates) > 5:
            remaining = len(suggestion.required_import_updates) - 5
            lines.append(f"  ... and {remaining} more")
    else:
        lines.append(f"\nNo import updates required")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Suggest merge opportunities for small related files',
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
        help='Similarity threshold (0.0-1.0, default: 0.5)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Determine similarity threshold
    similarity_threshold = args.threshold if args.threshold is not None else 0.5
    
    # Validate threshold
    if not (0.0 <= similarity_threshold <= 1.0):
        print("Error: Threshold must be between 0.0 and 1.0", file=sys.stderr)
        return 1
    
    # Create scanner and analyzers
    scanner = FileScanner(config)
    size_analyzer = FileSizeAnalyzer(config, scanner)
    merge_suggester = MergeSuggester(config, scanner, similarity_threshold)
    
    # Find small files
    print(f"Scanning for small files in: {args.root}")
    print(f"Small file threshold: {config.small_file_threshold} lines")
    print(f"Similarity threshold: {similarity_threshold:.2%}")
    print()
    
    size_result = size_analyzer.analyze_sizes(args.root)
    
    if not size_result.small_files:
        print("No small files found. Nothing to merge!")
        return 0
    
    print(f"Found {len(size_result.small_files)} small files")
    print(f"Analyzing merge opportunities...")
    print()
    
    # Suggest merges
    merge_result = merge_suggester.suggest_merges(size_result.small_files)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"MERGE SUGGESTION RESULTS")
    print(f"{'='*80}")
    print(f"Total merge suggestions: {len(merge_result.suggestions)}")
    print(f"Potential file reduction: {merge_result.total_file_reduction} files")
    
    if merge_result.suggestions:
        print(f"\nMerge suggestions:")
        for i, suggestion in enumerate(merge_result.suggestions):
            print(format_merge_suggestion(suggestion, i))
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Found {len(merge_result.suggestions)} merge opportunities")
        print(f"Merging these files would reduce file count by {merge_result.total_file_reduction}")
        
        # Calculate average similarity
        avg_similarity = sum(s.functional_similarity for s in merge_result.suggestions) / len(merge_result.suggestions)
        print(f"Average functional similarity: {avg_similarity:.2%}")
        
        # Calculate average merged size
        avg_size = sum(s.estimated_size for s in merge_result.suggestions) / len(merge_result.suggestions)
        print(f"Average merged file size: {avg_size:.0f} lines")
        
        print(f"\nRecommendation: Review these suggestions and merge files with high")
        print(f"functional similarity to improve code cohesion and maintainability.")
    else:
        print("\nNo merge opportunities found. Your small files are already well-organized!")
    
    # Export to JSON if requested
    if args.json:
        merge_suggester.export_json(merge_result, args.json)
        print(f"\nResults exported to: {args.json}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
