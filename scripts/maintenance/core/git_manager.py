"""Git operations manager for safe cleanup."""

from pathlib import Path
from typing import Tuple
import subprocess
from datetime import datetime


class GitManager:
    """Manages git operations."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def check_git_status(self) -> Tuple[bool, str]:
        """Check if repo is clean (no uncommitted changes)."""
        try:
            # Check if git repo exists
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False, "No git repository found"
            
            # Check for uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                return False, "Uncommitted changes detected. Please commit or stash changes."
            
            return True, "Repository is clean"
        except Exception as e:
            return False, f"Git error: {str(e)}"
    
    def create_cleanup_branch(self) -> str:
        """Create timestamped cleanup branch."""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        branch_name = f"cleanup-{timestamp}"
        
        try:
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return branch_name
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create branch: {e.stderr.decode()}")
    
    def commit_changes(self, message: str):
        """Commit current changes."""
        try:
            # Add all changes
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to commit changes: {e.stderr.decode()}")
    
    def rollback(self, original_branch: str):
        """Rollback to original branch and delete cleanup branch."""
        try:
            # Get current branch name
            current_branch = self.get_current_branch()
            
            # Checkout original branch
            subprocess.run(
                ['git', 'checkout', original_branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Delete cleanup branch
            if current_branch.startswith('cleanup-'):
                subprocess.run(
                    ['git', 'branch', '-D', current_branch],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to rollback: {e.stderr.decode()}")
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get current branch: {e.stderr.decode()}")
