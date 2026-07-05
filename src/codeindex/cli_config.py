"""CLI commands for configuration and project status.

This module provides commands for initializing configuration files,
checking indexing status, and listing indexable directories.
"""

import sys
from pathlib import Path

import click
from rich.table import Table

from .cli_common import console
from .config import DEFAULT_CONFIG_NAME, Config
from .init_wizard import (
    generate_config_yaml,
    inject_claude_md,
    run_interactive_wizard,
)
from .scanner import find_all_directories


def _update_gitignore(project_dir: Path) -> bool:
    """Add README_AI.md to .gitignore if not already present. Returns True if modified."""
    gitignore = project_dir / ".gitignore"
    marker = "README_AI.md"

    comment = "# codeindex - AI-generated indexes (regenerate with: codeindex scan-all)"
    entry = f"{comment}\nREADME_AI.md\n"

    if gitignore.exists():
        content = gitignore.read_text()
        if marker in content:
            return False
        prefix = "\n" if not content.endswith("\n") else ""
        gitignore.write_text(content + prefix + "\n" + entry)
    else:
        gitignore.write_text(entry)

    return True


def _collect_init_targets(project_dir: Path) -> list[tuple[str, str, str]]:
    """Return ``(action, target, detail)`` for each init mutation target.

    action: ``"create"`` | ``"modify"`` | ``"exists"`` (already in desired state).
    Reflects init's actual mutation set — ``.codeindex.yaml`` + ``CLAUDE.md``
    codeindex-section inject + ``.gitignore`` README_AI.md append. Used by
    ``--dry-run`` to preview (GH #88), replacing the SKILL Step 0 hardcoded bash.
    """
    targets: list[tuple[str, str, str]] = []
    cfg = project_dir / DEFAULT_CONFIG_NAME
    targets.append(("create" if not cfg.exists() else "exists", ".codeindex.yaml", ""))
    claude_md = project_dir / "CLAUDE.md"
    has_section = claude_md.exists() and "## codeindex" in claude_md.read_text()
    targets.append(("exists" if has_section else "modify", "CLAUDE.md", "inject ## codeindex section"))
    gitignore = project_dir / ".gitignore"
    has_entry = gitignore.exists() and "README_AI.md" in gitignore.read_text()
    targets.append(("exists" if has_entry else "modify", ".gitignore", "append README_AI.md"))
    return targets


def _print_post_init_message():
    """Print post-init next steps message."""
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. [cyan]Review .codeindex.yaml[/cyan]    → Verify include/exclude patterns")
    console.print("  2. [cyan]codeindex scan-all[/cyan]        → Generate documentation indexes")
    console.print("  3. [cyan]codeindex status[/cyan]           → Check coverage")
    console.print("\n[dim]Optional:[/dim]")
    console.print("  • [cyan]codeindex hooks install[/cyan]  → Auto-update README_AI.md on commit")
    console.print(
        "  • [dim]Claude Code:[/dim] [cyan]/plugin install codeindex@codeindex-claude[/cyan]"
    )
    console.print("\n[bold]AI enrichment (ADR-008, DeepSeek default):[/bold]")
    console.print("  • [cyan]export CODEINDEX_AI_API_KEY=sk-...[/cyan]   → enable the direct API")
    console.print("  • [cyan]codeindex scan-all --ai[/cyan]          → enrich READMEs via API")
    console.print("  [dim](Prefer claude/opencode CLI? Set `ai_command:` in .codeindex.yaml.)[/dim]")

@click.command()
@click.option("--force", "-f", is_flag=True, help="Overwrite existing config")
@click.option("--yes", "-y", is_flag=True, help="Non-interactive mode with defaults")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output (for CI/CD)")
@click.option("--help-config", is_flag=True, help="Show complete configuration reference")
@click.option(
    "--lang",
    type=click.Choice(["auto", "zh", "en"]),
    default="auto",
    help="Language for the injected CLAUDE.md section (auto = match host)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview mutation targets without writing anything (GH #88)",
)
def init(force: bool, yes: bool, quiet: bool, help_config: bool, lang: str, dry_run: bool = False):
    """Initialize .codeindex.yaml configuration file.

    Interactive wizard guides you through setup with smart defaults.
    Use --yes for non-interactive mode (suitable for automation).
    """
    # Show configuration help if requested
    if help_config:
        from .config_help import show_full_config_help

        show_full_config_help()
        return

    # --dry-run: preview mutation targets, mutate nothing (GH #88).
    # Runs before the exists/force gate so users can preview even with an
    # existing .codeindex.yaml (no --force needed for a read-only preview).
    if dry_run:
        targets = _collect_init_targets(Path.cwd())
        create = [(t, d) for (a, t, d) in targets if a == "create"]
        modify = [(t, d) for (a, t, d) in targets if a == "modify"]
        exists = [(t, d) for (a, t, d) in targets if a == "exists"]
        console.print("[dim]Dry run — no files mutated.[/dim]\n")
        if create:
            console.print("[bold]Would create:[/bold]")
            for t, _ in create:
                console.print(f"  {t}")
        if modify:
            console.print("\n[bold]Would modify:[/bold]")
            for t, d in modify:
                console.print(f"  {t} ({d})" if d else f"  {t}")
        if exists:
            console.print("\n[dim]Already in place:[/dim]")
            for t, _ in exists:
                console.print(f"  [dim]{t}[/dim]")
        return

    config_path = Path.cwd() / DEFAULT_CONFIG_NAME

    if config_path.exists() and not force:
        if not quiet:
            console.print(f"[yellow]Config already exists:[/yellow] {config_path}")
            console.print("Use --force to overwrite")
        return

    project_dir = Path.cwd()

    # Non-interactive mode
    if yes:
        from .init_wizard import (
            calculate_batch_size,
            calculate_parallel_workers,
            count_files,
            detect_frameworks,
            detect_languages,
            get_parser_install_guidance,
            infer_exclude_patterns,
            infer_include_patterns,
        )

        # Auto-detect everything
        detected_languages = detect_languages(project_dir)
        detected_frameworks = detect_frameworks(project_dir, detected_languages)
        include_patterns = infer_include_patterns(project_dir)
        exclude_patterns = infer_exclude_patterns(project_dir)

        file_count = count_files(project_dir, include_patterns)
        parallel_workers = calculate_parallel_workers(file_count)
        batch_size = calculate_batch_size(file_count)

        # Check parser installation
        if not quiet and detected_languages:
            guidance = get_parser_install_guidance(detected_languages)
            if guidance["missing"]:
                console.print(
                    f"[yellow]Warning: Missing parsers for: "
                    f"{', '.join(guidance['missing'])}[/yellow]"
                )
                console.print(
                    f"  Install with: {guidance['install_command']}"
                )

        # Create minimal result
        from .init_wizard import WizardResult

        result = WizardResult(
            detected_languages=detected_languages,
            suggested_patterns={"include": include_patterns, "exclude": exclude_patterns},
            detected_frameworks=detected_frameworks,
            parallel_workers=parallel_workers,
            batch_size=batch_size,
            enable_hooks=False,  # Hooks are opt-in via `codeindex hooks install`
            create_codeindex_md=False,  # Dropped from init (B1/ADR-006); CLAUDE.md is the guide
            # ADR-008: leave ai_command unset so generate_config_yaml emits the
            # direct-API `ai:` section (DeepSeek default). The prior claude-CLI
            # seed (RECOMMENDED_AI_COMMAND) is dead — Claude mass-bans made the
            # `claude` CLI unreliable. AI still activates only on `scan --ai`.
            configure_ai=False,
        )

        # Generate config
        yaml_content = generate_config_yaml(result, project_dir)
        config_path.write_text(yaml_content)

        # Inject codeindex section into the project's CLAUDE.md (project-scoped,
        # never ~/.claude — see ADR-006). Safe default for non-interactive.
        claude_md_path = inject_claude_md(project_dir, lang=lang)
        result.claude_md_injected = True

        # Update .gitignore
        gitignore_updated = _update_gitignore(project_dir)

        if not quiet:
            console.print(f"[green]✓ Created:[/green] {config_path}")
            console.print(f"[green]✓ Injected:[/green] {claude_md_path.name}")
            if gitignore_updated:
                console.print("[green]✓ Updated:[/green] .gitignore (added README_AI.md)")
            _print_post_init_message()

        return

    # Interactive mode needs a TTY. In CI / sandbox / container / piped input
    # (stdin not a TTY), the wizard's click.confirm/prompt calls raise a bare
    # Abort — the user just sees a cryptic "Aborted!" with no hint. Fail fast
    # with an actionable message pointing at --yes (GH #44, issue option 2:
    # explicit error, no silent behavior change).
    if not sys.stdin.isatty():
        raise click.ClickException(
            "codeindex init needs an interactive terminal (stdin is not a TTY "
            "— CI, sandbox, container, or piped input). Re-run with --yes for "
            "non-interactive defaults:  codeindex init --yes"
        )

    # Interactive mode (original behavior enhanced with wizard)
    result = run_interactive_wizard(project_dir)

    # Generate and write configuration
    yaml_content = generate_config_yaml(result, project_dir)
    config_path.write_text(yaml_content)
    result.config_created = True

    # Inject codeindex section into the project's CLAUDE.md if requested.
    # Project-scoped only (never ~/.claude) — see ADR-006.
    if result.inject_claude_md:
        claude_md_path = inject_claude_md(project_dir, lang=lang)
        result.claude_md_injected = True
        console.print(f"[green]✓ Injected:[/green] {claude_md_path.name}")

    # Update .gitignore
    gitignore_updated = _update_gitignore(project_dir)
    if gitignore_updated:
        console.print("[green]✓ Updated:[/green] .gitignore (added README_AI.md)")

    # Success summary
    console.print("\n[green]✓ Setup complete![/green]")
    console.print(f"\n[bold]Created:[/bold] {config_path}")
    _print_post_init_message()

    return result


@click.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
def status(root: Path):
    """Show indexing status for the project."""
    root = root.resolve()
    config = Config.load()

    console.print(f"[bold]Project:[/bold] {root}")
    console.print(f"[bold]Config:[/bold] {DEFAULT_CONFIG_NAME}")

    # Find all directories that should be indexed
    dirs = find_all_directories(root, config)

    if not dirs:
        console.print("[yellow]No indexable directories found[/yellow]")
        return

    # Check which have README_AI.md
    indexed = []
    not_indexed = []

    for d in dirs:
        readme_path = d / config.output_file
        if readme_path.exists():
            indexed.append(d)
        else:
            not_indexed.append(d)

    # Display table
    table = Table(title="Indexing Status")
    table.add_column("Status", style="bold")
    table.add_column("Count")
    table.add_column("Percentage")

    total = len(dirs)
    indexed_count = len(indexed)
    coverage = (indexed_count / total * 100) if total > 0 else 0

    table.add_row("[green]Indexed[/green]", str(indexed_count), f"{coverage:.1f}%")
    table.add_row("[yellow]Not indexed[/yellow]", str(len(not_indexed)), f"{100-coverage:.1f}%")
    table.add_row("Total", str(total), "100%")

    console.print(table)

    if not_indexed and len(not_indexed) <= 10:
        console.print("\n[dim]Not indexed:[/dim]")
        for d in not_indexed[:10]:
            rel = d.relative_to(root)
            console.print(f"  {rel}")


@click.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
def list_dirs(root: Path):
    """List all directories that would be indexed."""
    root = root.resolve()
    config = Config.load()

    dirs = find_all_directories(root, config)

    if not dirs:
        # GH #74: a silent empty result + exit 0 used to be indistinguishable
        # from "nothing to index". If the project actually has source files
        # that don't match ``config.languages``, diagnose the mismatch and
        # exit non-zero so the user (and tooling) know to act.
        from .scanner import language_mismatch_hint

        hint = language_mismatch_hint(root, config)
        if hint:
            raise click.ClickException(hint)
        # Truly empty include roots — keep the historical silent + exit 0
        # so scripts that pipe ``codeindex list-dirs`` to check "anything
        # to index?" continue to work.
        return

    for d in dirs:
        rel = d.relative_to(root)
        print(rel)


_STATUS_GLYPH = {
    "ok": "[green]✓[/green]",
    "warn": "[yellow]⚠[/yellow]",
    "error": "[red]✗[/red]",
    "info": "[dim]·[/dim]",
}


@click.command()
def doctor():
    """Report codeindex health: CLI, parsers, CLAUDE.md, and plugin sync.

    Read-only. Useful when you're unsure whether the CLI, the project config,
    the CLAUDE.md section, and the Claude Code plugin are all in sync — and
    what to upgrade if not.
    """
    from .doctor import has_errors, run_doctor

    findings = run_doctor()

    console.print("\n[bold]codeindex doctor[/bold]\n")

    current_section = None
    fixes: list[str] = []
    for f in findings:
        if f.section != current_section:
            console.print(f"[bold]{f.section}[/bold]")
            current_section = f.section
        glyph = _STATUS_GLYPH.get(f.status, "·")
        console.print(f"  {glyph} {f.message}")
        if f.fix:
            console.print(f"      [dim]→ {f.fix}[/dim]")
            fixes.append(f.fix)

    warn_count = sum(1 for f in findings if f.status == "warn")
    error_count = sum(1 for f in findings if f.status == "error")

    console.print()
    tail = "see suggested commands above."
    if error_count:
        console.print(
            f"[red]{error_count} error(s)[/red], "
            f"[yellow]{warn_count} warning(s)[/yellow] — {tail}"
        )
    elif warn_count:
        console.print(f"[yellow]{warn_count} warning(s)[/yellow] — {tail}")
    else:
        console.print("[green]All clear.[/green]")

    if has_errors(findings):
        raise SystemExit(1)
