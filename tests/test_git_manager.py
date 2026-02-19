"""Unit tests for GitManager."""

import pytest
from pathlib import Path
import subprocess
from scripts.maintenance.core.git_manager import GitManager


@pytest.fixture
def git_repo(tmp_path):
    """Create a test git repository."""
    subprocess.run(['git', 'init'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=tmp_path, check=True, capture_output=True)
    
    # Create initial commit
    test_file = tmp_path / 'test.txt'
    test_file.write_text('test')
    subprocess.run(['git', 'add', 'test.txt'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=tmp_path, check=True, capture_output=True)
    
    return tmp_path


@pytest.fixture
def git_manager(git_repo):
    """Create GitManager instance."""
    return GitManager(git_repo)


def test_check_git_status_clean(git_manager):
    """Test git status check with clean repo."""
    is_clean, message = git_manager.check_git_status()
    assert is_clean is True
    assert 'clean' in message.lower()


def test_check_git_status_dirty(git_manager, git_repo):
    """Test git status check with uncommitted changes."""
    # Create uncommitted change
    test_file = git_repo / 'new_file.txt'
    test_file.write_text('new content')
    
    is_clean, message = git_manager.check_git_status()
    assert is_clean is False
    assert 'uncommitted' in message.lower()


def test_check_git_status_no_repo(tmp_path):
    """Test git status check with no repository."""
    manager = GitManager(tmp_path)
    is_clean, message = manager.check_git_status()
    assert is_clean is False
    assert 'no git repository' in message.lower()


def test_create_cleanup_branch(git_manager):
    """Test cleanup branch creation."""
    branch_name = git_manager.create_cleanup_branch()
    
    assert branch_name.startswith('cleanup-')
    assert len(branch_name) > len('cleanup-')
    
    # Verify we're on the new branch
    current_branch = git_manager.get_current_branch()
    assert current_branch == branch_name


def test_get_current_branch(git_manager):
    """Test getting current branch name."""
    branch_name = git_manager.get_current_branch()
    assert branch_name in ['master', 'main']  # Default branch names


def test_commit_changes(git_manager, git_repo):
    """Test committing changes."""
    # Create a change
    test_file = git_repo / 'test2.txt'
    test_file.write_text('test content')
    
    git_manager.commit_changes('Test commit')
    
    # Verify commit was created
    result = subprocess.run(
        ['git', 'log', '--oneline', '-1'],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert 'Test commit' in result.stdout


def test_rollback(git_manager):
    """Test rollback functionality."""
    original_branch = git_manager.get_current_branch()
    
    # Create cleanup branch
    cleanup_branch = git_manager.create_cleanup_branch()
    assert git_manager.get_current_branch() == cleanup_branch
    
    # Rollback
    git_manager.rollback(original_branch)
    
    # Verify we're back on original branch
    assert git_manager.get_current_branch() == original_branch
    
    # Verify cleanup branch is deleted
    result = subprocess.run(
        ['git', 'branch'],
        cwd=git_manager.repo_path,
        capture_output=True,
        text=True
    )
    assert cleanup_branch not in result.stdout
