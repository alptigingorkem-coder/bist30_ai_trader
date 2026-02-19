#!/usr/bin/env python3
"""Organize scripts by usage pattern.

This script categorizes scripts into production, analysis, maintenance, and
integration test categories, then proposes a reorganization plan to move them
into appropriate subdirectories. It also detects any imports that would break
after reorganization.

Usage:
    python scripts/maintenance/organize_scripts.py [--root PATH] [--json OUTPUT] [--execute]
    
Examples:
    # Analyze scripts in default location (dry-run mode)
    python scripts/maintenance/organize_scripts.py
    
    # Analyze scripts in specific directory
    python scripts/maintenance/organize_scripts.py --root scripts/
    
    # Export results to JSON
    python scripts/maintenance/organize_scripts.py --json organization.json
    
    # Execute reorganization (moves files)
    python scripts/maintenance/organize_scripts.py --execute
"""

import argparse
import sys
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.maintenance.core import (
    CleanupConfig,
    FileScanner,
    ScriptCategorizer
)


def format_category(category, show_scripts=True):
    """Format a script category for console output."""
    lines = []
    lines.append(f"\n{category.name.upper().replace('_', ' ')}")
    lines.append(f"  Target Directory: {category.target_directory}")
    lines.append(f"  Script Count: {len(category.scripts)}")
    
    if show_scripts and category.scripts:
        lines.append(f"  Scripts:")
        for script in sorted(category.scripts):
            lines.append(f"    - {script}")
    
    return '\n'.join(lines)


def format_reorganization_plan(plan):
    """Format reorganization plan for console output."""
    if not plan:
        return "\nNo reorganization needed - all scripts are already in correct locations."
    
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"REORGANIZATION PLAN")
    lines.append(f"{'='*80}")
    lines.append(f"Total moves: {len(plan)}")
    lines.append(f"\nProposed moves:")
    
    for old_path, new_path in plan:
        lines.append(f"  {old_path}")
        lines.append(f"    -> {new_path}")
    
    return '\n'.join(lines)


def format_broken_imports(broken_imports):
    """Format broken imports for console output."""
    if not broken_imports:
        return "\nNo broken imports detected."
    
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"WARNING: POTENTIAL BROKEN IMPORTS")
    lines.append(f"{'='*80}")
    lines.append(f"Found {len(broken_imports)} import statements that may break:")
    
    # Group by file
    imports_by_file = {}
    for file_path, import_stmt in broken_imports:
        if file_path not in imports_by_file:
            imports_by_file[file_path] = []
        imports_by_file[file_path].append(import_stmt)
    
    for file_path, imports in sorted(imports_by_file.items()):
        lines.append(f"\n  {file_path}:")
        for import_stmt in imports:
            lines.append(f"    - {import_stmt}")
    
    lines.append(f"\nRecommendation: Update these imports after reorganization.")
    
    return '\n'.join(lines)


def execute_reorganization(plan, dry_run=True):
    """Execute the reorganization plan."""
    if dry_run:
        print("\n[DRY RUN MODE] No files will be moved.")
        return True
    
    print("\n[EXECUTE MODE] Moving files...")
    
    for old_path, new_path in plan:
        try:
            # Create target directory if it doesn't exist
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(old_path), str(new_path))
            print(f"  ✓ Moved: {old_path} -> {new_path}")
        except Exception as e:
            print(f"  ✗ Error moving {old_path}: {e}", file=sys.stderr)
            return False
    
    print("\nReorganization complete!")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Organize scripts by usage pattern',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--root',
        type=Path,
        default=Path('scripts'),
        help='Root scripts directory to analyze (default: scripts/)'
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
        '--execute',
        action='store_true',
        help='Execute reorganization (default is dry-run mode)'
    )
    
    args = parser.parse_args()
    
    # Validate root directory
    if not args.root.exists():
        print(f"Error: Directory not found: {args.root}", file=sys.stderr)
        return 1
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Create scanner and categorizer
    scanner = FileScanner(config)
    categorizer = ScriptCategorizer(config, scanner)
    
    # Analyze organization
    print(f"Analyzing script organization in: {args.root}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print()
    
    result = categorizer.analyze_organization(args.root)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"SCRIPT ORGANIZATION ANALYSIS")
    print(f"{'='*80}")
    
    # Show categories
    print(format_category(result.production))
    print(format_category(result.analysis))
    print(format_category(result.maintenance))
    print(format_category(result.integration_tests))
    
    # Show reorganization plan
    print(format_reorganization_plan(result.reorganization_plan))
    
    # Show broken imports warning
    print(format_broken_imports(result.broken_imports))
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Production scripts: {len(result.production.scripts)} (stay at root)")
    print(f"Analysis scripts: {len(result.analysis.scripts)} (move to analysis/)")
    print(f"Maintenance scripts: {len(result.maintenance.scripts)} (move to maintenance/)")
    print(f"Integration test scripts: {len(result.integration_tests.scripts)} (move to tests/)")
    print(f"Total moves required: {len(result.reorganization_plan)}")
    print(f"Potential broken imports: {len(result.broken_imports)}")
    
    # Export to JSON if requested
    if args.json:
        categorizer.export_json(result, args.json)
        print(f"\nResults exported to: {args.json}")
    
    # Execute reorganization if requested
    if result.reorganization_plan:
        if args.execute:
            if result.broken_imports:
                print("\n" + "="*80)
                print("WARNING: Broken imports detected!")
                print("="*80)
                response = input("\nProceed with reorganization anyway? (yes/no): ")
                if response.lower() != 'yes':
                    print("Reorganization cancelled.")
                    return 0
            
            success = execute_reorganization(result.reorganization_plan, dry_run=False)
            if not success:
                return 1
        else:
            print("\nTo execute this reorganization, run with --execute flag:")
            print(f"  python {Path(__file__).name} --root {args.root} --execute")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
