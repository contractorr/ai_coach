"""CLI entry point for AI Coach."""

import click

from cli.commands import register_all
from cli.config import load_config, setup_logging


@click.group()
@click.version_option(version="0.1.0")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def cli(verbose: bool):
    """AI Coach - Personal professional advisor."""
    config = load_config()
    if verbose:
        config["logging"] = {"level": "DEBUG", "file_level": "DEBUG"}
    setup_logging(config)


register_all(cli)


if __name__ == "__main__":
    cli()
