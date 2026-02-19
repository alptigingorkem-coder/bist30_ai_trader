#!/usr/bin/env python3
"""Automated cleanup of temporary files and artifacts.

This script automatically cleans up temporary files, __pycache__ directories,
old log files, empty __init__.py files, and other artifacts. It supports
dry-run mode (default) and requires git safety checks before executing cleanup.

Usage:
    python scripts/maintenance/auto_cleanup.py [--root PATH] [--execute] [--json OUTPUT]
    
Examples:
    # Dry-run mode (shows what would be cleaned)
    python scripts/maintenance/auto_cleanup.py
    
    # Execute cleanup (requires confirmation)
    python scripts/maintenance/auto_cleanup.py --execute
    
    # Scan specific directory
    python scripts/maintenance/auto_cleanup.py --root scripts/
    
    # Export results to JSON
    python scripts/maintenance/auto_cleanup.py --json cleanup_results.json
    
Safety Features:
    - Dry-run mode by default (no files deleted)
    - Git repository check (requires clean working directory)
    - Creates timestamped cleanup branch before executing
    - Confirmation prompt before executing cleanup
    - All operations logged with timestamps
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.maintenance.core import (
    CleanupConfig,
    AutoCleanupManager,
    GitManager
)


def format_size(size_bytes):
    """Format size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_operation(operation, index):
    """Format a cleanup operation for console output."""
    lines = []
    lines.append(f"  {index + 1}. [{operation.operation_type}] {operation.target}")
    lines.append(f"     Reason: {operation.reason}")
    lines.append(f"     Size: {format_size(operation.size_bytes)}")
    return '\n'.join(lines)


def confirm_cleanup():
    """Prompt user for confirmation before executing cleanup."""
    print("\n" + "="*80)
    print("WARNING: This will permanently delete the files listed above!")
    print("="*80)
    response = input("\nDo you want to proceed with cleanup? (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automated cleanup of temporary files and artifacts',
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
        '--execute',
        action='store_true',
        help='Execute cleanup (default is dry-run mode)'
    )
    
    parser.add_argument(
        '--json',
        type=Path,
        help='Export results to JSON file'
    )
    
    parser.add_argument(
        '--no-git-check',
        action='store_true',
        help='Skip git safety checks (not recommended)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Create managers
    cleanup_manager = AutoCleanupManager(config)
    git_manager = GitManager(args.root)
    
    # Git safety checks (only if executing and not skipped)
    original_branch = None
    if args.execute and not args.no_git_check:
        print("Performing git safety checks...")
        is_clean, message = git_manager.check_git_status()
        
        if not is_clean:
            print(f"Error: {message}", file=sys.stderr)
            print("\nPlease commit or stash your changes before running cleanup.", file=sys.stderr)
            return 1
        
        print(f"✓ {message}")
        
        # Get current branch before creating cleanup branch
        original_branch = git_manager.get_current_branch()
        print(f"✓ Current branch: {original_branch}")
    
    # Execute cleanup
    dry_run = not args.execute
    mode_str = "DRY-RUN MODE" if dry_run else "EXECUTE MODE"
    
    print(f"\n{'='*80}")
    print(f"AUTOMATED CLEANUP - {mode_str}")
    print(f"{'='*80}")
    print(f"Root directory: {args.root}")
    print(f"Log retention: {config.log_retention_days} days")
    
    if dry_run:
        print("\nNote: Running in dry-run mode. No files will be deleted.")
        print("Use --execute flag to perform actual cleanup.")
    
    print("\nScanning for cleanup targets...")
    
    result = cleanup_manager.execute_cleanup(args.root, dry_run=dry_run)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"CLEANUP RESULTS")
    print(f"{'='*80}")
    print(f"Total operations: {len(result.operations)}")
    print(f"Total size to free: {format_size(result.total_size_freed)}")
    
    if result.operations:
        # Group operations by type
        operations_by_type = {}
        for op in result.operations:
            if op.operation_type not in operations_by_type:
                operations_by_type[op.operation_type] = []
            operations_by_type[op.operation_type].append(op)
        
        # Display operations by type
        for op_type, ops in operations_by_type.items():
            print(f"\n{op_type.upper().replace('_', ' ')} ({len(ops)} items):")
            print("-" * 80)
            for i, op in enumerate(ops):
                print(format_operation(op, i))
        
        # Summary
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        
        for op_type, ops in operations_by_type.items():
            total_size = sum(op.size_bytes for op in ops)
            print(f"{op_type.replace('_', ' ').title()}: {len(ops)} items ({format_size(total_size)})")
        
        print(f"\nTotal: {len(result.operations)} items ({format_size(result.total_size_freed)})")
        
        # If dry-run, show what would happen
        if dry_run:
            print("\n" + "="*80)
            print("DRY-RUN COMPLETE")
            print("="*80)
            print("No files were deleted. Run with --execute to perform cleanup.")
        else:
            # Executing - confirm first
            if not confirm_cleanup():
                print("\nCleanup cancelled by user.")
                return 0
            
            # Create cleanup branch
            print("\nCreating cleanup branch...")
            cleanup_branch = git_manager.create_cleanup_branch()
            print(f"✓ Created branch: {cleanup_branch}")
            
            # Execute cleanup
            print("\nExecuting cleanup operations...")
            result = cleanup_manager.execute_cleanup(args.root, dry_run=False)
            
            # Commit changes
            print("\nCommitting changes...")
            commit_message = f"Automated cleanup: removed {len(result.operations)} items, freed {format_size(result.total_size_freed)}"
            git_manager.commit_changes(commit_message)
            print(f"✓ Changes committed")
            
            print("\n" + "="*80)
            print("CLEANUP COMPLETE")
            print("="*80)
            print(f"Removed {len(result.operations)} items")
            print(f"Freed {format_size(result.total_size_freed)}")
            print(f"\nCleanup branch: {cleanup_branch}")
            print(f"Original branch: {original_branch}")
            print("\nTo rollback: git checkout {} && git branch -D {}".format(
                original_branch, cleanup_branch))
    else:
        print("\nNo cleanup targets found! Your project is already clean.")
    
    # Export to JSON if requested
    if args.json:
        cleanup_manager.export_json(result, args.json)
        print(f"\nResults exported to: {args.json}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
