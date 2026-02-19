# Maintenance Scripts - User Guide

Comprehensive automated tools for analyzing, detecting, and remediating code quality issues in the BIST30 AI Trader project.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Scripts Reference](#scripts-reference)
  - [1. find_unused_files.py](#1-find_unused_filespy)
  - [2. find_small_files.py](#2-find_small_filespy)
  - [3. find_large_files.py](#3-find_large_filespy)
  - [4. find_duplicate_code.py](#4-find_duplicate_codepy)
  - [5. organize_scripts.py](#5-organize_scriptspy)
  - [6. suggest_merges.py](#6-suggest_mergespy)
  - [7. auto_cleanup.py](#7-auto_cleanuppy)
  - [8. generate_cleanup_report.py](#8-generate_cleanup_reportpy)
- [Configuration](#configuration)
- [Safety Features](#safety-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The maintenance scripts provide a comprehensive suite of tools to keep your codebase clean, organized, and maintainable. Each script focuses on a specific aspect of code quality:

- **Detection**: Identify unused files, size issues, and duplicates
- **Analysis**: Analyze script organization and merge opportunities
- **Cleanup**: Automated removal of temporary files and artifacts
- **Reporting**: Generate comprehensive cleanup reports

### Recent Improvements (v1.2.0)

- **Enhanced Unused File Detection**: Now correctly identifies entry points (`if __name__ == "__main__"`)
- **Special Directory Handling**: Automatically excludes tests/, api/, configs/, scripts/, examples/
- **Improved Accuracy**: Reduced false positives from 86.4% to 1.8%
- **Better Reporting**: Turkish and English language support

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate a comprehensive report** (recommended first step):
   ```bash
   python scripts/maintenance/generate_cleanup_report.py --markdown report.md
   ```

3. **Review specific issues**:
   ```bash
   # Find unused files
   python scripts/maintenance/find_unused_files.py
   
   # Find duplicate code
   python scripts/maintenance/find_duplicate_code.py
   ```

4. **Execute cleanup** (always use dry-run first):
   ```bash
   # Preview cleanup
   python scripts/maintenance/auto_cleanup.py
   
   # Execute cleanup
   python scripts/maintenance/auto_cleanup.py --execute
   ```

## Scripts Reference

### 1. find_unused_files.py

**Purpose**: Identifies Python files that are not imported anywhere in the project, helping you find dead code.

**Usage**:
```bash
python scripts/maintenance/find_unused_files.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root directory to scan (default: current directory)
- `--config FILE` - Path to cleanup configuration file
- `--json FILE` - Export results to JSON file

**Examples**:

```bash
# Scan current directory
python scripts/maintenance/find_unused_files.py

# Scan specific directory
python scripts/maintenance/find_unused_files.py --root scripts/

# Export results to JSON
python scripts/maintenance/find_unused_files.py --json unused_files.json

# Use custom configuration
python scripts/maintenance/find_unused_files.py --config my_config.yaml
```

**Output**:
- List of unused files with line counts and last modification dates
- Functions and classes defined in each unused file
- Percentage of unused files in the project
- Special files (\_\_init\_\_.py, \_\_main\_\_.py, setup.py) are automatically excluded

**When to use**:
- After major refactoring to identify orphaned files
- Before releases to remove dead code
- During code reviews to assess project cleanliness

**Safety notes**:
- Files may be "unused" but still serve a purpose (e.g., standalone scripts)
- Always review the list before deleting files
- Check if files are referenced in documentation or shell scripts

---

### 2. find_small_files.py

**Purpose**: Identifies files with fewer than 100 lines of code (configurable). Small files may be candidates for merging to improve code cohesion.

**Usage**:
```bash
python scripts/maintenance/find_small_files.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root directory to scan (default: current directory)
- `--config FILE` - Path to cleanup configuration file
- `--json FILE` - Export results to JSON file
- `--threshold N` - Small file threshold in lines (overrides config)

**Examples**:

```bash
# Scan with default threshold (100 lines)
python scripts/maintenance/find_small_files.py

# Use custom threshold
python scripts/maintenance/find_small_files.py --threshold 150

# Scan specific directory and export
python scripts/maintenance/find_small_files.py --root src/ --json small_files.json

# Group by directory
python scripts/maintenance/find_small_files.py | grep "/"
```

**Output**:
- Small files grouped by directory
- File sizes sorted from smallest to largest
- Total files and lines per directory
- File size distribution histogram
- Directories with multiple small files (merge candidates)

**When to use**:
- When planning code consolidation
- To identify fragmented modules
- Before suggesting merges (use with suggest_merges.py)

**Best practices**:
- Not all small files should be merged (e.g., \_\_init\_\_.py)
- Consider functional cohesion, not just file size
- Use suggest_merges.py for intelligent merge recommendations

---

### 3. find_large_files.py

**Purpose**: Identifies files with more than 500 lines of code (configurable). Large files may be candidates for splitting to improve maintainability.

**Usage**:
```bash
python scripts/maintenance/find_large_files.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root directory to scan (default: current directory)
- `--config FILE` - Path to cleanup configuration file
- `--json FILE` - Export results to JSON file
- `--threshold N` - Large file threshold in lines (overrides config)

**Examples**:

```bash
# Scan with default threshold (500 lines)
python scripts/maintenance/find_large_files.py

# Use custom threshold
python scripts/maintenance/find_large_files.py --threshold 600

# Scan specific directory
python scripts/maintenance/find_large_files.py --root src/

# Export with split suggestions
python scripts/maintenance/find_large_files.py --json large_files.json
```

**Output**:
- Large files sorted by size (largest first)
- Suggested split points (line numbers) based on class/function boundaries
- Approximate segment sizes after split
- File structure summary (classes and functions)
- File size distribution histogram

**When to use**:
- When files become difficult to maintain
- During refactoring planning
- To improve code navigability

**Split point suggestions**:
- Based on class and function boundaries
- Considers logical cohesion
- Aims for balanced segment sizes
- Manual review recommended before splitting

---

### 4. find_duplicate_code.py

**Purpose**: Identifies functions with identical or near-identical implementations across multiple files. Helps eliminate redundancy and create shared utilities.

**Usage**:
```bash
python scripts/maintenance/find_duplicate_code.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root directory to scan (default: current directory)
- `--config FILE` - Path to cleanup configuration file
- `--json FILE` - Export results to JSON file
- `--threshold FLOAT` - Similarity threshold 0.0-1.0 (default from config: 0.85)

**Examples**:

```bash
# Scan with default threshold (85% similarity)
python scripts/maintenance/find_duplicate_code.py

# Use stricter threshold (95% similarity)
python scripts/maintenance/find_duplicate_code.py --threshold 0.95

# Use looser threshold (70% similarity)
python scripts/maintenance/find_duplicate_code.py --threshold 0.70

# Scan specific directory
python scripts/maintenance/find_duplicate_code.py --root scripts/

# Export results
python scripts/maintenance/find_duplicate_code.py --json duplicates.json
```

**Output**:
- Duplicate groups with function names
- Similarity percentage for each group
- All file locations and line numbers
- Code snippets for comparison
- Suggested shared utility location

**How it works**:
- Extracts all functions from Python files
- Normalizes code (removes whitespace and comments)
- Calculates similarity using sequence matching
- Groups functions above similarity threshold

**When to use**:
- After copy-paste coding sessions
- During refactoring to consolidate utilities
- Before creating shared libraries

**Best practices**:
- Review suggested locations before moving code
- Consider creating a utils module for shared functions
- Update all references after consolidation
- Add tests for the consolidated function

---

### 5. organize_scripts.py

**Purpose**: Categorizes scripts by usage pattern (production, analysis, maintenance, integration tests) and proposes reorganization into appropriate subdirectories.

**Usage**:
```bash
python scripts/maintenance/organize_scripts.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root scripts directory (default: scripts/)
- `--config FILE` - Path to cleanup configuration file
- `--json FILE` - Export results to JSON file
- `--execute` - Execute reorganization (default is dry-run)

**Examples**:

```bash
# Analyze organization (dry-run)
python scripts/maintenance/organize_scripts.py

# Analyze specific directory
python scripts/maintenance/organize_scripts.py --root scripts/

# Export reorganization plan
python scripts/maintenance/organize_scripts.py --json organization.json

# Execute reorganization (moves files)
python scripts/maintenance/organize_scripts.py --execute
```

**Output**:
- Script categories with counts
- Target directories for each category
- Reorganization plan (source → target)
- Broken import warnings
- Confirmation prompt before execution

**Categories**:
- **Production**: Scripts used regularly in production/development workflows
- **Analysis**: Scripts for infrequent analysis or debugging
- **Maintenance**: One-time or infrequent setup/migration scripts
- **Integration Tests**: Scripts testing integration between components

**Categorization logic**:
1. Production scripts: Referenced in shell scripts, docs, or explicitly listed in config
2. Analysis scripts: Contains keywords (analyze, check, inspect, compare, evaluate)
3. Maintenance scripts: Contains keywords (migrate, update, fix, clean, convert)
4. Integration tests: Contains keywords (test, verify, validate, debug)

**When to use**:
- When scripts directory becomes cluttered
- After adding many new scripts
- To improve project organization

**⚠️ WARNING**:
- Always run in dry-run mode first
- Review broken import warnings carefully
- Update imports after reorganization
- Test thoroughly after moving files
- Consider using --no-git-check only if you know what you're doing

---

### 6. suggest_merges.py

**Purpose**: Analyzes small related files and suggests merge opportunities based on functional similarity. Helps improve code cohesion.

**Usage**:
```bash
python scripts/maintenance/suggest_merges.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root directory to scan (default: current directory)
- `--config FILE` - Path to cleanup configuration file
- `--json FILE` - Export results to JSON file
- `--threshold FLOAT` - Similarity threshold 0.0-1.0 (default: 0.5)

**Examples**:

```bash
# Suggest merges with default threshold (50% similarity)
python scripts/maintenance/suggest_merges.py

# Use stricter threshold (70% similarity)
python scripts/maintenance/suggest_merges.py --threshold 0.7

# Use looser threshold (30% similarity)
python scripts/maintenance/suggest_merges.py --threshold 0.3

# Scan specific directory
python scripts/maintenance/suggest_merges.py --root src/utils/

# Export suggestions
python scripts/maintenance/suggest_merges.py --json merge_suggestions.json
```

**Output**:
- Merge suggestions with functional similarity scores
- Source files and estimated merged size
- Target file path
- Required import updates
- Potential file count reduction

**Functional similarity calculation**:
- Import patterns (40%): Shared imports indicate related functionality
- Class hierarchies (30%): Inheritance relationships
- Function naming (30%): Similar prefixes/suffixes

**When to use**:
- After identifying small files (use find_small_files.py first)
- When planning code consolidation
- To improve module cohesion

**Best practices**:
- Only merge files with high functional similarity (>60%)
- Verify merged file size stays under 500 lines
- Update all imports after merging
- Run tests after merging
- Consider creating a new module name instead of using one source file

---

### 7. auto_cleanup.py

**Purpose**: Automated cleanup of temporary files, \_\_pycache\_\_ directories, old log files, empty \_\_init\_\_.py files, and other artifacts.

**Usage**:
```bash
python scripts/maintenance/auto_cleanup.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root directory to scan (default: current directory)
- `--config FILE` - Path to cleanup configuration file
- `--execute` - Execute cleanup (default is dry-run)
- `--json FILE` - Export results to JSON file
- `--no-git-check` - Skip git safety checks (not recommended)

**Examples**:

```bash
# Dry-run mode (preview cleanup)
python scripts/maintenance/auto_cleanup.py

# Execute cleanup (requires confirmation)
python scripts/maintenance/auto_cleanup.py --execute

# Scan specific directory
python scripts/maintenance/auto_cleanup.py --root scripts/

# Export cleanup plan
python scripts/maintenance/auto_cleanup.py --json cleanup_plan.json

# Skip git checks (not recommended)
python scripts/maintenance/auto_cleanup.py --execute --no-git-check
```

**What it cleans**:
- \_\_pycache\_\_ directories and .pyc files
- Log files older than retention period (default: 30 days)
- Empty \_\_init\_\_.py files in directories with no other Python files
- Temporary files (*.tmp, *.bak, *~, .DS_Store)

**Output**:
- Operations grouped by type
- File sizes to be freed
- Confirmation prompt before execution
- Git branch creation and commit messages

**Safety features**:
- Dry-run mode by default
- Git repository check (requires clean working directory)
- Creates timestamped cleanup branch before executing
- Confirmation prompt before deleting files
- All operations logged with timestamps
- Rollback instructions provided

**When to use**:
- Before releases to clean up artifacts
- After development sprints
- When disk space is running low
- As part of regular maintenance

**⚠️ CRITICAL WARNINGS**:
- ALWAYS run in dry-run mode first
- Review the list of files to be deleted
- Ensure git working directory is clean
- Backup important files before executing
- Do not use --no-git-check unless absolutely necessary
- Test thoroughly after cleanup

**Rollback**:
```bash
# If cleanup was executed, rollback with:
git checkout <original-branch>
git branch -D <cleanup-branch>
```

---

### 8. generate_cleanup_report.py

**Purpose**: Generates a comprehensive cleanup report that aggregates all analysis results into a single document with prioritized action items.

**Usage**:
```bash
python scripts/maintenance/generate_cleanup_report.py [OPTIONS]
```

**Options**:
- `--root PATH` - Root directory to analyze (default: current directory)
- `--config FILE` - Path to cleanup configuration file
- `--markdown FILE` - Export report to Markdown file
- `--json FILE` - Export report to JSON file
- `--lang LANG` - Report language: en (English) or tr (Turkish)
- `--scripts-dir PATH` - Scripts directory for organization analysis
- `--verbose` - Show detailed progress information

**Examples**:

```bash
# Generate report for current directory
python scripts/maintenance/generate_cleanup_report.py

# Generate Markdown report
python scripts/maintenance/generate_cleanup_report.py --markdown cleanup_report.md

# Generate JSON report
python scripts/maintenance/generate_cleanup_report.py --json cleanup_report.json

# Generate both formats
python scripts/maintenance/generate_cleanup_report.py --markdown report.md --json report.json

# Generate Turkish report
python scripts/maintenance/generate_cleanup_report.py --lang tr --markdown rapor.md

# Analyze specific directory with verbose output
python scripts/maintenance/generate_cleanup_report.py --root /path/to/project --verbose

# Custom scripts directory
python scripts/maintenance/generate_cleanup_report.py --scripts-dir custom_scripts/
```

**Report sections**:
1. **Summary**: Total files, average size, issue counts
2. **Unused Files**: List of files not imported anywhere
3. **File Sizes**: Small and large files analysis
4. **Duplicate Code**: Groups of duplicate functions
5. **Script Organization**: Current vs. proposed structure
6. **Merge Suggestions**: Opportunities to consolidate files
7. **Estimated Improvements**: Projected impact of cleanup
8. **Prioritized Actions**: Ranked by impact and effort

**Output formats**:
- **Console**: Formatted summary with key findings
- **Markdown**: Comprehensive report with all details
- **JSON**: Machine-readable format for automation

**Estimated improvements**:
- File count reduction percentage
- Average file size increase percentage
- Maintainability improvement score (0-100)

**Prioritized actions** (ranked by impact/effort):
1. Remove unused files (high impact, low effort)
2. Eliminate duplicate code (high impact, medium effort)
3. Merge small files (medium impact, medium effort)
4. Split large files (medium impact, high effort)
5. Reorganize scripts (low impact, low effort)

**When to use**:
- As the first step in cleanup planning
- Before major refactoring
- For project health assessments
- To track cleanup progress over time
- For team discussions about code quality

**Best practices**:
- Generate reports regularly (weekly/monthly)
- Compare reports over time to track improvements
- Share reports with the team
- Use as input for sprint planning
- Export to both Markdown (for humans) and JSON (for automation)

**Turkish language support**:
- Section headers translated
- Action items translated
- Recommendations translated
- Maintains same structure and data

---

## Configuration

The cleanup system is configured via `cleanup_config.yaml` in the project root.

**Configuration file structure**:

```yaml
thresholds:
  small_file_lines: 100        # Files smaller than this are "small"
  large_file_lines: 500        # Files larger than this are "large"
  log_retention_days: 30       # Keep logs for this many days
  duplicate_similarity: 0.85   # Similarity threshold for duplicates (0.0-1.0)

exclusions:
  directories:                 # Directories to exclude from analysis
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
  patterns:                    # File patterns to exclude
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "setup.py"

script_categories:
  production:                  # Explicitly list production scripts
    - train_models.py
    - run_backtest.py
    - daily_run.py
    - paper_trading_runner.py
  
  analysis_keywords:           # Keywords for analysis scripts
    - analyze
    - check
    - inspect
    - compare
    - evaluate
  
  maintenance_keywords:        # Keywords for maintenance scripts
    - migrate
    - update
    - fix
    - clean
    - convert
  
  test_keywords:              # Keywords for test scripts
    - test
    - verify
    - validate
    - debug
```

**Configuration options**:

### Thresholds
- `small_file_lines`: Threshold for small files (default: 100)
- `large_file_lines`: Threshold for large files (default: 500)
- `log_retention_days`: Days to retain log files (default: 30)
- `duplicate_similarity`: Similarity threshold for duplicate detection (default: 0.85)

### Exclusions
- `directories`: List of directories to exclude from all analysis
- `patterns`: List of file patterns to exclude (supports wildcards)

### Script Categories
- `production`: Explicit list of production scripts (stay at root)
- `analysis_keywords`: Keywords to identify analysis scripts
- `maintenance_keywords`: Keywords to identify maintenance scripts
- `test_keywords`: Keywords to identify test scripts

**Customization examples**:

```yaml
# Stricter thresholds
thresholds:
  small_file_lines: 50
  large_file_lines: 300
  duplicate_similarity: 0.95

# More exclusions
exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - build
    - dist
    - .eggs
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "setup.py"
    - "conftest.py"
    - "*.pyc"

# Custom script categories
script_categories:
  production:
    - train_models.py
    - run_backtest.py
    - daily_run.py
    - paper_trading_runner.py
    - data_fetcher.py
  analysis_keywords:
    - analyze
    - check
    - inspect
    - compare
    - evaluate
    - report
    - visualize
```

**Using custom configuration**:

```bash
# All scripts support --config option
python scripts/maintenance/find_small_files.py --config my_config.yaml
python scripts/maintenance/generate_cleanup_report.py --config my_config.yaml
```

---

## Safety Features

All cleanup operations include multiple layers of safety:

### 1. Dry-Run Mode (Default)
- All destructive operations default to dry-run mode
- Preview changes before executing
- No files are modified or deleted in dry-run mode
- Use `--execute` flag to perform actual operations

### 2. Git Integration
- Checks for clean working directory before executing
- Refuses to proceed if uncommitted changes exist
- Creates timestamped cleanup branch (cleanup-YYYYMMDD-HHMMSS)
- Commits changes incrementally with descriptive messages
- Provides rollback instructions

### 3. Confirmation Prompts
- Requires explicit confirmation before deleting files
- Shows list of files to be affected
- Allows cancellation at any point

### 4. Incremental Operations
- Changes are committed in logical groups
- Easy to identify what changed
- Simplifies rollback if needed

### 5. Comprehensive Logging
- All operations logged with timestamps
- File paths and reasons recorded
- Errors logged with context

### 6. Rollback Support
```bash
# Rollback cleanup operations
git checkout <original-branch>
git branch -D <cleanup-branch>

# Rollback script reorganization
git checkout <original-branch>
git branch -D <reorganization-branch>
```

---

## Best Practices

### General Workflow

1. **Start with a report**:
   ```bash
   python scripts/maintenance/generate_cleanup_report.py --markdown report.md
   ```

2. **Review specific issues**:
   ```bash
   python scripts/maintenance/find_unused_files.py
   python scripts/maintenance/find_duplicate_code.py
   ```

3. **Plan your cleanup**:
   - Review prioritized actions in the report
   - Identify quick wins (unused files, duplicates)
   - Plan larger refactoring (merges, splits)

4. **Execute incrementally**:
   - Start with low-risk operations (auto_cleanup)
   - Move to medium-risk (removing unused files)
   - End with high-risk (merges, reorganization)

5. **Test thoroughly**:
   - Run tests after each cleanup operation
   - Verify functionality hasn't changed
   - Check for broken imports

### Specific Recommendations

**For unused files**:
- Review each file before deleting
- Check if referenced in documentation
- Verify not used by external tools
- Consider archiving instead of deleting

**For duplicate code**:
- Consolidate into shared utilities
- Add comprehensive tests
- Update all references
- Document the shared function

**For small files**:
- Only merge functionally related files
- Keep merged files under 500 lines
- Update imports after merging
- Maintain clear module boundaries

**For large files**:
- Split at logical boundaries
- Ensure each split has clear responsibility
- Update imports after splitting
- Consider creating a package

**For script organization**:
- Keep production scripts at root
- Group analysis scripts together
- Separate maintenance scripts
- Update documentation after reorganization

**For auto cleanup**:
- Run regularly (weekly/monthly)
- Always use dry-run first
- Review log retention settings
- Backup before executing

### Frequency Recommendations

- **Daily**: Auto cleanup (dry-run)
- **Weekly**: Generate cleanup report
- **Monthly**: Review and act on report findings
- **Quarterly**: Major refactoring (merges, splits, reorganization)
- **Before releases**: Full cleanup cycle

---

## Troubleshooting

### Common Issues

**Issue**: "Error: Directory not found"
```bash
# Solution: Verify the path exists
ls -la /path/to/directory
# Or use absolute path
python scripts/maintenance/find_unused_files.py --root /absolute/path
```

**Issue**: "Error: Uncommitted changes detected"
```bash
# Solution: Commit or stash changes
git status
git add .
git commit -m "Save work before cleanup"
# Or stash
git stash
```

**Issue**: "Error: Threshold must be positive"
```bash
# Solution: Use valid threshold values
python scripts/maintenance/find_small_files.py --threshold 100  # Valid
python scripts/maintenance/find_small_files.py --threshold -50  # Invalid
```

**Issue**: "Error: Threshold must be between 0.0 and 1.0"
```bash
# Solution: Use valid similarity threshold
python scripts/maintenance/find_duplicate_code.py --threshold 0.85  # Valid
python scripts/maintenance/find_duplicate_code.py --threshold 1.5   # Invalid
```

**Issue**: "Warning: Broken imports detected"
```bash
# Solution: Review and update imports after reorganization
# 1. Note the broken imports from the output
# 2. Update import statements in affected files
# 3. Run tests to verify
pytest
```

**Issue**: "No module named 'scripts.maintenance.core'"
```bash
# Solution: Run from project root
cd /path/to/project/root
python scripts/maintenance/find_unused_files.py
```

**Issue**: Configuration file not found
```bash
# Solution: Create configuration file or use default
# Option 1: Create cleanup_config.yaml in project root
# Option 2: Specify config path
python scripts/maintenance/find_unused_files.py --config /path/to/config.yaml
# Option 3: Use defaults (no --config flag)
python scripts/maintenance/find_unused_files.py
```

### Getting Help

**View script help**:
```bash
python scripts/maintenance/find_unused_files.py --help
python scripts/maintenance/auto_cleanup.py --help
```

**Check configuration**:
```bash
# Verify configuration is valid
python -c "from scripts.maintenance.core import CleanupConfig; c = CleanupConfig(); print('Config OK')"
```

**Verify git status**:
```bash
git status
git log --oneline -5
```

**Test without side effects**:
```bash
# All scripts support dry-run or read-only modes
python scripts/maintenance/find_unused_files.py  # Read-only
python scripts/maintenance/auto_cleanup.py       # Dry-run by default
python scripts/maintenance/organize_scripts.py   # Dry-run by default
```

---

## Additional Resources

**Documentation**:
- `docs/specs/post-development-cleanup/requirements.md` - Requirements specification
- `docs/specs/post-development-cleanup/design.md` - Design document
- `docs/specs/post-development-cleanup/tasks.md` - Implementation plan

**Testing**:
```bash
# Run all maintenance tests
pytest tests/maintenance/

# Run with coverage
pytest tests/maintenance/ --cov=scripts/maintenance --cov-report=html

# Run only property-based tests
pytest tests/maintenance/ -m property
```

**Requirements**:
- Python 3.9+
- pytest (for testing)
- hypothesis (for property-based testing)
- PyYAML (for configuration)
- Git (for safe operations)

---

## Summary

The maintenance scripts provide a comprehensive toolkit for keeping your codebase clean and maintainable. Key takeaways:

✅ **Always start with a report** to understand the current state
✅ **Use dry-run mode** before executing any destructive operations
✅ **Review carefully** before deleting or moving files
✅ **Test thoroughly** after each cleanup operation
✅ **Commit incrementally** to make rollback easier
✅ **Run regularly** to prevent technical debt accumulation

For questions or issues, refer to the design document or run scripts with `--help` flag.
