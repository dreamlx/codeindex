"""CLI entry point for codeindex."""

import click


@click.group()
@click.version_option()
def main():
    """codeindex - AI-native code indexing tool for large codebases."""
    pass


# Register commands from specialized modules
from .cli_config import init, list_dirs, status
from .cli_scan import scan, scan_all
from .cli_symbols import affected, index, symbols
from .cli_tech_debt import tech_debt

main.add_command(scan)
main.add_command(scan_all)
main.add_command(init)
main.add_command(status)
main.add_command(list_dirs)
main.add_command(index)
main.add_command(symbols)
main.add_command(affected)
main.add_command(tech_debt)


if __name__ == "__main__":
    main()
