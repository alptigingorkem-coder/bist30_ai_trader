# Cleanup Configuration Guide

Comprehensive guide to configuring the post-development cleanup system through `cleanup_config.yaml`.

## Table of Contents

- [Overview](#overview)
- [Configuration File Location](#configuration-file-location)
- [Configuration Structure](#configuration-structure)
- [Configuration Options](#configuration-options)
  - [Thresholds](#thresholds)
  - [Exclusions](#exclusions)
  - [Script Categories](#script-categories)
- [Example Configurations](#example-configurations)
- [Threshold Tuning Guide](#threshold-tuning-guide)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The `cleanup_config.yaml` file controls how the maintenance scripts analyze and clean your codebase. It allows you to customize:

- **File size thresholds** for identifying small and large files
- **Retention policies** for log files and temporary artifacts
- **Similarity thresholds** for duplicate code detection
- **Exclusion patterns** for directories and files to skip
- **Script categorization rules** for organizing scripts by usage pattern

All maintenance scripts respect this configuration, ensuring consistent behavior across the cleanup system.

## Configuration File Location

The configuration file should be placed at the **project root**:

```
your-project/
├── cleanup_config.yaml    ← Configuration file here
├── scripts/
│   └── maintenance/
├── src/
└── tests/
```

**Alternative locations**:
- Specify a custom path using the `--config` flag:
  ```bash
  python scripts/maintenance/find_unused_files.py --config /path/to/config.yaml
  ```

**Default behavior**:
- If no configuration file is found, the system uses built-in defaults
- No error is raised if the file is missing
- You can start without a config file and add one later

## Configuration Structure

The configuration file has three main sections:

```yaml
thresholds:
  # File size and similarity thresholds
  
exclusions:
  # Directories and patterns to exclude
  
script_categories:
  # Rules for categorizing scripts
```

Each section is optional. If a section is missing, defaults are used for that section.

## Configuration Options

### Thresholds

Controls numeric thresholds for various cleanup operations.

```yaml
thresholds:
  small_file_lines: 100
  large_file_lines: 500
  log_retention_days: 30
  duplicate_similarity: 0.85
```

#### `small_file_lines`

**Type**: Integer  
**Default**: 100  
**Range**: 1 - 1000  
**Used by**: `find_small_files.py`, `suggest_merges.py`

Files with fewer than this many lines of code are considered "small" and may be candidates for merging.

**What counts as a line**:
- Only non-blank, non-comment lines are counted
- Docstrings are counted as code
- Imports are counted as code

**Tuning guidance**:
- **50-75**: Very strict, identifies even moderately small files
- **100**: Default, good balance for most projects
- **150-200**: Lenient, only flags very small files

**Example**:
```yaml
thresholds:
  small_file_lines: 75  # More aggressive small file detection
```

#### `large_file_lines`

**Type**: Integer  
**Default**: 500  
**Range**: 100 - 5000  
**Used by**: `find_large_files.py`, `suggest_merges.py`

Files with more than this many lines of code are considered "large" and may need splitting.

**What counts as a line**:
- Only non-blank, non-comment lines are counted
- Docstrings are counted as code
- Imports are counted as code

**Tuning guidance**:
- **300-400**: Strict, encourages smaller files
- **500**: Default, follows common best practices
- **700-1000**: Lenient, only flags very large files

**Important constraint**:
- Must be greater than `small_file_lines`
- Recommended gap: at least 200 lines between thresholds
- Files between thresholds are considered "normal" size

**Example**:
```yaml
thresholds:
  small_file_lines: 100
  large_file_lines: 600  # More lenient large file threshold
```

#### `log_retention_days`

**Type**: Integer  
**Default**: 30  
**Range**: 1 - 365  
**Used by**: `auto_cleanup.py`

Log files older than this many days will be removed during automated cleanup.

**What qualifies as a log file**:
- Files with `.log` extension
- Files in directories named `logs/` or `log/`
- Files matching pattern `*.log.*` (e.g., `app.log.2024-01-15`)

**Tuning guidance**:
- **7-14 days**: Short retention, saves disk space
- **30 days**: Default, good for most projects
- **60-90 days**: Long retention, useful for debugging historical issues
- **180+ days**: Very long retention, consider archiving instead

**Example**:
```yaml
thresholds:
  log_retention_days: 14  # Keep logs for 2 weeks only
```

#### `duplicate_similarity`

**Type**: Float  
**Default**: 0.85  
**Range**: 0.0 - 1.0  
**Used by**: `find_duplicate_code.py`

Minimum similarity score for two functions to be considered duplicates.

**How similarity is calculated**:
- Code is normalized (whitespace and comments removed)
- Sequence matching algorithm compares normalized code
- Score of 1.0 = identical code
- Score of 0.0 = completely different code

**Tuning guidance**:
- **0.95-1.0**: Very strict, only near-identical code
- **0.85**: Default, catches most duplicates with minor variations
- **0.70-0.80**: Moderate, catches similar code with more variations
- **0.50-0.65**: Lenient, may produce false positives

**Example**:
```yaml
thresholds:
  duplicate_similarity: 0.90  # Stricter duplicate detection
```

**Trade-offs**:
- Higher threshold: Fewer false positives, may miss similar code
- Lower threshold: More duplicates found, more false positives to review

---

### Exclusions

Controls which directories and files are excluded from analysis.

```yaml
exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
  patterns:
    - "test_*.py"
    - "__init__.py"
```

#### `directories`

**Type**: List of strings  
**Default**: Common virtual environment and cache directories  
**Used by**: All scripts

Directories to completely skip during file scanning.

**Default exclusions**:
```yaml
directories:
  - .venv
  - __pycache__
  - .git
  - node_modules
  - .pytest_cache
  - .mypy_cache
  - .tox
  - build
  - dist
  - "*.egg-info"
  - .vscode
  - .idea
  - htmlcov
  - .coverage
```

**When to add exclusions**:
- Virtual environments (venv, env, virtualenv)
- Build artifacts (build, dist, target)
- IDE directories (.vscode, .idea, .eclipse)
- Cache directories (.cache, .pytest_cache)
- Third-party code (vendor, external, lib)
- Generated code (generated, auto-generated)

**Pattern support**:
- Exact names: `.venv`, `build`
- Wildcards: `*.egg-info`, `*-cache`
- Relative paths: `docs/build`, `src/generated`

**Example**:
```yaml
exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - build
    - dist
    - vendor           # Third-party code
    - docs/build       # Generated documentation
    - src/generated    # Auto-generated code
```

#### `patterns`

**Type**: List of strings  
**Default**: Test files and special Python files  
**Used by**: `find_unused_files.py`, `find_small_files.py`, `find_large_files.py`

File patterns to exclude from unused file detection and size analysis.

**Default exclusions**:
```yaml
patterns:
  - "test_*.py"
  - "*_test.py"
  - "__init__.py"
  - "__main__.py"
  - "setup.py"
  - "conftest.py"
```

**Why these defaults**:
- `test_*.py`, `*_test.py`: Test files may not be imported directly
- `__init__.py`: Package markers, often empty or minimal
- `__main__.py`: Entry points, not imported
- `setup.py`: Installation script, not imported
- `conftest.py`: Pytest configuration, not imported

**When to add exclusions**:
- Entry point scripts (main.py, run.py, cli.py)
- Configuration files (config.py, settings.py)
- Migration scripts (migrate_*.py, migration_*.py)
- One-time scripts (setup_*.py, install_*.py)

**Pattern syntax**:
- Wildcards: `*` matches any characters
- Prefix: `test_*.py` matches `test_foo.py`, `test_bar.py`
- Suffix: `*_test.py` matches `foo_test.py`, `bar_test.py`
- Exact: `"setup.py"` matches only `setup.py`

**Example**:
```yaml
exclusions:
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"
    - "conftest.py"
    - "main.py"         # Entry point
    - "cli.py"          # Command-line interface
    - "migrate_*.py"    # Migration scripts
    - "*_config.py"     # Configuration files
```

---

### Script Categories

Controls how scripts are categorized and organized.

```yaml
script_categories:
  production:
    - train_models.py
    - run_backtest.py
  analysis_keywords:
    - analyze
    - check
  maintenance_keywords:
    - migrate
    - update
  test_keywords:
    - test
    - verify
```

#### `production`

**Type**: List of strings  
**Default**: Empty list  
**Used by**: `organize_scripts.py`

Explicit list of production scripts that should remain at the `scripts/` root level.

**What are production scripts**:
- Scripts used regularly in production or development workflows
- Scripts referenced in shell scripts, documentation, or CI/CD
- Critical scripts that should be easily accessible

**Why list them explicitly**:
- Prevents accidental reorganization
- Makes production scripts obvious
- Ensures they stay at predictable locations

**Example**:
```yaml
script_categories:
  production:
    - train_models.py
    - run_backtest.py
    - daily_run.py
    - paper_trading_runner.py
    - data_fetcher.py
    - model_evaluator.py
```

**Best practices**:
- List only scripts that run regularly
- Include scripts referenced in documentation
- Include scripts used in automation
- Keep the list minimal (5-10 scripts typically)

#### `analysis_keywords`

**Type**: List of strings  
**Default**: Common analysis-related keywords  
**Used by**: `organize_scripts.py`

Keywords that identify analysis scripts (should go to `scripts/analysis/`).

**Default keywords**:
```yaml
analysis_keywords:
  - analyze
  - check
  - inspect
  - compare
  - evaluate
  - report
  - visualize
  - plot
```

**What are analysis scripts**:
- Scripts for infrequent analysis or debugging
- Scripts that generate reports or visualizations
- Scripts that compare or evaluate results
- Scripts used for investigation

**Categorization logic**:
- If script name contains any keyword → categorized as analysis
- Case-insensitive matching
- Partial matching (e.g., "analyzer" matches "analyze")

**Example**:
```yaml
script_categories:
  analysis_keywords:
    - analyze
    - check
    - inspect
    - compare
    - evaluate
    - report
    - visualize
    - plot
    - explore      # Added
    - investigate  # Added
    - profile      # Added
```

**Examples of matching scripts**:
- `analyze_features.py` → analysis (contains "analyze")
- `check_data_quality.py` → analysis (contains "check")
- `compare_models.py` → analysis (contains "compare")
- `visualize_results.py` → analysis (contains "visualize")

#### `maintenance_keywords`

**Type**: List of strings  
**Default**: Common maintenance-related keywords  
**Used by**: `organize_scripts.py`

Keywords that identify maintenance scripts (should go to `scripts/maintenance/`).

**Default keywords**:
```yaml
maintenance_keywords:
  - migrate
  - update
  - fix
  - clean
  - convert
  - setup
  - install
```

**What are maintenance scripts**:
- One-time or infrequent setup scripts
- Migration scripts for data or code
- Scripts that fix or update existing data
- Installation or configuration scripts

**Categorization logic**:
- If script name contains any keyword → categorized as maintenance
- Case-insensitive matching
- Partial matching (e.g., "migration" matches "migrate")

**Example**:
```yaml
script_categories:
  maintenance_keywords:
    - migrate
    - update
    - fix
    - clean
    - convert
    - setup
    - install
    - repair      # Added
    - rebuild     # Added
    - initialize  # Added
```

**Examples of matching scripts**:
- `migrate_database.py` → maintenance (contains "migrate")
- `update_config.py` → maintenance (contains "update")
- `fix_data_issues.py` → maintenance (contains "fix")
- `cleanup_old_files.py` → maintenance (contains "clean")

#### `test_keywords`

**Type**: List of strings  
**Default**: Common test-related keywords  
**Used by**: `organize_scripts.py`

Keywords that identify integration test scripts (should go to `scripts/tests/`).

**Default keywords**:
```yaml
test_keywords:
  - test
  - verify
  - validate
  - debug
  - benchmark
```

**What are test scripts**:
- Integration test scripts (not unit tests)
- Verification scripts
- Validation scripts
- Debugging utilities
- Benchmark scripts

**Note**: Unit tests in `tests/` directory are not affected by this configuration.

**Categorization logic**:
- If script name contains any keyword → categorized as test
- Case-insensitive matching
- Partial matching (e.g., "testing" matches "test")

**Example**:
```yaml
script_categories:
  test_keywords:
    - test
    - verify
    - validate
    - debug
    - benchmark
    - smoke      # Added
    - sanity     # Added
    - integration # Added
```

**Examples of matching scripts**:
- `test_integration.py` → test (contains "test")
- `verify_deployment.py` → test (contains "verify")
- `validate_data.py` → test (contains "validate")
- `benchmark_models.py` → test (contains "benchmark")

---

## Example Configurations

### Minimal Configuration

For projects that want to use mostly defaults with minor tweaks:

```yaml
thresholds:
  small_file_lines: 75  # Slightly stricter than default

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - vendor  # Add third-party code exclusion

script_categories:
  production:
    - main.py
    - run.py
```

### Strict Configuration

For projects that want aggressive cleanup:

```yaml
thresholds:
  small_file_lines: 50
  large_file_lines: 300
  log_retention_days: 7
  duplicate_similarity: 0.95

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - build
    - dist
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"

script_categories:
  production:
    - train.py
    - evaluate.py
  analysis_keywords:
    - analyze
    - check
    - inspect
    - compare
    - evaluate
    - report
    - visualize
    - plot
    - explore
  maintenance_keywords:
    - migrate
    - update
    - fix
    - clean
    - convert
    - setup
    - install
    - repair
  test_keywords:
    - test
    - verify
    - validate
    - debug
    - benchmark
```

### Lenient Configuration

For projects that want conservative cleanup:

```yaml
thresholds:
  small_file_lines: 150
  large_file_lines: 800
  log_retention_days: 90
  duplicate_similarity: 0.75

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - .mypy_cache
    - build
    - dist
    - vendor
    - external
    - third_party
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"
    - "conftest.py"
    - "main.py"
    - "cli.py"
    - "*_config.py"
    - "*_settings.py"

script_categories:
  production:
    - train_models.py
    - run_backtest.py
    - daily_run.py
    - paper_trading_runner.py
    - data_fetcher.py
    - model_evaluator.py
    - feature_engineer.py
  analysis_keywords:
    - analyze
    - check
    - inspect
  maintenance_keywords:
    - migrate
    - update
    - fix
  test_keywords:
    - test
    - verify
```

### Machine Learning Project Configuration

Tailored for ML/AI projects:

```yaml
thresholds:
  small_file_lines: 100
  large_file_lines: 500
  log_retention_days: 30
  duplicate_similarity: 0.85

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - build
    - dist
    - models          # Trained model files
    - data            # Data files
    - logs            # Log files
    - checkpoints     # Training checkpoints
    - tensorboard     # TensorBoard logs
    - mlruns          # MLflow runs
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"
    - "conftest.py"

script_categories:
  production:
    - train.py
    - evaluate.py
    - predict.py
    - serve.py
  analysis_keywords:
    - analyze
    - visualize
    - plot
    - compare
    - evaluate
    - explore
    - profile
  maintenance_keywords:
    - migrate
    - update
    - fix
    - clean
    - convert
    - preprocess
  test_keywords:
    - test
    - verify
    - validate
    - benchmark
```

---

## Threshold Tuning Guide

### How to Choose File Size Thresholds

**Step 1: Analyze your current codebase**

```bash
# Generate a report to see current file size distribution
python scripts/maintenance/generate_cleanup_report.py --markdown report.md
```

Review the "File Sizes" section to understand:
- Average file size
- Median file size
- Distribution of file sizes

**Step 2: Set initial thresholds**

Use these guidelines based on your project type:

| Project Type | Small Threshold | Large Threshold |
|--------------|----------------|-----------------|
| Microservices | 50-75 | 300-400 |
| Standard Application | 100 | 500 |
| Monolithic Application | 150-200 | 700-1000 |
| Library/Framework | 75-100 | 400-600 |

**Step 3: Iterate and refine**

```bash
# Test with different thresholds
python scripts/maintenance/find_small_files.py --threshold 75
python scripts/maintenance/find_small_files.py --threshold 100
python scripts/maintenance/find_small_files.py --threshold 150

# Compare results and choose the threshold that identifies the right files
```

**Step 4: Validate**

- Review the list of small/large files
- Ensure the threshold catches files you want to address
- Ensure it doesn't flag files that are appropriately sized

### How to Choose Duplicate Similarity Threshold

**Step 1: Start with default (0.85)**

```bash
python scripts/maintenance/find_duplicate_code.py
```

**Step 2: Adjust based on results**

**If you see too many false positives** (code that's not really duplicate):
- Increase threshold to 0.90 or 0.95
- This makes detection stricter

**If you're missing obvious duplicates**:
- Decrease threshold to 0.75 or 0.80
- This makes detection more lenient

**Step 3: Test different thresholds**

```bash
# Strict (fewer results, higher confidence)
python scripts/maintenance/find_duplicate_code.py --threshold 0.95

# Default (balanced)
python scripts/maintenance/find_duplicate_code.py --threshold 0.85

# Lenient (more results, requires more review)
python scripts/maintenance/find_duplicate_code.py --threshold 0.75
```

**Step 4: Choose based on your workflow**

- **0.95+**: When you want high confidence and will act on all results
- **0.85**: When you want a balance and will review results
- **0.75**: When you want to find all potential duplicates and will carefully review

### How to Choose Log Retention Period

**Consider these factors**:

1. **Disk space**: How much space do logs consume?
   ```bash
   du -sh logs/
   ```

2. **Debugging needs**: How far back do you typically need to look?
   - Active development: 7-14 days
   - Stable production: 30-60 days
   - Compliance requirements: 90+ days

3. **Log volume**: How quickly do logs accumulate?
   - High volume: Shorter retention (7-14 days)
   - Low volume: Longer retention (60-90 days)

**Recommended values**:
- **7 days**: High-volume logs, tight disk space
- **14 days**: Active development, frequent debugging
- **30 days**: Default, good for most projects
- **60 days**: Production systems, occasional debugging
- **90+ days**: Compliance requirements, archival needs

---

## Best Practices

### Configuration Management

1. **Version control**: Always commit `cleanup_config.yaml` to git
   ```bash
   git add cleanup_config.yaml
   git commit -m "Add cleanup configuration"
   ```

2. **Document customizations**: Add comments explaining why you chose specific values
   ```yaml
   thresholds:
     small_file_lines: 75  # Stricter than default because we have many utility files
     large_file_lines: 600  # Lenient because our models are complex
   ```

3. **Review regularly**: Revisit configuration as your project evolves
   - After major refactoring
   - When project structure changes
   - When team size changes

4. **Share with team**: Ensure all team members understand the configuration
   - Document in README
   - Discuss in team meetings
   - Include in onboarding

### Threshold Selection

1. **Start conservative**: Begin with lenient thresholds and tighten over time
   ```yaml
   # Initial configuration
   thresholds:
     small_file_lines: 150  # Lenient
     large_file_lines: 800  # Lenient
   
   # After cleanup
   thresholds:
     small_file_lines: 100  # Stricter
     large_file_lines: 500  # Stricter
   ```

2. **Measure impact**: Track metrics before and after threshold changes
   ```bash
   # Before
   python scripts/maintenance/generate_cleanup_report.py --json before.json
   
   # Change thresholds
   # ...
   
   # After
   python scripts/maintenance/generate_cleanup_report.py --json after.json
   ```

3. **Consider team preferences**: Align thresholds with team coding standards
   - Discuss in code reviews
   - Reference in style guide
   - Enforce in CI/CD

### Exclusion Management

1. **Exclude generated code**: Always exclude auto-generated files
   ```yaml
   exclusions:
     directories:
       - generated
       - auto-generated
       - .generated
     patterns:
       - "*_pb2.py"      # Protocol buffers
       - "*_generated.py"
   ```

2. **Exclude third-party code**: Don't analyze code you don't maintain
   ```yaml
   exclusions:
     directories:
       - vendor
       - external
       - third_party
       - lib
   ```

3. **Exclude build artifacts**: Don't analyze temporary build files
   ```yaml
   exclusions:
     directories:
       - build
       - dist
       - target
       - out
   ```

4. **Review exclusions periodically**: Ensure exclusions are still relevant
   - Remove exclusions for deleted directories
   - Add exclusions for new generated code
   - Update patterns as project evolves

### Script Categorization

1. **Be explicit about production scripts**: List all production scripts explicitly
   ```yaml
   script_categories:
     production:
       - train.py
       - evaluate.py
       - predict.py
       - serve.py
       # Add new production scripts here
   ```

2. **Use descriptive script names**: Name scripts to match categorization keywords
   - Analysis: `analyze_*.py`, `check_*.py`, `compare_*.py`
   - Maintenance: `migrate_*.py`, `update_*.py`, `fix_*.py`
   - Tests: `test_*.py`, `verify_*.py`, `validate_*.py`

3. **Review categorization results**: Check that scripts are categorized correctly
   ```bash
   python scripts/maintenance/organize_scripts.py
   # Review the output before executing
   ```

---

## Troubleshooting

### Configuration Not Loading

**Symptom**: Scripts use default values instead of your configuration

**Solutions**:

1. **Check file location**:
   ```bash
   ls -la cleanup_config.yaml
   # Should be in project root
   ```

2. **Check file name**:
   ```bash
   # Correct: cleanup_config.yaml
   # Incorrect: cleanup-config.yaml, cleanup_config.yml
   ```

3. **Specify config path explicitly**:
   ```bash
   python scripts/maintenance/find_unused_files.py --config cleanup_config.yaml
   ```

4. **Check YAML syntax**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('cleanup_config.yaml'))"
   ```

### Invalid Threshold Values

**Symptom**: Error message about invalid threshold values

**Solutions**:

1. **Check threshold ranges**:
   ```yaml
   thresholds:
     small_file_lines: 100    # Must be positive integer
     large_file_lines: 500    # Must be > small_file_lines
     log_retention_days: 30   # Must be positive integer
     duplicate_similarity: 0.85  # Must be 0.0-1.0
   ```

2. **Ensure proper types**:
   ```yaml
   # Correct
   thresholds:
     small_file_lines: 100
   
   # Incorrect
   thresholds:
     small_file_lines: "100"  # String instead of integer
   ```

3. **Validate configuration**:
   ```bash
   python -c "from scripts.maintenance.core import CleanupConfig; c = CleanupConfig(); print('Valid')"
   ```

### Exclusions Not Working

**Symptom**: Excluded directories or files still appear in results

**Solutions**:

1. **Check pattern syntax**:
   ```yaml
   # Correct
   patterns:
     - "test_*.py"    # Matches test_foo.py
     - "*_test.py"    # Matches foo_test.py
   
   # Incorrect
   patterns:
     - test_*.py      # Missing quotes
     - "test_.*\.py"  # Regex syntax (not supported)
   ```

2. **Check directory paths**:
   ```yaml
   # Correct
   directories:
     - .venv          # Relative to project root
     - build
     - dist
   
   # Incorrect
   directories:
     - /.venv         # Absolute path (not recommended)
     - ./build        # Unnecessary ./
   ```

3. **Verify exclusions are loaded**:
   ```bash
   python -c "from scripts.maintenance.core import CleanupConfig; c = CleanupConfig(); print(c.excluded_dirs)"
   ```

### Script Categorization Issues

**Symptom**: Scripts categorized incorrectly

**Solutions**:

1. **Check keyword matching**:
   ```yaml
   # Script: analyze_data.py
   # Matches: analysis_keywords contains "analyze"
   
   # Script: my_script.py
   # Doesn't match any keywords → uncategorized
   ```

2. **Add to production list explicitly**:
   ```yaml
   script_categories:
     production:
       - my_script.py  # Explicitly mark as production
   ```

3. **Add custom keywords**:
   ```yaml
   script_categories:
     analysis_keywords:
       - analyze
       - check
       - custom_keyword  # Add your custom keyword
   ```

4. **Review categorization**:
   ```bash
   python scripts/maintenance/organize_scripts.py
   # Check output before executing
   ```

### Configuration Validation Errors

**Symptom**: Error messages about invalid configuration

**Solutions**:

1. **Check YAML syntax**:
   ```bash
   # Use a YAML validator
   python -c "import yaml; yaml.safe_load(open('cleanup_config.yaml'))"
   ```

2. **Check indentation**:
   ```yaml
   # Correct (2 spaces)
   thresholds:
     small_file_lines: 100
   
   # Incorrect (tabs or inconsistent spaces)
   thresholds:
   	small_file_lines: 100
   ```

3. **Check for typos**:
   ```yaml
   # Correct
   thresholds:
     small_file_lines: 100
   
   # Incorrect
   thresholds:
     small_file_line: 100  # Missing 's'
   ```

4. **Use default configuration as template**:
   ```bash
   # Copy default configuration
   cp cleanup_config.yaml cleanup_config.yaml.backup
   # Edit carefully
   ```

---

## Summary

The `cleanup_config.yaml` file provides powerful customization for the cleanup system:

✅ **Thresholds**: Control file size and similarity detection  
✅ **Exclusions**: Skip irrelevant directories and files  
✅ **Script Categories**: Organize scripts by usage pattern  
✅ **Flexibility**: Start with defaults, customize as needed  
✅ **Safety**: Invalid configuration falls back to defaults  

**Quick start**:
1. Copy the default configuration from the project root
2. Customize thresholds based on your project needs
3. Add exclusions for generated code and third-party libraries
4. List production scripts explicitly
5. Test with dry-run mode before executing

**Remember**:
- Start conservative, tighten over time
- Document your customizations
- Review configuration regularly
- Share with your team

For more information, see:
- `scripts/maintenance/README.md` - Maintenance scripts guide
- `docs/specs/post-development-cleanup/requirements.md` - Requirements
- `docs/specs/post-development-cleanup/design.md` - Design document
