"""Ctrl+Q confirmation dialog - documentation only.

This file contains no executable code, only comments describing the
implementation that was added to tui_app.py:

1. Added ModalScreen import and created QuitConfirmDialog class
2. Updated BINDINGS from "quit" to "confirm_quit" 
3. Added action_confirm_quit() method to TextualHarnessApp (shows dialog)
4. Added publish_quit_confirm() method to TextualHarnessApp (emits event)
5. Dialog's on_button_pressed handles Yes/No buttons and escape key

The confirmation flow:
- User presses Ctrl+Q → app.action_confirm_quit() called
- Pushes QuitConfirmDialog as overlay
- User clicks "Yes" or presses 'y' → dialog calls self.app.publish_quit_confirm()
  which emits PROCESS_CONTROL_QUIT_CONFIRM event, then dismisses(True)
- User clicks "No" or presses Esc → dismisses(False), no action taken

"""

