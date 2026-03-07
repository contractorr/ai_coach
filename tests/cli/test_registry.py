"""Tests for CLI command registry helpers."""

from click import Group

from cli.commands import COMMAND_GROUPS, STANDALONE_COMMANDS, register_all


def test_register_all_adds_all_commands():
    cli = Group()

    register_all(cli)

    expected = {command.name for command in COMMAND_GROUPS + STANDALONE_COMMANDS}
    assert expected.issubset(set(cli.commands))
