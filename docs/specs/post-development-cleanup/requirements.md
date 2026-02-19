# Requirements Document

## Introduction

The BIST30 AI Trader project has undergone intensive development with multiple features (Feature Importance, Regime Detection, etc.) and now requires comprehensive cleanup and modularization. The post-development cleanup feature provides automated tools to detect code quality issues, reorganize project structure, eliminate duplicate code, and generate actionable cleanup reports. The goal is to make the project sustainable and maintainable without over-fragmentation, following the principle that files under 100 lines should be merged, files over 500 lines should be split, and files in between should remain as-is.

## Glossary

- **Cleanup_System**: The automated post-development cleanup toolset
- **Detection_Tool**: Scripts that analyze and detect code quality issues
- **Unused_File**: A Python file that is not imported by any other file in the project
- **Small_File**: A Python file containing fewer than 100 lines of code
- **Large_File**: A Python file containing more than 500 lines of code
- **Duplicate_Code**: Functions or code blocks that appear in multiple files with identical or near-identical implementations
- **Production_Script**: Scripts used regularly in production or development workflows
- **Analysis_Script**: Scripts used infrequently for analysis or debugging purposes
- **Maintenance_Script**: One-time or infrequent scripts for setup, migration, or maintenance tasks
- **Integration_Test_Script**: Scripts that test integration between components (distinct from unit tests)
- **Dry_Run_Mode**: Execution mode that shows what would be changed without making actual modifications
- **Cleanup_Report**: Comprehensive document showing current state, issues detected, and prioritized action items

## Requirements

### Requirement 1: Unused File Detection

**User Story:** As a developer, I want to identify Python files that are not imported anywhere in the project, so that I can remove dead code and reduce project complexity.

#### Acceptance Criteria

1. WHEN the Detection_Tool scans the project THEN the Cleanup_System SHALL identify all Python files that are not imported by any other file
2. WHEN a Python file is imported using any import statement (import, from...import) THEN the Cleanup_System SHALL mark that file as used
3. WHEN generating the unused files list THEN the Cleanup_System SHALL exclude special files (__init__.py, __main__.py, setup.py, and top-level scripts)
4. WHEN an unused file is detected THEN the Cleanup_System SHALL report the file path and last modification date
5. THE Cleanup_System SHALL output the unused files list in both console format and JSON format

### Requirement 2: File Size Analysis

**User Story:** As a developer, I want to identify files that are too small or too large, so that I can merge small files for better cohesion and split large files for better maintainability.

#### Acceptance Criteria

1. WHEN the Detection_Tool analyzes file sizes THEN the Cleanup_System SHALL count lines of code excluding blank lines and comments
2. WHEN a Python file contains fewer than 100 lines THEN the Cleanup_System SHALL classify it as a Small_File
3. WHEN a Python file contains more than 500 lines THEN the Cleanup_System SHALL classify it as a Large_File
4. WHEN reporting Small_Files THEN the Cleanup_System SHALL group them by directory and suggest merge candidates
5. WHEN reporting Large_Files THEN the Cleanup_System SHALL identify logical split points based on class and function boundaries
6. THE Cleanup_System SHALL calculate and report average file size across the project

### Requirement 3: Duplicate Code Detection

**User Story:** As a developer, I want to identify duplicate code across the project, so that I can eliminate redundancy and create shared utilities.

#### Acceptance Criteria

1. WHEN the Detection_Tool scans for duplicates THEN the Cleanup_System SHALL identify functions with identical or near-identical implementations across multiple files
2. WHEN comparing functions THEN the Cleanup_System SHALL normalize whitespace and comments before comparison
3. WHEN duplicate code is detected THEN the Cleanup_System SHALL group duplicates together and report all file locations
4. WHEN reporting duplicates THEN the Cleanup_System SHALL calculate similarity percentage for near-identical code
5. THE Cleanup_System SHALL suggest a shared utility location for each duplicate code group

### Requirement 4: Script Organization and Categorization

**User Story:** As a developer, I want to reorganize scripts by usage pattern, so that production scripts, analysis scripts, maintenance scripts, and test scripts are clearly separated.

#### Acceptance Criteria

1. WHEN the Cleanup_System categorizes scripts THEN it SHALL identify Production_Scripts by checking if they are referenced in shell scripts, documentation, or CI/CD configurations
2. WHEN a script is used infrequently for analysis or debugging THEN the Cleanup_System SHALL classify it as an Analysis_Script
3. WHEN a script is used for one-time setup, migration, or maintenance THEN the Cleanup_System SHALL classify it as a Maintenance_Script
4. WHEN a script tests integration between components THEN the Cleanup_System SHALL classify it as an Integration_Test_Script
5. THE Cleanup_System SHALL propose a reorganization plan moving scripts to appropriate subdirectories (scripts/analysis/, scripts/maintenance/, scripts/tests/)
6. WHEN generating the reorganization plan THEN the Cleanup_System SHALL preserve production scripts at the scripts/ root level
7. THE Cleanup_System SHALL detect and report any broken imports that would result from script reorganization

### Requirement 5: Merge Suggestions

**User Story:** As a developer, I want automated suggestions for merging small related files, so that I can improve code cohesion without manual analysis.

#### Acceptance Criteria

1. WHEN the Cleanup_System suggests merges THEN it SHALL only suggest merging Small_Files (under 100 lines)
2. WHEN identifying merge candidates THEN the Cleanup_System SHALL group files by directory and functional similarity
3. WHEN analyzing functional similarity THEN the Cleanup_System SHALL examine import patterns, class hierarchies, and function naming conventions
4. WHEN suggesting a merge THEN the Cleanup_System SHALL estimate the resulting file size and verify it remains under 500 lines
5. THE Cleanup_System SHALL provide a merge plan showing source files, target file, and required import updates

### Requirement 6: Automated Cleanup Operations

**User Story:** As a developer, I want automated cleanup of temporary files and artifacts, so that the project remains clean without manual intervention.

#### Acceptance Criteria

1. THE Cleanup_System SHALL remove all __pycache__ directories and .pyc files
2. WHEN cleaning log files THEN the Cleanup_System SHALL remove log files older than 30 days
3. THE Cleanup_System SHALL remove empty __init__.py files in directories with no other Python files
4. WHEN cleaning temporary files THEN the Cleanup_System SHALL remove files matching patterns (*.tmp, *.bak, *~, .DS_Store)
5. WHEN performing cleanup operations THEN the Cleanup_System SHALL support Dry_Run_Mode showing what would be deleted without actual deletion
6. WHEN Dry_Run_Mode is disabled THEN the Cleanup_System SHALL require explicit confirmation before deleting files
7. THE Cleanup_System SHALL log all cleanup operations with timestamps and file paths

### Requirement 7: Comprehensive Cleanup Report

**User Story:** As a developer, I want a comprehensive cleanup report showing current state and prioritized action items, so that I can make informed decisions about project cleanup.

#### Acceptance Criteria

1. WHEN generating the Cleanup_Report THEN the Cleanup_System SHALL include total Python file count and average file size
2. THE Cleanup_Report SHALL list all unused files with counts and percentages
3. THE Cleanup_Report SHALL list all Small_Files and Large_Files with counts and percentages
4. THE Cleanup_Report SHALL list all duplicate code groups with similarity scores
5. THE Cleanup_Report SHALL include a script organization section showing current vs. proposed structure
6. WHEN calculating improvements THEN the Cleanup_Report SHALL estimate file count reduction, average file size increase, and maintainability score improvement
7. THE Cleanup_Report SHALL provide prioritized action items ranked by impact and effort
8. THE Cleanup_System SHALL generate the report in both Markdown format and JSON format
9. WHERE the user is Turkish THEN the Cleanup_Report SHALL include Turkish translations for section headers and descriptions

### Requirement 8: Safety and Reversibility

**User Story:** As a developer, I want all cleanup operations to be safe and reversible, so that I can experiment with cleanup without risk of data loss.

#### Acceptance Criteria

1. WHEN performing any destructive operation THEN the Cleanup_System SHALL verify a git repository exists and has no uncommitted changes
2. IF uncommitted changes exist THEN the Cleanup_System SHALL refuse to proceed and prompt the user to commit or stash changes
3. WHEN starting cleanup operations THEN the Cleanup_System SHALL create a new git branch with timestamp (cleanup-YYYYMMDD-HHMMSS)
4. WHEN performing file operations THEN the Cleanup_System SHALL commit changes incrementally with descriptive commit messages
5. THE Cleanup_System SHALL provide a rollback command that reverts to the original branch and deletes the cleanup branch
6. WHEN an error occurs during cleanup THEN the Cleanup_System SHALL halt operations and provide instructions for manual recovery

### Requirement 9: Integration Testing

**User Story:** As a developer, I want to verify that cleanup operations don't break the project, so that I can ensure the codebase remains functional after cleanup.

#### Acceptance Criteria

1. WHEN cleanup operations complete THEN the Cleanup_System SHALL prompt the user to run tests
2. THE Cleanup_System SHALL provide a command to run all unit tests and integration tests
3. WHEN tests fail after cleanup THEN the Cleanup_System SHALL provide rollback instructions
4. THE Cleanup_System SHALL generate a test report showing which tests passed and failed
5. WHEN all tests pass THEN the Cleanup_System SHALL mark the cleanup as successful and suggest merging the cleanup branch

### Requirement 10: Configuration and Customization

**User Story:** As a developer, I want to customize cleanup thresholds and exclusions, so that the cleanup process fits the project's specific needs.

#### Acceptance Criteria

1. THE Cleanup_System SHALL read configuration from a cleanup_config.yaml file
2. WHEN the configuration file is missing THEN the Cleanup_System SHALL use default values (small_file_threshold=100, large_file_threshold=500, log_retention_days=30)
3. THE Cleanup_System SHALL allow customization of file size thresholds for Small_Files and Large_Files
4. THE Cleanup_System SHALL allow specification of excluded directories (e.g., .venv, node_modules, __pycache__)
5. THE Cleanup_System SHALL allow specification of excluded file patterns for unused file detection
6. WHEN configuration is invalid THEN the Cleanup_System SHALL report validation errors and use default values
