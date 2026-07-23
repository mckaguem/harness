"""Tests for slash-command handlers (/exit, /quit)."""

from unittest.mock import patch
import pytest


class TestCmdExit:
    """Tests for the /exit command handler."""

    def test_returns_false_to_show_confirmation_first(self):
        from harness_core.commands import cmd_exit
        result = cmd_exit("")
        assert result is False

    @patch('harness_core.commands.exit_quit.print_system')
    def test_calls_print_system_with_goodbye_message(self, mock_ps):
        # Import after patching
        from harness_core.commands import cmd_exit
        cmd_exit("")
        mock_ps.assert_called_once()

    def test_returns_false_for_non_empty_rest(self):
        from harness_core.commands import cmd_exit
        result = cmd_exit("  ")
        assert result is False


class TestCmdQuit:
    """Tests for the /quit command handler."""

    def test_returns_false_to_show_confirmation_first(self):
        from harness_core.commands import cmd_exit
        result = cmd_exit("")
        assert result is False

    @patch('harness_core.commands.exit_quit.print_system')
    def test_calls_print_system_with_goodbye_message(self, mock_ps):
        # Import after patching
        from harness_core.commands import cmd_exit
        cmd_exit("")
        mock_ps.assert_called_once()

    def test_returns_false_for_non_empty_rest(self):
        from harness_core.commands import cmd_exit
        result = cmd_exit("  ")
        assert result is False


class TestCommandRegistry:
    """Tests for COMMANDS registry."""

    def test_commands_dict_exists(self):
        from harness_core.commands import COMMANDS
        assert isinstance(COMMANDS, dict)

    def test_exit_command_registered(self):
        from harness_core.commands import COMMANDS
        assert 'exit' in COMMANDS
        assert callable(COMMANDS['exit'])

    def test_quit_command_registered(self):
        from harness_core.commands import COMMANDS
        assert 'quit' in COMMANDS
        assert callable(COMMANDS['quit'])
