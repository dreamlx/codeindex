"""Git Hooks management module for codeindex.

Epic 6, P3.1: Automate Git Hooks installation and management.

This module provides:
- HookManager: Manage Git hooks installation/uninstall
- Hook script generation with templates
- Backup and restore existing hooks
- Detect and merge with existing hooks
"""

import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import click

from .cli_common import console


class HookStatus(Enum):
    """Status of a Git hook."""

    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"  # codeindex-managed
    CUSTOM = "custom"  # User's custom hook


class HookManager:
    """Manage Git hooks for codeindex."""

    CODEINDEX_MARKER = "# codeindex-managed hook"
    SUPPORTED_HOOKS = ["pre-commit", "pre-push"]
    # GH #167: hooks removed from the product. Still uninstallable (cleanup
    # of installs from older codeindex), and surfaced as leftovers by
    # `hooks status` so they don't sit silent (dead wrapper = one Python
    # startup per commit, errors buried in ~/.codeindex/hooks/).
    RETIRED_HOOKS = ["post-commit"]

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize HookManager.

        Args:
            repo_path: Path to Git repository. If None, uses current directory.
        """
        if repo_path is None:
            repo_path = self._find_git_repo()

        self.repo_path = Path(repo_path)
        self.hooks_dir = self.repo_path / ".git" / "hooks"

        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        # Create hooks directory if it doesn't exist
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    def _find_git_repo(self) -> Path:
        """Find Git repository from current directory."""
        current = Path.cwd()

        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        raise ValueError("Not in a git repository")

    def get_hook_status(self, hook_name: str) -> HookStatus:
        """
        Get status of a hook.

        Args:
            hook_name: Name of hook (e.g., "pre-commit")

        Returns:
            HookStatus indicating current status
        """
        hook_path = self.hooks_dir / hook_name

        if not hook_path.exists():
            return HookStatus.NOT_INSTALLED

        content = hook_path.read_text()

        if self.CODEINDEX_MARKER in content:
            return HookStatus.INSTALLED
        else:
            return HookStatus.CUSTOM

    def install_hook(
        self, hook_name: str, backup: bool = True, force: bool = False
    ) -> bool:
        """
        Install codeindex hook.

        Args:
            hook_name: Name of hook to install
            backup: Whether to backup existing hook
            force: Overwrite existing codeindex hook

        Returns:
            True if successful, False otherwise
        """
        if hook_name not in self.SUPPORTED_HOOKS:
            raise ValueError(f"Unsupported hook: {hook_name}")

        hook_path = self.hooks_dir / hook_name
        status = self.get_hook_status(hook_name)

        # Backup existing hook if requested
        if status == HookStatus.CUSTOM and backup:
            backup_existing_hook(hook_path)

        # Don't overwrite codeindex hook unless force=True
        if status == HookStatus.INSTALLED and not force:
            return True

        # Generate and write hook script
        script = generate_hook_script(hook_name)
        hook_path.write_text(script)
        hook_path.chmod(0o755)  # Make executable

        # Ensure hook-common.sh is installed (used by pre-commit/pre-push)
        self._ensure_hook_common()

        return True

    def _ensure_hook_common(self) -> None:
        """Copy hook-common.sh to .git/hooks/ if bundled version exists."""
        common_dest = self.hooks_dir / "hook-common.sh"
        # Source from scripts/hooks/ in the repo
        common_src = self.repo_path / "scripts" / "hooks" / "hook-common.sh"
        if common_src.exists():
            shutil.copy(common_src, common_dest)
            common_dest.chmod(0o755)

    def uninstall_hook(
        self, hook_name: str, restore_backup: bool = True
    ) -> bool:
        """
        Uninstall codeindex hook.

        Args:
            hook_name: Name of hook to uninstall
            restore_backup: Whether to restore backup if exists

        Returns:
            True if successful, False otherwise
        """
        hook_path = self.hooks_dir / hook_name
        status = self.get_hook_status(hook_name)

        # Only uninstall codeindex-managed hooks
        if status != HookStatus.INSTALLED:
            return False

        # Remove hook
        hook_path.unlink()

        # Restore backup if requested and exists
        if restore_backup:
            backup_path = self.hooks_dir / f"{hook_name}.backup"
            if backup_path.exists():
                shutil.copy(backup_path, hook_path)
                backup_path.unlink()

        return True

    def list_all_hooks(self) -> dict[str, HookStatus]:
        """
        List status of all supported hooks.

        Returns:
            Dictionary mapping hook name to status
        """
        statuses = {}
        for hook_name in self.SUPPORTED_HOOKS:
            statuses[hook_name] = self.get_hook_status(hook_name)
        return statuses


def generate_hook_script(
    hook_name: str, config: Optional[dict] = None
) -> str:
    """
    Generate hook script content.

    Args:
        hook_name: Name of hook (e.g., "pre-commit")
        config: Optional configuration for customization

    Returns:
        Hook script as string
    """
    config = config or {}

    if hook_name == "pre-commit":
        return _generate_pre_commit_script(config)
    elif hook_name == "pre-push":
        return _generate_pre_push_script(config)
    else:
        raise ValueError(f"Unsupported hook: {hook_name}")


def _generate_pre_commit_script(config: dict) -> str:
    """Generate pre-commit hook script."""
    lint_enabled = config.get("lint_enabled", True)

    script = """#!/usr/bin/env bash
# codeindex-managed hook
# Pre-commit hook for codeindex
# L1: Lint check (ruff)
# L2: Forbid debug code (print/breakpoint)

set -e

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[0;33m'
NC='\\033[0m' # No Color

# Try to activate virtual environment if exists
REPO_ROOT=$(git rev-parse --show-toplevel)
if [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
    source "$REPO_ROOT/.venv/bin/activate"
elif [ -f "$REPO_ROOT/venv/bin/activate" ]; then
    source "$REPO_ROOT/venv/bin/activate"
fi

echo "🔍 Running pre-commit checks..."

# Get staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    echo "${GREEN}✓ No Python files to check${NC}"
    exit 0
fi

echo "   Checking files: $(echo $STAGED_PY_FILES | wc -w | tr -d ' ') Python files"
"""

    if lint_enabled:
        script += """
# ============================================
# L1: Ruff lint check
# ============================================
echo "\\n${YELLOW}[L1] Running ruff lint...${NC}"

# Try venv ruff first, then system ruff
RUFF_CMD=""
if [ -f "$REPO_ROOT/.venv/bin/ruff" ]; then
    RUFF_CMD="$REPO_ROOT/.venv/bin/ruff"
elif command -v ruff &> /dev/null; then
    RUFF_CMD="ruff"
else
    echo "${RED}✗ ruff not found. Install with: pip install ruff${NC}"
    exit 1
fi

# Check only staged files
STAGED_FILES_ARRAY=()
while IFS= read -r file; do
    if [ -f "$file" ]; then
        STAGED_FILES_ARRAY+=("$file")
    fi
done < <(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$' || true)

if [ ${#STAGED_FILES_ARRAY[@]} -eq 0 ]; then
    echo "${GREEN}✓ No files to lint${NC}"
else
    if ! $RUFF_CMD check "${STAGED_FILES_ARRAY[@]}"; then
        echo "\\n${RED}✗ Lint errors found. Fix them before committing.${NC}"
        echo "   Run: ruff check --fix src/"
        exit 1
    fi
    echo "${GREEN}✓ Lint check passed${NC}"
fi
"""

    script += """
# Note: Debug code detection (print/breakpoint/pdb) is now handled by
# ruff rules T201 (print) and T100 (debugger) in the lint check above.
# Per-file-ignores in pyproject.toml exempt CLI files.

# ============================================
# All checks passed
# ============================================
echo "\\n${GREEN}✓ All pre-commit checks passed!${NC}\\n"
exit 0
"""

    return script


def _generate_pre_push_script(config: dict) -> str:
    """Generate pre-push hook script."""
    return """#!/usr/bin/env bash
# codeindex-managed hook
# Pre-push hook for codeindex

echo "🚀 Running pre-push checks..."

# Add your pre-push checks here
# Example: run tests before push

echo "✓ Pre-push checks passed"
exit 0
"""


def backup_existing_hook(hook_path: Path) -> Path:
    """
    Backup existing hook file.

    Args:
        hook_path: Path to hook file

    Returns:
        Path to backup file
    """
    backup_path = hook_path.parent / f"{hook_path.name}.backup"

    # If backup already exists, use timestamped name
    if backup_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = hook_path.parent / f"{hook_path.name}.backup.{timestamp}"

    shutil.copy(hook_path, backup_path)
    return backup_path


def detect_existing_hooks(hooks_dir: Path) -> list[str]:
    """
    Detect existing hooks in hooks directory.

    Args:
        hooks_dir: Path to .git/hooks directory

    Returns:
        List of hook names that exist (excluding .sample files)
    """
    existing = []

    if not hooks_dir.exists():
        return existing

    for file in hooks_dir.iterdir():
        # Skip .sample files and backup files
        if file.suffix in [".sample", ".backup"]:
            continue

        # Skip if file name contains .backup (timestamped backups)
        if ".backup" in file.name:
            continue

        # Skip if it's a directory
        if file.is_dir():
            continue

        # It's a hook file
        existing.append(file.name)

    return existing


def install_hook(hook_name: str, repo_path: Optional[Path] = None) -> bool:
    """
    Install a specific hook.

    Args:
        hook_name: Name of hook to install
        repo_path: Path to repository

    Returns:
        True if successful
    """
    manager = HookManager(repo_path)
    return manager.install_hook(hook_name, backup=True)


def uninstall_hook(hook_name: str, repo_path: Optional[Path] = None) -> bool:
    """
    Uninstall a specific hook.

    Args:
        hook_name: Name of hook to uninstall
        repo_path: Path to repository

    Returns:
        True if successful
    """
    manager = HookManager(repo_path)
    return manager.uninstall_hook(hook_name, restore_backup=True)


# ============================================================================
# CLI Commands
# ============================================================================


@click.group()
def hooks():
    """Manage Git hooks for codeindex."""
    pass


@hooks.command()
@click.option(
    "--all",
    "install_all",
    is_flag=True,
    help="Install all supported hooks",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing codeindex hooks",
)
@click.argument("hook_name", required=False)
def install(hook_name: Optional[str], install_all: bool, force: bool):
    """Install Git hooks for codeindex.

    Examples:
        codeindex hooks install pre-commit
        codeindex hooks install --all
        codeindex hooks install --all --force
    """
    try:
        manager = HookManager()

        hooks_to_install = []
        if install_all:
            hooks_to_install = manager.SUPPORTED_HOOKS
        elif hook_name:
            if hook_name not in manager.SUPPORTED_HOOKS:
                console.print(
                    f"[red]✗[/red] Unsupported hook: {hook_name}",
                    style="red",
                )
                console.print(
                    f"  Supported hooks: {', '.join(manager.SUPPORTED_HOOKS)}"
                )
                raise click.Abort()
            hooks_to_install = [hook_name]
        else:
            console.print(
                "[yellow]Usage:[/yellow] codeindex hooks install <hook-name> or --all"
            )
            raise click.Abort()

        console.print("\n[bold]Installing Git Hooks[/bold]\n")

        installed_count = 0
        skipped_count = 0
        backed_up = []

        for hook in hooks_to_install:
            status = manager.get_hook_status(hook)

            if status == HookStatus.CUSTOM:
                backup_path = manager.hooks_dir / f"{hook}.backup"
                backed_up.append(f"{hook} → {backup_path.name}")

            result = manager.install_hook(hook, backup=True, force=force)

            if result:
                if status == HookStatus.INSTALLED and not force:
                    console.print(f"  [dim]→ {hook}: already installed (skipped)[/dim]")
                    skipped_count += 1
                else:
                    console.print(f"  [green]✓[/green] {hook}: installed")
                    installed_count += 1
            else:
                console.print(f"  [red]✗[/red] {hook}: failed")

        console.print()

        if backed_up:
            console.print("[yellow]Backups created:[/yellow]")
            for backup in backed_up:
                console.print(f"  {backup}")
            console.print()

        if installed_count > 0:
            console.print(
                f"[green]✓[/green] Successfully installed {installed_count} hook(s)\n"
            )
        if skipped_count > 0:
            console.print(
                f"[dim]→ Skipped {skipped_count} already installed hook(s)[/dim]\n"
            )

    except ValueError as e:
        console.print(f"[red]✗[/red] Error: {e}", style="red")
        raise click.Abort()


@hooks.command()
@click.option(
    "--all",
    "uninstall_all",
    is_flag=True,
    help="Uninstall all codeindex hooks",
)
@click.option(
    "--keep-backup",
    is_flag=True,
    help="Don't restore backup when uninstalling",
)
@click.argument("hook_name", required=False)
def uninstall(hook_name: Optional[str], uninstall_all: bool, keep_backup: bool):
    """Uninstall codeindex Git hooks.

    Examples:
        codeindex hooks uninstall pre-commit
        codeindex hooks uninstall --all
        codeindex hooks uninstall --all --keep-backup
    """
    try:
        manager = HookManager()

        hooks_to_uninstall = []
        if uninstall_all:
            # Only uninstall codeindex-managed hooks
            statuses = manager.list_all_hooks()
            hooks_to_uninstall = [
                name
                for name, status in statuses.items()
                if status == HookStatus.INSTALLED
            ]
            # Retired leftovers are ours too — clean them with the rest
            hooks_to_uninstall += [
                name
                for name in manager.RETIRED_HOOKS
                if name not in hooks_to_uninstall
                and manager.get_hook_status(name) == HookStatus.INSTALLED
            ]
        elif hook_name:
            hooks_to_uninstall = [hook_name]
        else:
            console.print(
                "[yellow]Usage:[/yellow] codeindex hooks uninstall <hook-name> or --all"
            )
            raise click.Abort()

        if not hooks_to_uninstall:
            console.print("[yellow]→[/yellow] No codeindex hooks to uninstall\n")
            return

        console.print("\n[bold]Uninstalling Git Hooks[/bold]\n")

        uninstalled_count = 0
        restored = []

        for hook in hooks_to_uninstall:
            status = manager.get_hook_status(hook)

            if status != HookStatus.INSTALLED:
                console.print(f"  [dim]→ {hook}: not installed (skipped)[/dim]")
                continue

            backup_path = manager.hooks_dir / f"{hook}.backup"
            has_backup = backup_path.exists()

            result = manager.uninstall_hook(hook, restore_backup=not keep_backup)

            if result:
                console.print(f"  [green]✓[/green] {hook}: uninstalled")
                uninstalled_count += 1

                if has_backup and not keep_backup:
                    restored.append(f"{hook} ← {backup_path.name}")

        console.print()

        if restored:
            console.print("[green]Backups restored:[/green]")
            for restore in restored:
                console.print(f"  {restore}")
            console.print()

        console.print(
            f"[green]✓[/green] Successfully uninstalled {uninstalled_count} hook(s)\n"
        )

    except ValueError as e:
        console.print(f"[red]✗[/red] Error: {e}", style="red")
        raise click.Abort()


@hooks.command()
def status():
    """Show status of Git hooks."""
    try:
        manager = HookManager()
        statuses = manager.list_all_hooks()

        console.print("\n[bold]Git Hooks Status[/bold]\n")

        # Status indicators
        status_icons = {
            HookStatus.INSTALLED: "[green]✓[/green]",
            HookStatus.CUSTOM: "[yellow]⚠[/yellow]",
            HookStatus.NOT_INSTALLED: "[dim]○[/dim]",
        }

        status_labels = {
            HookStatus.INSTALLED: "[green]installed[/green]",
            HookStatus.CUSTOM: "[yellow]custom[/yellow]",
            HookStatus.NOT_INSTALLED: "[dim]not installed[/dim]",
        }

        for hook_name in manager.SUPPORTED_HOOKS:
            status = statuses[hook_name]
            icon = status_icons[status]
            label = status_labels[status]

            console.print(f"  {icon} {hook_name}: {label}")

            # Show backup info if exists
            if status in [HookStatus.INSTALLED, HookStatus.CUSTOM]:
                backup_path = manager.hooks_dir / f"{hook_name}.backup"
                if backup_path.exists():
                    console.print(f"     [dim]└─ backup: {backup_path.name}[/dim]")

        console.print()

        # Retired-hook leftovers (GH #167): dead wrappers from older
        # installs — silent on every commit, so surface them here.
        for name in manager.RETIRED_HOOKS:
            hook_path = manager.hooks_dir / name
            if hook_path.exists():
                try:
                    content = hook_path.read_text()
                except OSError:
                    continue  # unreadable — status is informational, don't crash
                if manager.CODEINDEX_MARKER in content:
                    console.print(
                        f"[yellow]⚠[/yellow] {name}: leftover from a removed "
                        "codeindex feature — does nothing but still runs on "
                        f"every commit. Remove with "
                        f"[bold]codeindex hooks uninstall {name}[/bold]"
                    )

        # Summary
        installed = sum(1 for s in statuses.values() if s == HookStatus.INSTALLED)
        custom = sum(1 for s in statuses.values() if s == HookStatus.CUSTOM)

        if installed > 0:
            console.print(f"[green]→[/green] {installed} codeindex hook(s) installed")
        if custom > 0:
            console.print(
                f"[yellow]→[/yellow] {custom} custom hook(s) detected\n"
                f"   [dim]Use 'codeindex hooks install --force' to overwrite[/dim]"
            )

        console.print()

    except ValueError as e:
        console.print(f"[red]✗[/red] Error: {e}", style="red")
        raise click.Abort()
