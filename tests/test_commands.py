"""Tests for slash-command handlers (/exit, /quit)."""

from unittest.mock import patch
import pytest


class TestCmdExit:
    """Tests for the /exit command handler."""

    @patch("builtins.print")
    def test_returns_true_to_break_loop(self, mock_print):
        from commands import _cmd_exit
        result = _cmd_exit("")
        assert result is True

    @patch("builtins.print")
    def test_calls_print_system_with_goodbye_message(self, mock_print):
        from commands import _cmd_exit
        with patch('commands.print_system') as mock_ps:
            _cmd_exit("")
            mock_ps.assert_called_once()

    @patch("builtins.print")
    def test_returns_true_for_non_empty_rest(self, mock_print):
        from commands import _cmd_exit
        result = _cmd_exit("  ")
        assert result is True


class TestCmdQuit:
    """Tests for the /quit command handler."""

    @patch("builtins.print")
    def test_returns_true_to_break_loop(self, mock_print):
        from commands import _cmd_exit
        result = _cmd_exit("")
        assert result is True

    @patch("builtins.print")
    def test_calls_print_system_with_goodbye_message(self, mock_print):
        from commands import _cmd_exit
        with patch('commands.print_system') as mock_ps:
            _cmd_exit("")
            mock_ps.assert_called_once()

    @patch("builtins.print")
    def test_returns_true_for_non_empty_rest(self, mock_print):
        from commands import _cmd_exit
        result = _cmd_exit("  ")
        assert result is True


class TestCommandRegistry:
    """Tests for COMMANDS registry."""

    def test_commands_dict_exists(self):
        from commands import COMMANDS
        assert isinstance(COMMANDS, dict)

    def test_exit_command_registered(self):
        from commands import COMMANDS
        assert 'exit' in COMMANDS
        assert callable(COMMANDS['exit'])

    def test_quit_command_registered(self):
        from commands import COMMANDS
        assert 'quit' in COMMANDS
        assert callable(COMMANDS['quit'])
