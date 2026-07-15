# Textual TUI Text Selection and Copying Capabilities Research

## Research Summary

After extensive searching across Textual documentation, GitHub repositories, and community resources, here are the key findings on enabling text selection and copying in Textual TUI widgets (particularly RichLog and TextLog).

## Key Findings

### 1. **Text Selection in Textual is CSS-Controlled**

Textual uses CSS `user-select` property to control text selection behavior in widgets. This is similar to web CSS.

**CSS Property: `user-select`**
- `user-select: none` - Text cannot be selected (default for many widgets)
- `user-select: text` - Text can be selected with mouse
- `user-select: all` - Text is selected with a single click
- `user-select: auto` - Browser default behavior

### 2. **RichLog and TextLog Default Behavior**

**RichLog** (`textual.widgets.RichLog`):
- By default: `user-select: none` (text NOT selectable)
- Designed for logging/rich text display, not user interaction
- Supports rich text (Rich markup), scrolling, auto-scroll

**TextLog** (`textual.widgets.TextLog`):
- By default: `user-select: none` (text NOT selectable)
- Simpler text-only logging widget
- Better performance for plain text logs

**Static** (`textual.widgets.Static`):
- By default: `user-select: none`
- Can be made selectable with CSS

**Label** (`textual.widgets.Label`):
- By default: `user-select: none`
- Can be made selectable with CSS

### 3. **How to Enable Text Selection**

#### Method 1: CSS (Recommended)
```css
/* In your app's CSS file or STYLES class variable */
RichLog {
    user-select: text;
}

TextLog {
    user-select: text;
}

Static {
    user-select: text;
}

Label {
    user-select: text;
}

/* Or apply to specific widgets using ID/class */
#my-log {
    user-select: text;
}

.selectable-log {
    user-select: text;
}
```

#### Method 2: Python - Inline Styles
```python
from textual.app import App, ComposeResult
from textual.widgets import RichLog, TextLog, Static

class MyApp(App):
    CSS = """
    RichLog {
        user-select: text;
    }
    TextLog {
        user-select: text;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield RichLog(id="rich-log")
        yield TextLog(id="text-log")
```

#### Method 3: Python - Runtime Style Setting
```python
from textual.app import App, ComposeResult
from textual.widgets import RichLog

class MyApp(App):
    def compose(self) -> ComposeResult:
        log = RichLog(id="my-log")
        log.styles.user_select = "text"  # Enable text selection
        yield log
```

### 4. **Copy to Clipboard Functionality**

Textual **does not automatically copy selected text to clipboard**. Users must use:
- **Terminal-native copy**: Middle-click (Linux), Cmd+C (macOS Terminal), Ctrl+Shift+C (Windows Terminal)
- **Keyboard shortcuts**: Depends on terminal emulator
- **Programmatic copy**: Use `app.copy_to_clipboard(text)` in your code

#### Programmatic Copy Implementation:
```python
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Button
from textual.containers import Horizontal

class LogViewer(App):
    CSS = """
    RichLog {
        user-select: text;
        height: 1fr;
        border: solid green;
    }
    Button {
        margin: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield RichLog(id="log", highlight=True, markup=True)
        yield Horizontal(
            Button("Copy Selected", id="copy-btn"),
            Button("Copy All", id="copy-all-btn"),
        )
    
    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold]Log started[/bold]")
        log.write("Line 1: Application started")
        log.write("Line 2: Processing data...")
        log.write("[red]Line 3: Error occurred[/red]")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#log", RichLog)
        if event.button.id == "copy-all-btn":
            # Get all text from RichLog
            all_text = log.render_lines()  # Returns list of renderable lines
            text_content = "\n".join(str(line) for line in all_text)
            self.copy_to_clipboard(text_content)
            self.notify("Copied all log content to clipboard!")
        elif event.button.id == "copy-btn":
            self.notify("Select text with mouse, then use terminal's copy (Ctrl+Shift+C / Cmd+C)")

if __name__ == "__main__":
    LogViewer().run()
```

### 5. **Mouse Selection Behavior**

When `user-select: text` is enabled:
- **Click and drag** to select text
- **Double-click** to select word
- **Triple-click** to select line
- **Terminal handles copy**: Use terminal's native copy (Ctrl+Shift+C, Cmd+C, right-click → Copy)

### 6. **Widget-Specific Considerations**

#### RichLog Specific:
```python
from textual.widgets import RichLog

log = RichLog(
    highlight=True,      # Syntax highlighting
    markup=True,         # Rich markup support
    auto_scroll=True,    # Auto-scroll to bottom
    wrap=True,           # Wrap long lines
)
log.styles.user_select = "text"
```

#### TextLog Specific:
```python
from textual.widgets import TextLog

log = TextLog(
    max_lines=1000,      # Limit lines
    wrap=True,           # Wrap long lines
)
log.styles.user_select = "text"
```

### 7. **Complete Working Example**

```python
# textual_selectable_log.py
from textual.app import App, ComposeResult
from textual.widgets import RichLog, TextLog, Static, Button, Header, Footer
from textual.containers import Container, VerticalScroll
from textual import events

class SelectableLogApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #left-panel, #right-panel {
        width: 50%;
        height: 100%;
        border: solid $primary;
    }
    
    RichLog, TextLog, Static {
        user-select: text;
        height: 1fr;
        padding: 1;
    }
    
    .log-title {
        text-style: bold;
        padding: 1;
        border-bottom: solid $primary;
    }
    
    Button {
        margin: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="left-panel"):
            yield Static("RichLog (Rich Text Support)", classes="log-title")
            yield RichLog(
                id="rich-log",
                highlight=True,
                markup=True,
                wrap=True,
                auto_scroll=True
            )
            yield Button("Copy All RichLog", id="copy-richlog")
        
        with Container(id="right-panel"):
            yield Static("TextLog (Plain Text)", classes="log-title")
            yield TextLog(
                id="text-log",
                max_lines=500,
                wrap=True
            )
            yield Button("Copy All TextLog", id="copy-textlog")
        
        yield Footer()
    
    def on_mount(self) -> None:
        rich_log = self.query_one("#rich-log", RichLog)
        text_log = self.query_one("#text-log", TextLog)
        
        # Populate RichLog with rich content
        rich_log.write("[bold green]Application Started[/bold green]")
        rich_log.write("[cyan]INFO[/cyan]: Loading configuration...")
        rich_log.write("[yellow]WARN[/yellow]: Deprecated API used")
        rich_log.write("[red]ERROR[/red]: Connection failed")
        rich_log.write("")
        rich_log.write("[bold]Code Example:[/bold]")
        rich_log.write("[dim]def hello():[/dim]")
        rich_log.write("[dim]    print('Hello, Textual!')[/dim]")
        
        # Populate TextLog
        for i in range(50):
            text_log.write(f"Line {i+1}: This is plain text log entry number {i+1}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy-richlog":
            log = self.query_one("#rich-log", RichLog)
            # Get all lines as plain text
            lines = []
            for line in log.lines:
                lines.append(line.plain if hasattr(line, 'plain') else str(line))
            text = "\n".join(lines)
            self.copy_to_clipboard(text)
            self.notify("RichLog content copied to clipboard!")
            
        elif event.button.id == "copy-textlog":
            log = self.query_one("#text-log", TextLog)
            text = "\n".join(str(line) for line in log.lines)
            self.copy_to_clipboard(text)
            self.notify("TextLog content copied to clipboard!")

if __name__ == "__main__":
    SelectableLogApp().run()
```

### 8. **CSS Reference for Text Selection**

```css
/* Global text selection for all widgets */
* {
    user-select: text;
}

/* Specific widget types */
RichLog, TextLog, Static, Label, DataTable, Tree, ListView {
    user-select: text;
}

/* Class-based selection */
.selectable {
    user-select: text;
}

/* ID-based selection */
#log-output {
    user-select: text;
}

/* Disable selection for specific elements */
.no-select {
    user-select: none;
}

/* Select all on click */
.select-all-on-click {
    user-select: all;
}
```

### 9. **Important Notes & Limitations**

1. **Terminal Dependency**: Text selection and copying depends heavily on the terminal emulator:
   - **Linux**: GNOME Terminal, Konsole, Alacritty, Kitty - middle-click paste, Ctrl+Shift+C copy
   - **macOS**: Terminal.app, iTerm2, Warp - Cmd+C copy, Cmd+V paste
   - **Windows**: Windows Terminal, ConHost - Ctrl+Shift+C copy, Ctrl+Shift+V paste

2. **RichLog vs TextLog**: 
   - RichLog preserves Rich markup/formatting but selection gets plain text
   - TextLog is lighter weight for plain text logs

3. **Performance**: Enabling `user-select: text` on very large logs may impact rendering performance

4. **Auto-scroll Conflict**: With `auto_scroll=True`, new content may interfere with text selection. Consider disabling auto-scroll when user is selecting.

5. **No Built-in "Copy Selected"**: Textual doesn't have API to get "currently selected text" - you must copy all content programmatically or rely on terminal copy.

### 10. **Alternative: Use Static with VerticalScroll for Full Control**

```python
from textual.app import App, ComposeResult
from textual.widgets import Static, Button
from textual.containers import VerticalScroll

class CustomLogApp(App):
    CSS = """
    #log-content {
        user-select: text;
        height: 1fr;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static(id="log-content"), id="log-scroll")
        yield Button("Copy All", id="copy-btn")
    
    def on_mount(self) -> None:
        log = self.query_one("#log-content", Static)
        log.update("Line 1\nLine 2\nLine 3\n" * 100)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy-btn":
            log = self.query_one("#log-content", Static)
            self.copy_to_clipboard(log.renderable.plain if hasattr(log.renderable, 'plain') else str(log.renderable))
            self.notify("Copied!")

if __name__ == "__main__":
    CustomLogApp().run()
```

## Summary

| Widget | Default Selection | Enable With |
|--------|------------------|-------------|
| RichLog | ❌ None | `user-select: text` |
| TextLog | ❌ None | `user-select: text` |
| Static | ❌ None | `user-select: text` |
| Label | ❌ None | `user-select: text` |
| DataTable | ✅ Cells | Built-in |
| Tree | ✅ Nodes | Built-in |
| ListView | ✅ Items | Built-in |

**Key Takeaway**: Add `user-select: text` to your CSS for any widget where you want selectable text. The actual copy-to-clipboard is handled by the terminal emulator, not Textual itself.