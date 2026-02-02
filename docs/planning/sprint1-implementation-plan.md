# Sprint 1 Implementation Plan: Git History Analysis Engine

**Epic**: 5 - Intelligent Branch Management
**Phase**: 1 - Infrastructure Layer
**Sprint**: 1 (Week 1-2)
**Story**: 5.1.1 - Git History Analysis Engine
**Status**: 🚀 Ready to Start

---

## Sprint Goal

Build a robust Git history analysis engine that can extract commit metadata, analyze file changes, and detect symbol-level changes using tree-sitter integration.

**Definition of Done**:
- ✅ All acceptance criteria met
- ✅ All tests passing (TDD: Red → Green → Refactor)
- ✅ Code coverage ≥ 90% for GitHistoryAnalyzer
- ✅ Performance benchmarks met
- ✅ Documentation updated

---

## Day-by-Day Implementation Plan

### Day 1: Project Setup + Basic Commit Extraction (RED)

**Morning: Environment Setup** (2 hours)
```bash
# 1. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/epic5-git-analyzer

# 2. Install dependencies
pip install pygit2
# Or: pip install GitPython

# 3. Create module structure
mkdir -p src/codeindex/git
touch src/codeindex/git/__init__.py
touch src/codeindex/git/analyzer.py
touch src/codeindex/git/models.py

# 4. Create test structure
mkdir -p tests/git
touch tests/git/__init__.py
touch tests/git/test_analyzer.py
touch tests/git/conftest.py  # Test fixtures
```

**Afternoon: Write Failing Tests** (4 hours)

**File**: `tests/git/conftest.py`
```python
"""Test fixtures for git analyzer tests"""
import pytest
import subprocess
from pathlib import Path
from typing import Iterator

@pytest.fixture
def test_repo(tmp_path: Path) -> Iterator[Path]:
    """
    Create a test git repository with sample commits

    Commits:
    1. Initial commit (README.md)
    2. Add src/auth.py with login function
    3. Modify src/auth.py - add validate function
    4. Add src/oauth.py
    5. Delete old file
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True
    )

    # Commit 1: Initial
    (repo_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True
    )

    # Commit 2: Add auth.py with login function
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "auth.py").write_text("""
def login(username, password):
    \"\"\"Authenticate user\"\"\"
    return True
""")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add login function"],
        cwd=repo_path,
        check=True
    )

    # Commit 3: Modify auth.py - add validate
    (src_dir / "auth.py").write_text("""
def login(username, password):
    \"\"\"Authenticate user\"\"\"
    if validate(username):
        return True
    return False

def validate(username):
    \"\"\"Validate username\"\"\"
    return len(username) > 0
""")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add validate function"],
        cwd=repo_path,
        check=True
    )

    yield repo_path

    # Cleanup happens automatically with tmp_path
```

**File**: `tests/git/test_analyzer.py` (RED phase - failing tests)
```python
"""Tests for GitHistoryAnalyzer (TDD: RED phase)"""
import pytest
from codeindex.git.analyzer import GitHistoryAnalyzer
from codeindex.git.models import CommitInfo, FileChange

class TestGitHistoryAnalyzer:
    """Test git history analysis"""

    def test_init_with_valid_repo(self, test_repo):
        """Test initializing analyzer with valid git repo"""
        analyzer = GitHistoryAnalyzer(str(test_repo))
        assert analyzer.repo_path == str(test_repo)
        # These will FAIL initially - that's the RED phase
        assert analyzer.repo is not None

    def test_get_commits_single(self, test_repo):
        """Test extracting single commit"""
        analyzer = GitHistoryAnalyzer(str(test_repo))
        commits = analyzer.get_commits("HEAD~1", "HEAD")

        # These assertions will FAIL - we haven't implemented yet
        assert len(commits) == 1
        assert isinstance(commits[0], CommitInfo)
        assert commits[0].sha  # Has SHA
        assert commits[0].message  # Has message

    def test_get_commits_range(self, test_repo):
        """Test extracting commit range"""
        analyzer = GitHistoryAnalyzer(str(test_repo))
        commits = analyzer.get_commits("HEAD~2", "HEAD")

        # FAIL - not implemented
        assert len(commits) == 2

    def test_get_commits_all(self, test_repo):
        """Test getting all commits"""
        analyzer = GitHistoryAnalyzer(str(test_repo))
        commits = analyzer.get_commits("HEAD~10", "HEAD")  # More than exists

        # Should return all 3 commits in test_repo
        assert len(commits) == 3
```

**Run Tests (Should Fail)**:
```bash
pytest tests/git/test_analyzer.py -v

# Expected output:
# FAILED test_init_with_valid_repo - ModuleNotFoundError
# FAILED test_get_commits_single - ModuleNotFoundError
# FAILED test_get_commits_range - ModuleNotFoundError
# ... etc
```

✅ **End of Day 1**: We have failing tests (RED phase complete)

---

### Day 2: Implement Basic Commit Extraction (GREEN)

**Morning: Create Data Models** (2 hours)

**File**: `src/codeindex/git/models.py`
```python
"""Data models for git analysis"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class CommitInfo:
    """Single commit metadata"""
    sha: str
    author: str
    author_email: str
    message: str
    timestamp: datetime
    parent_shas: List[str]
    files_changed: List[str]

    @property
    def short_sha(self) -> str:
        """Get short SHA (7 chars)"""
        return self.sha[:7]

    @property
    def first_line_message(self) -> str:
        """Get first line of commit message"""
        return self.message.split('\n')[0]

@dataclass
class DiffHunk:
    """Single diff hunk"""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    header: str
    content: str

@dataclass
class FileChange:
    """File-level changes in a commit"""
    file_path: str
    status: str  # "added" | "modified" | "deleted" | "renamed"
    lines_added: int
    lines_deleted: int
    hunks: List[DiffHunk]
    old_path: Optional[str] = None  # For renamed files

@dataclass
class SymbolChange:
    """Symbol-level changes"""
    file_path: str
    functions_added: List[str]
    functions_modified: List[str]
    functions_deleted: List[str]
    classes_added: List[str]
    classes_modified: List[str]
    classes_deleted: List[str]
```

**Afternoon: Implement GitHistoryAnalyzer** (4 hours)

**File**: `src/codeindex/git/analyzer.py`
```python
"""Git history analysis using pygit2"""
import pygit2
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import CommitInfo, FileChange, DiffHunk

class GitHistoryAnalyzer:
    """Analyze git repository history"""

    def __init__(self, repo_path: str = "."):
        """
        Initialize git analyzer

        Args:
            repo_path: Path to git repository

        Raises:
            ValueError: If path is not a valid git repository
        """
        self.repo_path = repo_path

        try:
            self.repo = pygit2.Repository(repo_path)
        except Exception as e:
            raise ValueError(f"Not a valid git repository: {repo_path}") from e

    def get_commits(
        self,
        since: str,
        until: str = "HEAD"
    ) -> List[CommitInfo]:
        """
        Get commits in range [since, until]

        Args:
            since: Start commit (SHA, branch, or HEAD~N)
            until: End commit (default: HEAD)

        Returns:
            List of CommitInfo objects in reverse chronological order
        """
        # Resolve commit references to actual commits
        until_commit = self._resolve_ref(until)
        since_commit = self._resolve_ref(since)

        # Walk commits from until to since
        commits = []
        walker = self.repo.walk(until_commit.id, pygit2.GIT_SORT_TIME)

        # Add commits until we reach since_commit
        for commit in walker:
            commit_info = self._commit_to_info(commit)
            commits.append(commit_info)

            if commit.id == since_commit.id:
                break

        return commits

    def _resolve_ref(self, ref: str) -> pygit2.Commit:
        """
        Resolve reference to commit object

        Handles:
        - SHA: "abc123"
        - Branch: "main", "feature/auth"
        - Relative: "HEAD~5"

        Args:
            ref: Git reference string

        Returns:
            pygit2.Commit object

        Raises:
            ValueError: If reference is invalid
        """
        try:
            # Try to resolve as revspec (handles HEAD~N syntax)
            obj = self.repo.revparse_single(ref)

            # If it's a commit, return it
            if isinstance(obj, pygit2.Commit):
                return obj

            # If it's a reference, peel to commit
            if isinstance(obj, pygit2.Reference):
                return obj.peel(pygit2.Commit)

            # If it's a tag, peel to commit
            if isinstance(obj, pygit2.Tag):
                return obj.peel(pygit2.Commit)

            raise ValueError(f"Cannot resolve {ref} to commit")

        except Exception as e:
            raise ValueError(f"Invalid git reference: {ref}") from e

    def _commit_to_info(self, commit: pygit2.Commit) -> CommitInfo:
        """
        Convert pygit2.Commit to CommitInfo

        Args:
            commit: pygit2 commit object

        Returns:
            CommitInfo with extracted metadata
        """
        # Get files changed in this commit
        files_changed = []
        if commit.parents:
            # Compare with first parent
            parent = commit.parents[0]
            diff = parent.tree.diff_to_tree(commit.tree)

            for delta in diff.deltas:
                files_changed.append(delta.new_file.path)
        else:
            # Initial commit - all files are new
            for entry in commit.tree:
                files_changed.append(entry.name)

        return CommitInfo(
            sha=str(commit.id),
            author=commit.author.name,
            author_email=commit.author.email,
            message=commit.message,
            timestamp=datetime.fromtimestamp(commit.commit_time),
            parent_shas=[str(p.id) for p in commit.parents],
            files_changed=files_changed
        )
```

**Run Tests Again (Should Pass)**:
```bash
pytest tests/git/test_analyzer.py -v

# Expected output:
# PASSED test_init_with_valid_repo
# PASSED test_get_commits_single
# PASSED test_get_commits_range
# PASSED test_get_commits_all
```

✅ **End of Day 2**: Basic commit extraction working (GREEN phase complete)

---

### Day 3: File-level Diff Analysis (RED → GREEN)

**Morning: Write Tests for File Changes** (2 hours)

**File**: `tests/git/test_analyzer.py` (add more tests)
```python
class TestFileChanges:
    """Test file-level change detection"""

    def test_get_file_changes_modified(self, test_repo):
        """Test detecting modified files"""
        analyzer = GitHistoryAnalyzer(str(test_repo))

        # Get the commit that modified auth.py (added validate function)
        commits = analyzer.get_commits("HEAD~1", "HEAD")
        commit_sha = commits[0].sha

        # FAIL - not implemented yet
        changes = analyzer.get_file_changes(commit_sha)

        assert "src/auth.py" in changes
        assert changes["src/auth.py"].status == "modified"
        assert changes["src/auth.py"].lines_added > 0
        assert len(changes["src/auth.py"].hunks) > 0

    def test_get_file_changes_added(self, test_repo):
        """Test detecting added files"""
        analyzer = GitHistoryAnalyzer(str(test_repo))

        # Get the commit that added auth.py
        commits = analyzer.get_commits("HEAD~2", "HEAD~1")
        commit_sha = commits[0].sha

        changes = analyzer.get_file_changes(commit_sha)

        assert "src/auth.py" in changes
        assert changes["src/auth.py"].status == "added"
        assert changes["src/auth.py"].lines_added > 0
        assert changes["src/auth.py"].lines_deleted == 0
```

**Run Tests (Should Fail)**:
```bash
pytest tests/git/test_analyzer.py::TestFileChanges -v
# FAILED - analyzer.get_file_changes not implemented
```

**Afternoon: Implement File Change Detection** (4 hours)

**File**: `src/codeindex/git/analyzer.py` (add method)
```python
def get_file_changes(self, commit_sha: str) -> Dict[str, FileChange]:
    """
    Get file-level changes for a commit

    Args:
        commit_sha: Commit SHA

    Returns:
        Dict mapping file_path -> FileChange
    """
    commit = self._resolve_ref(commit_sha)

    if not commit.parents:
        # Initial commit - all files are added
        return self._get_initial_commit_changes(commit)

    # Compare with first parent
    parent = commit.parents[0]
    diff = parent.tree.diff_to_tree(commit.tree)

    file_changes = {}

    for delta in diff.deltas:
        file_path = delta.new_file.path
        status = self._delta_status_to_string(delta.status)

        # Parse hunks
        hunks = []
        patch = diff[delta]
        for hunk in patch.hunks:
            hunks.append(DiffHunk(
                old_start=hunk.old_start,
                old_lines=hunk.old_lines,
                new_start=hunk.new_start,
                new_lines=hunk.new_lines,
                header=hunk.header,
                content=''.join(line.content for line in hunk.lines)
            ))

        # Calculate lines added/deleted
        lines_added = sum(
            1 for line in patch.line_stats
            if line.startswith('+')
        )
        lines_deleted = sum(
            1 for line in patch.line_stats
            if line.startswith('-')
        )

        file_changes[file_path] = FileChange(
            file_path=file_path,
            status=status,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            hunks=hunks,
            old_path=delta.old_file.path if status == "renamed" else None
        )

    return file_changes

def _delta_status_to_string(self, status: int) -> str:
    """Convert pygit2 delta status to string"""
    status_map = {
        pygit2.GIT_DELTA_ADDED: "added",
        pygit2.GIT_DELTA_DELETED: "deleted",
        pygit2.GIT_DELTA_MODIFIED: "modified",
        pygit2.GIT_DELTA_RENAMED: "renamed",
        pygit2.GIT_DELTA_COPIED: "copied",
    }
    return status_map.get(status, "unknown")
```

**Run Tests (Should Pass)**:
```bash
pytest tests/git/test_analyzer.py::TestFileChanges -v
# PASSED test_get_file_changes_modified
# PASSED test_get_file_changes_added
```

✅ **End of Day 3**: File-level diff working

---

### Day 4-5: Symbol-level Diff Analysis (RED → GREEN)

**Day 4 Morning: Write Tests for Symbol Changes** (2 hours)

**File**: `tests/git/test_analyzer.py` (add symbol tests)
```python
class TestSymbolChanges:
    """Test symbol-level change detection"""

    def test_get_symbol_changes_function_added(self, test_repo):
        """Test detecting added functions"""
        analyzer = GitHistoryAnalyzer(str(test_repo))

        # Commit that added validate function
        commits = analyzer.get_commits("HEAD~1", "HEAD")
        commit_sha = commits[0].sha

        # FAIL - not implemented
        symbol_changes = analyzer.get_symbol_changes(commit_sha)

        assert "src/auth.py" in symbol_changes
        changes = symbol_changes["src/auth.py"]
        assert "validate" in changes.functions_added

    def test_get_symbol_changes_function_modified(self, test_repo):
        """Test detecting modified functions"""
        analyzer = GitHistoryAnalyzer(str(test_repo))

        # Commit that modified login function (added validate call)
        commits = analyzer.get_commits("HEAD~1", "HEAD")
        commit_sha = commits[0].sha

        symbol_changes = analyzer.get_symbol_changes(commit_sha)

        assert "src/auth.py" in symbol_changes
        changes = symbol_changes["src/auth.py"]
        assert "login" in changes.functions_modified
```

**Day 4 Afternoon + Day 5: Implement Symbol Diff** (12 hours)

This is the most complex part - need to integrate with existing SymbolParser.

**File**: `src/codeindex/git/symbol_differ.py` (new file)
```python
"""Symbol-level diff calculator"""
from typing import Dict, List
from codeindex.parser import SymbolParser, Symbol
from .models import SymbolChange

class SymbolDiffer:
    """Calculate symbol-level differences between file versions"""

    def __init__(self):
        self.parser = SymbolParser()

    def diff_symbols(
        self,
        old_content: str,
        new_content: str,
        file_path: str = "",
        language: str = "python"
    ) -> SymbolChange:
        """
        Compare symbols between old and new file versions

        Args:
            old_content: Old file content
            new_content: New file content
            file_path: File path (for result)
            language: Programming language

        Returns:
            SymbolChange with added/modified/deleted symbols
        """
        # Parse both versions
        old_result = self.parser.parse_content(old_content, language)
        new_result = self.parser.parse_content(new_content, language)

        # Build symbol maps by name
        old_funcs = {s.name: s for s in old_result.symbols if s.kind == "function"}
        new_funcs = {s.name: s for s in new_result.symbols if s.kind == "function"}

        old_classes = {s.name: s for s in old_result.symbols if s.kind == "class"}
        new_classes = {s.name: s for s in new_result.symbols if s.kind == "class"}

        # Calculate differences
        funcs_added = [name for name in new_funcs if name not in old_funcs]
        funcs_deleted = [name for name in old_funcs if name not in new_funcs]
        funcs_modified = []

        # Check for modifications (signature or body changed)
        for name in set(old_funcs.keys()) & set(new_funcs.keys()):
            if self._is_modified(old_funcs[name], new_funcs[name]):
                funcs_modified.append(name)

        # Same for classes
        classes_added = [name for name in new_classes if name not in old_classes]
        classes_deleted = [name for name in old_classes if name not in new_classes]
        classes_modified = []

        for name in set(old_classes.keys()) & set(new_classes.keys()):
            if self._is_modified(old_classes[name], new_classes[name]):
                classes_modified.append(name)

        return SymbolChange(
            file_path=file_path,
            functions_added=funcs_added,
            functions_modified=funcs_modified,
            functions_deleted=funcs_deleted,
            classes_added=classes_added,
            classes_modified=classes_modified,
            classes_deleted=classes_deleted
        )

    def _is_modified(self, old_symbol: Symbol, new_symbol: Symbol) -> bool:
        """
        Check if symbol was modified

        A symbol is considered modified if:
        - Signature changed (parameters, return type)
        - Body changed (line range different)
        """
        # Check signature
        if old_symbol.signature != new_symbol.signature:
            return True

        # Check line range (body size changed)
        old_lines = old_symbol.line_end - old_symbol.line_start
        new_lines = new_symbol.line_end - new_symbol.line_start

        if old_lines != new_lines:
            return True

        return False
```

**File**: `src/codeindex/git/analyzer.py` (add method using SymbolDiffer)
```python
from .symbol_differ import SymbolDiffer

class GitHistoryAnalyzer:
    # ... existing code ...

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.repo = pygit2.Repository(repo_path)
        self.symbol_differ = SymbolDiffer()  # Add this

    def get_symbol_changes(self, commit_sha: str) -> Dict[str, SymbolChange]:
        """
        Get symbol-level changes (functions, classes)

        Uses tree-sitter to parse old/new versions and diff symbols.

        Args:
            commit_sha: Commit SHA

        Returns:
            Dict mapping file_path -> SymbolChange
        """
        commit = self._resolve_ref(commit_sha)

        if not commit.parents:
            # Initial commit - all symbols are added
            return self._get_initial_symbol_changes(commit)

        parent = commit.parents[0]
        diff = parent.tree.diff_to_tree(commit.tree)

        symbol_changes = {}

        for delta in diff.deltas:
            file_path = delta.new_file.path

            # Only process Python files
            if not file_path.endswith('.py'):
                continue

            # Get old and new content
            try:
                old_content = self._get_file_content(parent.tree, file_path)
                new_content = self._get_file_content(commit.tree, file_path)

                # Diff symbols
                change = self.symbol_differ.diff_symbols(
                    old_content,
                    new_content,
                    file_path,
                    language="python"
                )

                symbol_changes[file_path] = change

            except Exception as e:
                # File might not exist in one version
                continue

        return symbol_changes

    def _get_file_content(self, tree: pygit2.Tree, file_path: str) -> str:
        """Get file content from tree"""
        try:
            entry = tree[file_path]
            blob = self.repo[entry.id]
            return blob.data.decode('utf-8')
        except KeyError:
            return ""  # File doesn't exist in this tree
```

**Run All Tests**:
```bash
pytest tests/git/ -v --cov=src/codeindex/git

# Expected: All tests passing, coverage > 90%
```

✅ **End of Day 5**: Symbol-level diff working

---

### Day 6: Performance Optimization + Refactoring

**Morning: Performance Tests** (2 hours)

**File**: `tests/git/test_performance.py`
```python
"""Performance benchmarks for git analyzer"""
import pytest
from codeindex.git.analyzer import GitHistoryAnalyzer

class TestPerformance:
    """Performance benchmarks"""

    def test_get_commits_100(self, large_test_repo, benchmark):
        """Benchmark: 100 commits in < 5 seconds"""
        analyzer = GitHistoryAnalyzer(str(large_test_repo))

        result = benchmark(analyzer.get_commits, "HEAD~100", "HEAD")

        assert len(result) == 100
        assert benchmark.stats['mean'] < 5.0  # < 5 seconds

    def test_get_file_changes_large(self, large_test_repo, benchmark):
        """Benchmark: 50-file commit in < 2 seconds"""
        analyzer = GitHistoryAnalyzer(str(large_test_repo))

        # Find commit with ~50 files
        commit_sha = "..."  # Large commit

        result = benchmark(analyzer.get_file_changes, commit_sha)

        assert len(result) >= 50
        assert benchmark.stats['mean'] < 2.0

    def test_symbol_diff_large_file(self, benchmark):
        """Benchmark: 1000-line file in < 1 second"""
        analyzer = GitHistoryAnalyzer()

        # Create 1000-line Python file
        old_content = "..."
        new_content = "..."

        result = benchmark(
            analyzer.symbol_differ.diff_symbols,
            old_content,
            new_content
        )

        assert benchmark.stats['mean'] < 1.0
```

**Afternoon: Refactoring** (4 hours)
- Extract common methods
- Add error handling
- Improve code readability
- Add docstrings
- Run ruff for linting

```bash
# Refactor while keeping tests green
ruff check src/codeindex/git/
ruff format src/codeindex/git/

# All tests should still pass
pytest tests/git/ -v
```

✅ **End of Day 6**: Refactoring complete (REFACTOR phase done)

---

### Day 7-8: Branch Operations + Integration

**Day 7: Branch Operations** (8 hours)

**File**: `tests/git/test_analyzer.py` (add branch tests)
```python
class TestBranchOperations:
    """Test branch-related operations"""

    def test_get_branch_commits(self, test_repo_with_branches):
        """Test getting all commits on a branch"""
        analyzer = GitHistoryAnalyzer(str(test_repo_with_branches))

        commits = analyzer.get_branch_commits("feature/auth")

        assert len(commits) > 0
        assert all(isinstance(c, CommitInfo) for c in commits)

    def test_get_divergence_point(self, test_repo_with_branches):
        """Test finding merge-base of two branches"""
        analyzer = GitHistoryAnalyzer(str(test_repo_with_branches))

        divergence = analyzer.get_divergence_point("main", "feature/auth")

        assert isinstance(divergence, CommitInfo)
        assert divergence.sha
```

Implement the methods in `analyzer.py`.

**Day 8: Integration Testing** (8 hours)
- Test with real codeindex repository
- Fix edge cases
- Add error handling
- Update documentation

**File**: `tests/git/test_integration.py`
```python
"""Integration tests with real codeindex repo"""
import pytest
from codeindex.git.analyzer import GitHistoryAnalyzer

class TestIntegration:
    """Integration tests"""

    def test_analyze_real_repo(self):
        """Test analyzing actual codeindex repo"""
        analyzer = GitHistoryAnalyzer(".")

        # Get recent commits
        commits = analyzer.get_commits("HEAD~10", "HEAD")
        assert len(commits) <= 10

        # Analyze a commit
        if commits:
            changes = analyzer.get_file_changes(commits[0].sha)
            assert isinstance(changes, dict)

    def test_analyze_with_errors(self):
        """Test error handling"""
        analyzer = GitHistoryAnalyzer(".")

        # Invalid ref
        with pytest.raises(ValueError):
            analyzer.get_commits("INVALID_REF", "HEAD")

        # Non-existent commit
        with pytest.raises(ValueError):
            analyzer.get_file_changes("0" * 40)
```

✅ **End of Day 8**: Integration complete

---

### Day 9-10: Documentation + Wrap-up

**Day 9: Documentation** (8 hours)

**File**: `src/codeindex/git/README_AI.md` (create via codeindex)
```bash
# Generate documentation
codeindex scan src/codeindex/git --fallback

# Manual review and enhancement
```

**File**: `docs/guides/git-analysis.md` (new user guide)
````markdown
# Git Analysis Guide

## Overview

The Git History Analyzer provides tools for analyzing git repository history, including commit metadata extraction, file-level diffs, and symbol-level changes.

## Basic Usage

```python
from codeindex.git.analyzer import GitHistoryAnalyzer

# Initialize with repository path
analyzer = GitHistoryAnalyzer("/path/to/repo")

# Get recent commits
commits = analyzer.get_commits("HEAD~10", "HEAD")

for commit in commits:
    print(f"{commit.short_sha}: {commit.first_line_message}")

# Analyze file changes
changes = analyzer.get_file_changes(commits[0].sha)

for file_path, change in changes.items():
    print(f"{file_path}: +{change.lines_added} -{change.lines_deleted}")

# Analyze symbol changes
symbol_changes = analyzer.get_symbol_changes(commits[0].sha)

for file_path, changes in symbol_changes.items():
    print(f"{file_path}:")
    print(f"  Added: {changes.functions_added}")
    print(f"  Modified: {changes.functions_modified}")
```

## Performance Characteristics

- 100 commits: < 5 seconds
- 50-file commit: < 2 seconds
- Symbol diff for 1000-line file: < 1 second

## API Reference

See module docstrings for detailed API documentation.
````

**Update**: `README.md`, `CHANGELOG.md`

**Day 10: Final Testing + PR**

```bash
# Run all tests
pytest -v --cov=src/codeindex/git --cov-report=term-missing

# Should show:
# - All tests passing
# - Coverage ≥ 90%

# Lint
ruff check src/codeindex/git/

# Update CHANGELOG
# Update README with new features

# Commit
git add .
git commit -m "feat(git): implement git history analyzer

- Add GitHistoryAnalyzer for commit metadata extraction
- Add file-level diff analysis with hunks
- Add symbol-level diff using tree-sitter
- Add branch operations (get_branch_commits, get_divergence_point)
- Comprehensive test suite with 90%+ coverage
- Performance benchmarks met

Relates to Epic 5, Story 5.1.1

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Push and create PR
git push origin feature/epic5-git-analyzer

# Create PR to develop
gh pr create --title "feat: Git History Analyzer (Epic 5 Story 5.1.1)" \
  --body "$(cat <<EOF
## Summary
Implements Git History Analysis Engine for Epic 5.

## Features
- ✅ Commit metadata extraction
- ✅ File-level diff analysis
- ✅ Symbol-level diff using tree-sitter
- ✅ Branch operations

## Testing
- ✅ 50+ tests, all passing
- ✅ Coverage: 92%
- ✅ Performance benchmarks met

## Documentation
- ✅ User guide created
- ✅ API documentation complete
- ✅ README updated

Closes #XXX (Story 5.1.1 issue)
EOF
)"
```

✅ **End of Sprint 1**: Story 5.1.1 complete!

---

## Sprint Retrospective Checklist

### Definition of Done Validation

- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Code coverage ≥ 90%
- [ ] Performance benchmarks met
- [ ] Documentation complete (README, user guide, API docs)
- [ ] CHANGELOG updated
- [ ] Code reviewed and merged to develop
- [ ] No regressions in existing tests

### Code Quality Metrics

```bash
# Run final quality check
pytest --cov=src/codeindex/git --cov-report=html
ruff check src/
mypy src/codeindex/git/

# Expected results:
# - 50+ tests passing
# - Coverage: 90%+
# - No lint errors
# - No type errors
```

### Deliverables

- ✅ Working GitHistoryAnalyzer module
- ✅ SymbolDiffer for symbol-level diff
- ✅ Comprehensive test suite
- ✅ User documentation
- ✅ Performance benchmarks
- ✅ Merged PR to develop

---

## Next Sprint Preview

**Sprint 2 (Week 3-4)**: Story 5.1.2 - Branch Comparison Engine

Will build on top of GitHistoryAnalyzer to create:
- BranchComparator for file and symbol comparison
- Markdown/JSON/console report generation
- Merge conflict prediction

**Estimated Timeline**: 10 development days (same as Story 5.1.1)

---

**Document Status**: ✅ Ready for Sprint 1 Start
**Created**: 2026-02-01
**Story**: 5.1.1 - Git History Analysis Engine
