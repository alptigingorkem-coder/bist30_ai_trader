"""
Core utilities for the post-development cleanup system.

This module contains shared utilities used by all cleanup tools:
- Configuration management
- File scanning
- File size analysis
- Duplicate code detection
- Common data structures
"""

from .config import CleanupConfig
from .scanner import FileScanner, FileInfo
from .size_analyzer import FileSizeAnalyzer, FileSizeResult
from .duplicate_detector import DuplicateCodeDetector, DuplicateGroup, DuplicateResult
from .unused_detector import UnusedFileDetector, UnusedFileResult
from .script_categorizer import ScriptCategorizer, ScriptCategory, ScriptOrganizationResult
from .merge_suggester import MergeSuggester, MergeSuggestion, MergeResult
from .auto_cleanup import AutoCleanupManager, CleanupOperation, CleanupResult
from .git_manager import GitManager
from .report_generator import ReportGenerator, CleanupReport

__all__ = [
    'CleanupConfig',
    'FileScanner',
    'FileInfo',
    'FileSizeAnalyzer',
    'FileSizeResult',
    'DuplicateCodeDetector',
    'DuplicateGroup',
    'DuplicateResult',
    'UnusedFileDetector',
    'UnusedFileResult',
    'ScriptCategorizer',
    'ScriptCategory',
    'ScriptOrganizationResult',
    'MergeSuggester',
    'MergeSuggestion',
    'MergeResult',
    'AutoCleanupManager',
    'CleanupOperation',
    'CleanupResult',
    'GitManager',
    'ReportGenerator',
    'CleanupReport',
]
