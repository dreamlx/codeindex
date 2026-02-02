"""Tests for Git Hooks CLI module (Epic 6, P3.1, Task 4.1-4.5)."""

import os
from pathlib import Path
from unittest.mock import patch

from codeindex.cli_hooks import (
    HookManager,
    HookStatus,
    backup_existing_hook,
    detect_existing_hooks,
    generate_hook_script,
)


class TestHookManager:
    """Test HookManager class."""

    def test_init_with_repo_path(self, tmp_path):
        """Should initialize with given repository path."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        manager = HookManager(repo_path)

        assert manager.repo_path == repo_path
        assert manager.hooks_dir == repo_path / ".git" / "hooks"

    def test_init_detects_git_repo(self, tmp_path):
        """Should detect git repository from current directory."""
        # Create a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # Change to repo directory
        original_cwd = Path.cwd()
        try:
            os.chdir(repo_path)
            manager = HookManager()
            assert manager.repo_path == repo_path
        finally:
            os.chdir(original_cwd)

    def test_get_hook_status_not_exists(self, tmp_path):
        """Should return NOT_INSTALLED when hook doesn't exist."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        manager = HookManager(repo_path)
        status = manager.get_hook_status("pre-commit")

        assert status == HookStatus.NOT_INSTALLED

    def test_get_hook_status_exists_codeindex(self, tmp_path):
        """Should return INSTALLED when codeindex hook exists."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create hook with codeindex marker
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\n# codeindex-managed hook\necho 'test'")
        hook_file.chmod(0o755)

        manager = HookManager(repo_path)
        status = manager.get_hook_status("pre-commit")

        assert status == HookStatus.INSTALLED

    def test_get_hook_status_exists_custom(self, tmp_path):
        """Should return CUSTOM when non-codeindex hook exists."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create custom hook without codeindex marker
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\necho 'custom hook'")
        hook_file.chmod(0o755)

        manager = HookManager(repo_path)
        status = manager.get_hook_status("pre-commit")

        assert status == HookStatus.CUSTOM

    def test_install_hook(self, tmp_path):
        """Should install hook successfully."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        manager = HookManager(repo_path)
        result = manager.install_hook("pre-commit")

        assert result is True
        assert (hooks_dir / "pre-commit").exists()
        assert (hooks_dir / "pre-commit").stat().st_mode & 0o111  # Executable

    def test_install_hook_with_backup(self, tmp_path):
        """Should backup existing custom hook before installing."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create existing custom hook
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\necho 'old hook'")

        manager = HookManager(repo_path)
        result = manager.install_hook("pre-commit", backup=True)

        assert result is True
        assert (hooks_dir / "pre-commit.backup").exists()
        assert (hooks_dir / "pre-commit").exists()

    def test_uninstall_hook(self, tmp_path):
        """Should uninstall codeindex hook."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create codeindex hook
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\n# codeindex-managed hook\necho 'test'")

        manager = HookManager(repo_path)
        result = manager.uninstall_hook("pre-commit")

        assert result is True
        assert not (hooks_dir / "pre-commit").exists()

    def test_uninstall_hook_restores_backup(self, tmp_path):
        """Should restore backup when uninstalling."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create codeindex hook and backup
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\n# codeindex-managed hook\necho 'new'")

        backup_file = hooks_dir / "pre-commit.backup"
        backup_file.write_text("#!/bin/bash\necho 'old hook'")

        manager = HookManager(repo_path)
        result = manager.uninstall_hook("pre-commit", restore_backup=True)

        assert result is True
        assert (hooks_dir / "pre-commit").exists()
        assert (hooks_dir / "pre-commit").read_text() == "#!/bin/bash\necho 'old hook'"
        assert not (hooks_dir / "pre-commit.backup").exists()

    def test_list_all_hooks_status(self, tmp_path):
        """Should list status of all hooks."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create one codeindex hook
        (hooks_dir / "pre-commit").write_text("# codeindex-managed hook\n")

        # Create one custom hook
        (hooks_dir / "post-commit").write_text("#!/bin/bash\necho 'custom'\n")

        manager = HookManager(repo_path)
        statuses = manager.list_all_hooks()

        assert statuses["pre-commit"] == HookStatus.INSTALLED
        assert statuses["post-commit"] == HookStatus.CUSTOM
        assert statuses["pre-push"] == HookStatus.NOT_INSTALLED


class TestHookGeneration:
    """Test hook script generation."""

    def test_generate_pre_commit_hook(self):
        """Should generate valid pre-commit hook script."""
        script = generate_hook_script("pre-commit")

        assert "#!/bin/zsh" in script or "#!/bin/bash" in script
        assert "codeindex-managed hook" in script
        assert "ruff" in script.lower() or "lint" in script.lower()

    def test_generate_post_commit_hook(self):
        """Should generate valid post-commit hook script."""
        script = generate_hook_script("post-commit")

        assert "#!/bin/zsh" in script or "#!/bin/bash" in script
        assert "codeindex-managed hook" in script
        assert "README_AI.md" in script or "codeindex" in script

    def test_generate_hook_with_config(self):
        """Should customize hook based on config."""
        config = {
            "lint_enabled": False,
            "auto_update": True,
        }

        script = generate_hook_script("pre-commit", config=config)

        assert "codeindex-managed hook" in script


class TestBackupAndRestore:
    """Test backup and restore functionality."""

    def test_backup_existing_hook(self, tmp_path):
        """Should create backup of existing hook."""
        hooks_dir = tmp_path
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\necho 'original'")

        backup_path = backup_existing_hook(hook_file)

        assert backup_path.exists()
        assert backup_path.name == "pre-commit.backup"
        assert backup_path.read_text() == "#!/bin/bash\necho 'original'"

    def test_backup_with_existing_backup(self, tmp_path):
        """Should handle existing backup files."""
        hooks_dir = tmp_path
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\necho 'new'")

        # Create existing backup
        (hooks_dir / "pre-commit.backup").write_text("#!/bin/bash\necho 'old'")

        backup_path = backup_existing_hook(hook_file)

        # Should create timestamped backup
        assert backup_path.exists()
        assert "pre-commit.backup" in backup_path.name


class TestDetection:
    """Test hook detection."""

    def test_detect_existing_hooks(self, tmp_path):
        """Should detect all existing hooks."""
        hooks_dir = tmp_path
        (hooks_dir / "pre-commit").write_text("#!/bin/bash\necho 'test'")
        (hooks_dir / "post-commit").write_text("#!/bin/bash\necho 'test'")

        detected = detect_existing_hooks(hooks_dir)

        assert "pre-commit" in detected
        assert "post-commit" in detected
        assert len(detected) == 2

    def test_detect_ignores_samples(self, tmp_path):
        """Should ignore .sample files."""
        hooks_dir = tmp_path
        (hooks_dir / "pre-commit").write_text("#!/bin/bash\necho 'test'")
        (hooks_dir / "pre-commit.sample").write_text("#!/bin/bash\necho 'sample'")

        detected = detect_existing_hooks(hooks_dir)

        assert "pre-commit" in detected
        assert "pre-commit.sample" not in detected


class TestCLIIntegration:
    """Test CLI command integration."""

    @patch("subprocess.run")
    def test_cli_hooks_install_command(self, mock_run, tmp_path):
        """Should provide hooks install CLI command."""
        # This will be implemented with Click
        # Just verify the interface exists
        pass

    @patch("subprocess.run")
    def test_cli_hooks_status_command(self, mock_run, tmp_path):
        """Should provide hooks status CLI command."""
        # This will be implemented with Click
        pass
