# Phase 1 Story Planning: Epic 5 Infrastructure Layer

**Epic**: Intelligent Branch Management
**Phase**: 1 - Infrastructure Layer (v0.4.0)
**Target Release**: 2026 Q1
**Status**: 📋 Planning

---

## 📋 Phase 1 Overview

**Goal**: Build foundational infrastructure for branch comparison and code similarity detection.

**Stories in Phase 1**:
- ✅ Story 5.1.1: Git History Analysis Engine
- ✅ Story 5.1.2: Branch Comparison Engine
- ✅ Story 5.2.1a: Incremental Duplicate Detection (Commit/PR Level)

**Out of Scope for Phase 1**:
- LLM-based semantic analysis (Phase 2)
- Cross-branch duplicate detection (Phase 2)
- Full project scan (Phase 3)
- Auto PR creation (Phase 3)

---

## Story 5.1.1: Git History Analysis Engine

**User Story**:
> As a developer, I want to analyze git history to understand code evolution, so that I can track when and how code changed across branches.

### Acceptance Criteria

**AC1**: Extract commit metadata
```python
# Given a commit SHA or range
result = git_analyzer.get_commits("HEAD~10", "HEAD")

# Then return structured commit info
assert len(result.commits) == 10
assert result.commits[0].sha
assert result.commits[0].author
assert result.commits[0].message
assert result.commits[0].timestamp
assert result.commits[0].files_changed
```

**AC2**: Analyze file changes in commits
```python
# Given a commit
changes = git_analyzer.get_file_changes("abc123")

# Then return detailed file diff info
assert "src/auth/login.py" in changes
assert changes["src/auth/login.py"].lines_added == 15
assert changes["src/auth/login.py"].lines_deleted == 3
assert changes["src/auth/login.py"].hunks  # List of diff hunks
```

**AC3**: Track symbol-level changes
```python
# Given a commit that modified functions
symbol_changes = git_analyzer.get_symbol_changes("abc123")

# Then identify which functions were modified
assert "login" in symbol_changes["src/auth/login.py"].functions_modified
assert "validate_token" in symbol_changes["src/auth/login.py"].functions_added
```

**AC4**: Performance requirements
- ✅ Analyze 100 commits in < 5 seconds
- ✅ Extract file changes for 50-file commit in < 2 seconds
- ✅ Symbol-level diff for 1000-line file in < 1 second

### Technical Design

#### Component: `GitHistoryAnalyzer`

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import pygit2  # Or GitPython

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

@dataclass
class FileChange:
    """File-level changes in a commit"""
    file_path: str
    status: str  # "added" | "modified" | "deleted" | "renamed"
    lines_added: int
    lines_deleted: int
    hunks: List['DiffHunk']
    old_path: Optional[str] = None  # For renamed files

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
class SymbolChange:
    """Symbol-level changes"""
    file_path: str
    functions_added: List[str]
    functions_modified: List[str]
    functions_deleted: List[str]
    classes_added: List[str]
    classes_modified: List[str]
    classes_deleted: List[str]

class GitHistoryAnalyzer:
    """Analyze git history and extract commit metadata"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.repo = pygit2.Repository(repo_path)

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
            List of CommitInfo objects
        """
        pass

    def get_file_changes(self, commit_sha: str) -> Dict[str, FileChange]:
        """
        Get file-level changes for a commit

        Args:
            commit_sha: Commit SHA

        Returns:
            Dict mapping file_path -> FileChange
        """
        pass

    def get_symbol_changes(self, commit_sha: str) -> Dict[str, SymbolChange]:
        """
        Get symbol-level changes (functions, classes)

        Uses tree-sitter to parse old/new versions and diff symbols.

        Args:
            commit_sha: Commit SHA

        Returns:
            Dict mapping file_path -> SymbolChange
        """
        pass

    def get_branch_commits(self, branch: str) -> List[CommitInfo]:
        """Get all commits on a branch"""
        pass

    def get_divergence_point(
        self,
        branch_a: str,
        branch_b: str
    ) -> CommitInfo:
        """Find where two branches diverged (merge-base)"""
        pass
```

#### Integration with Tree-sitter

```python
from codeindex.parser import SymbolParser

class SymbolDiffer:
    """Diff symbols between two versions of a file"""

    def __init__(self):
        self.parser = SymbolParser()

    def diff_symbols(
        self,
        old_content: str,
        new_content: str,
        language: str = "python"
    ) -> SymbolChange:
        """
        Compare symbols between old and new file versions

        Returns:
            SymbolChange with added/modified/deleted symbols
        """
        old_symbols = self.parser.parse_content(old_content, language)
        new_symbols = self.parser.parse_content(new_content, language)

        # Build symbol maps
        old_map = {s.name: s for s in old_symbols}
        new_map = {s.name: s for s in new_symbols}

        # Calculate differences
        added = [name for name in new_map if name not in old_map]
        deleted = [name for name in old_map if name not in new_map]

        # Modified: exists in both but content changed
        modified = []
        for name in set(old_map.keys()) & set(new_map.keys()):
            if old_map[name].signature != new_map[name].signature:
                modified.append(name)

        return SymbolChange(
            file_path="",
            functions_added=added,
            functions_modified=modified,
            functions_deleted=deleted,
            classes_added=[],
            classes_modified=[],
            classes_deleted=[]
        )
```

### Test Cases (TDD)

#### Test File: `tests/test_git_history_analyzer.py`

```python
import pytest
from pathlib import Path
from codeindex.git_analyzer import GitHistoryAnalyzer, CommitInfo

class TestGitHistoryAnalyzer:
    """Test git history analysis functionality"""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create analyzer with test repo"""
        # Create test git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        # Initialize git, create test commits
        return GitHistoryAnalyzer(str(repo_path))

    def test_get_commits_single(self, analyzer):
        """Test extracting single commit metadata"""
        commits = analyzer.get_commits("HEAD~1", "HEAD")

        assert len(commits) == 1
        assert isinstance(commits[0], CommitInfo)
        assert commits[0].sha
        assert commits[0].author
        assert commits[0].message

    def test_get_commits_range(self, analyzer):
        """Test extracting commit range"""
        commits = analyzer.get_commits("HEAD~10", "HEAD")

        assert len(commits) == 10
        assert commits[0].timestamp > commits[-1].timestamp  # Reverse chronological

    def test_get_file_changes_added(self, analyzer):
        """Test detecting added files"""
        # Create commit that adds a file
        changes = analyzer.get_file_changes("test_commit_sha")

        assert "new_file.py" in changes
        assert changes["new_file.py"].status == "added"
        assert changes["new_file.py"].lines_added > 0
        assert changes["new_file.py"].lines_deleted == 0

    def test_get_file_changes_modified(self, analyzer):
        """Test detecting modified files"""
        changes = analyzer.get_file_changes("test_commit_sha")

        assert "existing.py" in changes
        assert changes["existing.py"].status == "modified"
        assert changes["existing.py"].lines_added > 0
        assert changes["existing.py"].hunks  # Has diff hunks

    def test_get_symbol_changes_function_added(self, analyzer):
        """Test detecting new functions"""
        symbol_changes = analyzer.get_symbol_changes("test_commit_sha")

        assert "src/auth.py" in symbol_changes
        assert "new_login" in symbol_changes["src/auth.py"].functions_added

    def test_get_symbol_changes_function_modified(self, analyzer):
        """Test detecting modified functions"""
        symbol_changes = analyzer.get_symbol_changes("test_commit_sha")

        assert "validate" in symbol_changes["src/auth.py"].functions_modified

    def test_performance_100_commits(self, analyzer, benchmark):
        """Performance: 100 commits in < 5 seconds"""
        result = benchmark(analyzer.get_commits, "HEAD~100", "HEAD")
        assert len(result) == 100
        assert benchmark.stats['mean'] < 5.0

    def test_get_divergence_point(self, analyzer):
        """Test finding branch merge-base"""
        divergence = analyzer.get_divergence_point("feature/a", "feature/b")

        assert isinstance(divergence, CommitInfo)
        assert divergence.sha  # Has valid commit SHA
```

### Implementation Checklist

**Phase 1: Basic Commit Extraction** (2 days)
- [ ] Set up pygit2/GitPython wrapper
- [ ] Implement `get_commits()` for commit range
- [ ] Extract commit metadata (SHA, author, message, timestamp)
- [ ] Write tests for commit extraction
- [ ] Performance test: 100 commits < 5s

**Phase 2: File-level Diff** (2 days)
- [ ] Implement `get_file_changes()` for single commit
- [ ] Parse diff hunks with line numbers
- [ ] Handle added/modified/deleted/renamed files
- [ ] Write tests for file changes
- [ ] Performance test: 50-file commit < 2s

**Phase 3: Symbol-level Diff** (3 days)
- [ ] Integrate with existing SymbolParser
- [ ] Implement `SymbolDiffer.diff_symbols()`
- [ ] Detect added/modified/deleted functions
- [ ] Detect added/modified/deleted classes
- [ ] Write tests for symbol changes
- [ ] Performance test: 1000-line file < 1s

**Phase 4: Branch Operations** (2 days)
- [ ] Implement `get_branch_commits()`
- [ ] Implement `get_divergence_point()` (merge-base)
- [ ] Write tests for branch operations
- [ ] Integration tests with real repo

**Total Estimate**: 9 development days

### Dependencies
- External: `pygit2` or `GitPython`
- Internal: `codeindex.parser.SymbolParser` (already exists)

---

## Story 5.1.2: Branch Comparison Engine

**User Story**:
> As a developer, I want to compare two branches to see what changed, so that I can understand differences before merging or cherry-picking.

### Acceptance Criteria

**AC1**: Compare files between branches
```python
# Given two branches
comparison = branch_comparator.compare("main", "feature/auth")

# Then return file-level differences
assert comparison.files_only_in_source  # List of files
assert comparison.files_only_in_target
assert comparison.files_modified
assert comparison.files_identical
```

**AC2**: Compare symbols between branches
```python
# Given two branches
symbol_diff = branch_comparator.compare_symbols("main", "feature/auth")

# Then return symbol-level differences
assert "src/auth.py" in symbol_diff
assert "new_login" in symbol_diff["src/auth.py"].functions_only_in_target
```

**AC3**: Generate comparison report
```python
# Given a comparison
report = branch_comparator.generate_report("main", "feature/auth", format="markdown")

# Then generate readable report
assert "## Branch Comparison" in report
assert "Files modified: 5" in report
assert "Functions added: 3" in report
```

**AC4**: Performance requirements
- ✅ Compare 100 files in < 10 seconds
- ✅ Symbol-level comparison for 50 files in < 15 seconds

### Technical Design

#### Component: `BranchComparator`

```python
from dataclasses import dataclass
from typing import List, Dict, Set
from enum import Enum

class FileStatus(Enum):
    """File status in branch comparison"""
    ONLY_IN_SOURCE = "only_in_source"
    ONLY_IN_TARGET = "only_in_target"
    MODIFIED = "modified"
    IDENTICAL = "identical"

@dataclass
class BranchComparison:
    """Result of comparing two branches"""
    source_branch: str
    target_branch: str
    divergence_commit: str  # Merge-base SHA

    files_only_in_source: List[str]
    files_only_in_target: List[str]
    files_modified: List[str]
    files_identical: List[str]

    commits_ahead: int  # Target is N commits ahead of source
    commits_behind: int  # Target is N commits behind source

@dataclass
class SymbolDiff:
    """Symbol-level differences for a file"""
    file_path: str

    functions_only_in_source: List[str]
    functions_only_in_target: List[str]
    functions_modified: List[str]
    functions_identical: List[str]

    classes_only_in_source: List[str]
    classes_only_in_target: List[str]
    classes_modified: List[str]
    classes_identical: List[str]

class BranchComparator:
    """Compare two git branches"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.git_analyzer = GitHistoryAnalyzer(repo_path)

    def compare(
        self,
        source_branch: str,
        target_branch: str,
        path_filter: Optional[str] = None
    ) -> BranchComparison:
        """
        Compare two branches at file level

        Args:
            source_branch: Source branch (e.g., "main")
            target_branch: Target branch (e.g., "feature/auth")
            path_filter: Optional path to compare (e.g., "src/")

        Returns:
            BranchComparison with file-level differences
        """
        pass

    def compare_symbols(
        self,
        source_branch: str,
        target_branch: str,
        path_filter: Optional[str] = None
    ) -> Dict[str, SymbolDiff]:
        """
        Compare two branches at symbol level

        Returns:
            Dict mapping file_path -> SymbolDiff
        """
        pass

    def generate_report(
        self,
        source_branch: str,
        target_branch: str,
        format: str = "markdown"
    ) -> str:
        """
        Generate human-readable comparison report

        Args:
            format: "markdown" | "json" | "console"

        Returns:
            Formatted report string
        """
        pass

    def get_merge_conflicts(
        self,
        source_branch: str,
        target_branch: str
    ) -> List[str]:
        """
        Predict potential merge conflicts

        Returns:
            List of file paths that may conflict
        """
        pass
```

#### Report Template: Markdown Format

```markdown
# Branch Comparison: {source_branch} → {target_branch}

**Divergence Point**: {divergence_commit}
**Commits Ahead**: {commits_ahead}
**Commits Behind**: {commits_behind}

## Summary

| Metric | Count |
|--------|-------|
| Files modified | {files_modified_count} |
| Files added in target | {files_only_in_target_count} |
| Files deleted from source | {files_only_in_source_count} |
| Files identical | {files_identical_count} |

## Modified Files

{for file in files_modified}
### {file}

- Lines added: {lines_added}
- Lines deleted: {lines_deleted}
- Functions added: {functions_added}
- Functions modified: {functions_modified}

{endfor}

## Files Only in {target_branch}

{files_only_in_target}

## Potential Merge Conflicts

{potential_conflicts}
```

### Test Cases (TDD)

#### Test File: `tests/test_branch_comparator.py`

```python
import pytest
from codeindex.branch_comparator import BranchComparator, BranchComparison

class TestBranchComparator:
    """Test branch comparison functionality"""

    @pytest.fixture
    def comparator(self, test_repo):
        """Create comparator with test repo"""
        return BranchComparator(str(test_repo))

    def test_compare_identical_branches(self, comparator):
        """Test comparing branch with itself"""
        result = comparator.compare("main", "main")

        assert len(result.files_modified) == 0
        assert len(result.files_only_in_target) == 0
        assert result.commits_ahead == 0
        assert result.commits_behind == 0

    def test_compare_with_new_files(self, comparator):
        """Test detecting new files in target branch"""
        # Setup: feature branch has new file
        result = comparator.compare("main", "feature/new-auth")

        assert "src/auth/oauth.py" in result.files_only_in_target
        assert result.commits_ahead > 0

    def test_compare_with_modified_files(self, comparator):
        """Test detecting modified files"""
        result = comparator.compare("main", "feature/refactor")

        assert "src/auth/login.py" in result.files_modified

    def test_compare_symbols(self, comparator):
        """Test symbol-level comparison"""
        symbol_diff = comparator.compare_symbols("main", "feature/new-auth")

        assert "src/auth/login.py" in symbol_diff
        diff = symbol_diff["src/auth/login.py"]
        assert "oauth_login" in diff.functions_only_in_target

    def test_generate_markdown_report(self, comparator):
        """Test markdown report generation"""
        report = comparator.generate_report("main", "feature/auth", format="markdown")

        assert "# Branch Comparison" in report
        assert "main" in report
        assert "feature/auth" in report
        assert "## Summary" in report

    def test_generate_json_report(self, comparator):
        """Test JSON report generation"""
        import json
        report = comparator.generate_report("main", "feature/auth", format="json")

        data = json.loads(report)
        assert "source_branch" in data
        assert "files_modified" in data

    def test_performance_100_files(self, comparator, benchmark):
        """Performance: 100 files in < 10 seconds"""
        result = benchmark(comparator.compare, "main", "feature/large")
        assert benchmark.stats['mean'] < 10.0
```

### Implementation Checklist

**Phase 1: File-level Comparison** (3 days)
- [ ] Implement `compare()` for file-level diff
- [ ] Detect files_only_in_source/target
- [ ] Detect files_modified
- [ ] Calculate commits ahead/behind
- [ ] Write tests for file comparison

**Phase 2: Symbol-level Comparison** (3 days)
- [ ] Implement `compare_symbols()` using SymbolDiffer
- [ ] Handle multiple files in parallel
- [ ] Write tests for symbol comparison
- [ ] Performance optimization

**Phase 3: Report Generation** (2 days)
- [ ] Implement markdown report template
- [ ] Implement JSON report output
- [ ] Implement console (rich) output
- [ ] Write tests for report generation

**Phase 4: Advanced Features** (2 days)
- [ ] Implement `get_merge_conflicts()` prediction
- [ ] Add path filtering support
- [ ] Integration tests
- [ ] Performance tests

**Total Estimate**: 10 development days

---

## Story 5.2.1a: Incremental Duplicate Detection (Commit/PR Level)

**User Story**:
> As a developer, I want to detect duplicate code in my current commit/PR, so that I can refactor before merging.

### Acceptance Criteria

**AC1**: Detect duplicates in single commit
```python
# Given a commit
result = dup_detector.detect_in_commit("HEAD")

# Then return duplicate function pairs
assert len(result.duplicates) >= 0
for dup in result.duplicates:
    assert dup.similarity_score >= 0.7  # Threshold
    assert dup.function_a.file_path
    assert dup.function_b.file_path
```

**AC2**: Detect duplicates in PR
```python
# Given a PR number
result = dup_detector.detect_in_pr(123)

# Then analyze all commits in PR
assert result.pr_number == 123
assert result.commits_analyzed > 0
```

**AC3**: Generate duplication report
```python
# Given detection results
report = dup_detector.generate_report(result, format="markdown")

# Then generate actionable report
assert "## Duplicate Code Detected" in report
assert "Refactoring Suggestion" in report
```

**AC4**: Performance requirements
- ✅ Detect duplicates in <500 line commit in < 30 seconds
- ✅ Handle commits up to 5000 lines
- ✅ Skip if commit too small (<10 lines changed)

### Technical Design

#### Component: `DuplicateDetector`

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class DetectionMethod(Enum):
    """Duplicate detection method"""
    AST_ONLY = "ast"           # Fast, structural only
    SEMANTIC = "semantic"      # LLM-based (not in Phase 1)
    HYBRID = "hybrid"          # AST first, LLM if needed (Phase 2)

@dataclass
class FunctionInfo:
    """Function metadata"""
    file_path: str
    function_name: str
    line_start: int
    line_end: int
    code: str
    ast_hash: str  # AST structural hash

@dataclass
class DuplicatePair:
    """A pair of similar functions"""
    function_a: FunctionInfo
    function_b: FunctionInfo
    similarity_score: float  # 0.0-1.0
    similarity_method: DetectionMethod
    recommendation: str  # "extract_common" | "reuse_existing" | "keep_separate"

@dataclass
class DuplicationReport:
    """Result of duplicate detection"""
    scope: str  # "commit:abc123" | "pr:123"
    commits_analyzed: int
    functions_analyzed: int
    duplicates: List[DuplicatePair]
    timestamp: datetime

class DuplicateDetector:
    """Detect duplicate/similar code"""

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        method: DetectionMethod = DetectionMethod.AST_ONLY,
        min_function_lines: int = 10
    ):
        self.threshold = similarity_threshold
        self.method = method
        self.min_lines = min_function_lines
        self.git_analyzer = GitHistoryAnalyzer()

    def detect_in_commit(
        self,
        commit_sha: str = "HEAD"
    ) -> DuplicationReport:
        """
        Detect duplicates within a single commit

        Strategy:
        1. Extract functions added/modified in commit
        2. Compare each pair using AST similarity
        3. Report pairs above threshold

        Args:
            commit_sha: Commit to analyze

        Returns:
            DuplicationReport with duplicate pairs
        """
        pass

    def detect_in_pr(
        self,
        pr_number: int
    ) -> DuplicationReport:
        """
        Detect duplicates in a PR (all commits)

        Uses GitHub/GitLab API to get PR commits.
        """
        pass

    def _extract_functions(
        self,
        file_changes: Dict[str, FileChange]
    ) -> List[FunctionInfo]:
        """
        Extract functions from changed files

        Returns:
            List of functions added/modified
        """
        pass

    def _calculate_ast_similarity(
        self,
        func_a: FunctionInfo,
        func_b: FunctionInfo
    ) -> float:
        """
        Calculate AST structural similarity

        Algorithm:
        1. Parse both functions to AST
        2. Normalize variable names (a -> var1, b -> var2)
        3. Calculate tree edit distance
        4. Return similarity score 0.0-1.0
        """
        pass

    def generate_report(
        self,
        result: DuplicationReport,
        format: str = "markdown"
    ) -> str:
        """Generate human-readable report"""
        pass
```

#### AST Similarity Algorithm

```python
from tree_sitter import Node
from typing import Tuple

class ASTSimilarityCalculator:
    """Calculate structural similarity between ASTs"""

    def similarity(self, ast_a: Node, ast_b: Node) -> float:
        """
        Calculate similarity between two AST nodes

        Algorithm: Tree edit distance normalized to 0.0-1.0

        Returns:
            Similarity score (1.0 = identical, 0.0 = completely different)
        """
        # Normalize ASTs (rename variables to generic names)
        norm_a = self._normalize_ast(ast_a)
        norm_b = self._normalize_ast(ast_b)

        # Calculate tree edit distance
        distance = self._tree_edit_distance(norm_a, norm_b)

        # Normalize to 0.0-1.0 based on tree size
        max_size = max(self._tree_size(norm_a), self._tree_size(norm_b))
        similarity = 1.0 - (distance / max_size)

        return similarity

    def _normalize_ast(self, node: Node) -> Node:
        """
        Normalize AST by replacing identifiers with generic names

        Example:
            def login(username, password) -> def func(var1, var2)
        """
        pass

    def _tree_edit_distance(self, node_a: Node, node_b: Node) -> int:
        """
        Calculate tree edit distance using Zhang-Shasha algorithm

        Returns:
            Number of edits needed to transform tree A to tree B
        """
        pass

    def _tree_size(self, node: Node) -> int:
        """Count nodes in tree"""
        pass
```

### Test Cases (TDD)

#### Test File: `tests/test_duplicate_detector.py`

```python
import pytest
from codeindex.duplicate_detector import (
    DuplicateDetector,
    DuplicationReport,
    DetectionMethod
)

class TestDuplicateDetector:
    """Test duplicate code detection"""

    @pytest.fixture
    def detector(self):
        """Create detector with default settings"""
        return DuplicateDetector(
            similarity_threshold=0.7,
            method=DetectionMethod.AST_ONLY
        )

    def test_detect_no_duplicates(self, detector, test_repo):
        """Test commit with no duplicates"""
        # Create commit with unique functions
        result = detector.detect_in_commit("test_commit_unique")

        assert len(result.duplicates) == 0
        assert result.functions_analyzed > 0

    def test_detect_exact_duplicate(self, detector, test_repo):
        """Test detecting exact duplicate functions"""
        # Create commit with identical functions
        result = detector.detect_in_commit("test_commit_duplicate")

        assert len(result.duplicates) == 1
        dup = result.duplicates[0]
        assert dup.similarity_score == 1.0  # Exact match

    def test_detect_similar_functions(self, detector, test_repo):
        """Test detecting similar but not identical functions"""
        # Create commit with 80% similar functions
        result = detector.detect_in_commit("test_commit_similar")

        assert len(result.duplicates) == 1
        dup = result.duplicates[0]
        assert 0.7 <= dup.similarity_score < 1.0

    def test_skip_small_functions(self, detector, test_repo):
        """Test skipping functions below min_lines threshold"""
        detector.min_lines = 10

        # Commit has 5-line duplicate functions
        result = detector.detect_in_commit("test_commit_tiny")

        assert len(result.duplicates) == 0  # Skipped

    def test_detect_in_pr(self, detector, mock_github_api):
        """Test detecting duplicates across PR commits"""
        result = detector.detect_in_pr(123)

        assert result.pr_number == 123
        assert result.commits_analyzed > 1

    def test_ast_similarity_identical(self, detector):
        """Test AST similarity for identical code"""
        code_a = """
def login(user, pwd):
    if validate(user):
        return create_token(user)
    return None
"""
        code_b = """
def authenticate(username, password):
    if validate(username):
        return create_token(username)
    return None
"""
        # Same structure, different variable names
        func_a = parse_function(code_a)
        func_b = parse_function(code_b)

        similarity = detector._calculate_ast_similarity(func_a, func_b)
        assert similarity > 0.9  # Very similar structure

    def test_generate_markdown_report(self, detector, test_repo):
        """Test markdown report generation"""
        result = detector.detect_in_commit("test_commit_duplicate")
        report = detector.generate_report(result, format="markdown")

        assert "## Duplicate Code Detected" in report
        assert "Similarity:" in report
        assert "Recommendation:" in report

    def test_performance_500_lines(self, detector, benchmark):
        """Performance: 500-line commit in < 30 seconds"""
        result = benchmark(
            detector.detect_in_commit,
            "test_commit_500_lines"
        )
        assert benchmark.stats['mean'] < 30.0
```

### CLI Integration

```bash
# Detect duplicates in current commit
codeindex find-duplicates --commit HEAD

# Detect in specific commit
codeindex find-duplicates --commit abc123

# Detect in PR (requires GitHub token)
codeindex find-duplicates --pr 123

# Options
--threshold 0.8           # Similarity threshold (default: 0.7)
--method ast              # Detection method: ast only
--min-lines 15            # Minimum function size (default: 10)
--output report.md        # Save report to file
--format markdown         # markdown | json | console
```

### Implementation Checklist

**Phase 1: Git Integration** (2 days)
- [ ] Implement `detect_in_commit()` basic flow
- [ ] Extract functions from FileChange objects
- [ ] Filter by min_function_lines
- [ ] Write tests for function extraction

**Phase 2: AST Similarity** (4 days)
- [ ] Implement AST normalization (variable renaming)
- [ ] Implement tree edit distance calculation
- [ ] Implement similarity score calculation
- [ ] Write tests for AST similarity
- [ ] Test with real Python code samples

**Phase 3: Report Generation** (2 days)
- [ ] Implement markdown report template
- [ ] Implement JSON report output
- [ ] Implement console (rich) output
- [ ] Write tests for report generation

**Phase 4: CLI Integration** (2 days)
- [ ] Add `find-duplicates` command to CLI
- [ ] Add command-line options
- [ ] Add PR support (GitHub API)
- [ ] Integration tests
- [ ] Performance tests

**Total Estimate**: 10 development days

---

## Phase 1 Timeline

**Total Development Days**: 29 days (6 weeks)

**Sprint Breakdown**:

### Sprint 1 (Week 1-2): Git History Analysis
- Story 5.1.1: Git History Analysis Engine
- Deliverable: Working git analyzer with symbol-level diff

### Sprint 2 (Week 3-4): Branch Comparison
- Story 5.1.2: Branch Comparison Engine
- Deliverable: Branch comparison CLI and reports

### Sprint 3 (Week 5-6): Duplicate Detection
- Story 5.2.1a: Incremental Duplicate Detection
- Deliverable: Commit-level duplicate detection CLI

### Sprint 4 (Week 7): Integration & Testing
- Integration testing across all components
- Performance optimization
- Documentation updates
- Prepare for v0.4.0 release

---

## Configuration Changes

### `.codeindex.yaml` Extensions for Phase 1

```yaml
# Git analysis configuration
git:
  default_branch: "main"
  ignore_merge_commits: true

# Branch comparison configuration
branch_comparison:
  path_filters:
    - "src/**"
    - "!tests/**"

  report:
    format: "markdown"  # markdown | json | console
    output: "branch_comparison.md"

# Duplicate detection configuration (Phase 1: AST-only)
duplication:
  similarity_threshold: 0.7
  detection_method: "ast"  # Only "ast" in Phase 1

  min_function_lines: 10

  ignore:
    - "test/*"
    - "*/migrations/*"

  report:
    format: "markdown"
    output: "duplicates.md"
```

---

## Success Criteria for Phase 1

**Functional Requirements**:
- ✅ Can analyze git history and extract commit metadata
- ✅ Can compare two branches at file and symbol level
- ✅ Can detect duplicate code in commits using AST similarity
- ✅ All CLI commands working with proper error handling

**Quality Requirements**:
- ✅ All tests passing (target: 200+ new tests)
- ✅ Code coverage ≥ 85% for new components
- ✅ Performance benchmarks met
- ✅ Documentation complete

**Deliverables**:
- ✅ Working v0.4.0 release
- ✅ Updated README with new commands
- ✅ Comprehensive test suite
- ✅ Performance benchmark results

---

## Phase 2 Preview

**What comes next in Phase 2** (v0.5.0):
- Story 5.2.1b: Cross-Branch Duplicate Detection (LLM-based)
- Story 5.3.1: LLM Integration for Semantic Analysis
- Story 5.3.2: Similarity Clustering and Grouping

**Key difference from Phase 1**:
- Phase 1: Local, fast, AST-based (no LLM costs)
- Phase 2: Semantic, accurate, LLM-powered (pay-per-token)

---

**Document Status**: ✅ Ready for Review
**Next Step**: Validate Phase 1 plan, then start Sprint 1
**Created**: 2026-02-01
