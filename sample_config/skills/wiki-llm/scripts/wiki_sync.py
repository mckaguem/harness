import os
import sys
import json
import subprocess

STATE_FILE = "./wiki/.sync_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"todo": [], "current": None, "history": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"

def get_next_item(state):
    if not state["todo"]:
        state["current"] = None
        save_state(state)
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        return "SYNC_COMPLETE: All modified files have been processed and the wiki is up to date."
    
    state["current"] = state["todo"].pop(0)
    save_state(state)
    
    # Fetch the specific diff context for this file to hand to the LLM
    diff_content = run_command(f"git diff HEAD -- '{state['current']}'")
    # If it's a new untracked file, diff might be empty; get content instead
    if not diff_content or "Error" in diff_content:
        diff_content = "[New or Untracked File detected]"
        
    return f"CURRENT_SYNC_TARGET: {state['current']}\n\n--- GIT DIFF CONTEXT ---\n{diff_content}\n------------------------"

def cmd_init():
    """Finds all modified, staged, and untracked files in the repository."""
    # Get modified and staged files
    mod_files = run_command("git diff --name-only HEAD")
    # Get untracked files
    untracked_files = run_command("git ls-files --others --exclude-standard")
    
    all_files = set()
    if mod_files and "Error" not in mod_files:
        all_files.update(mod_files.splitlines())
    if untracked_files and "Error" not in untracked_files:
        all_files.update(untracked_files.splitlines())
        
    # Ignore the wiki directory itself to prevent feedback loops
    todo_list = [f for f in all_files if f and not f.startswith("wiki/")]
    
    if not todo_list:
        print("NO_CHANGES_DETECTED: Codebase matches git HEAD. No wiki updates required.")
        return

    state = {"todo": todo_list, "current": None, "history": []}
    print(f"Initialized wiki sync session. {len(todo_list)} files require review.")
    print(get_next_item(state))

def cmd_resolve():
    """Marks the current file as processed and moves to the next."""
    state = load_state()
    if not state["current"]:
        print("Error: No active sync session. Run 'init' first.")
        return
    
    state["history"].append(state["current"])
    print(get_next_item(state))

def cmd_status():
    """Checks remaining queue status."""
    state = load_state()
    print(f"Current Target: {state['current']}")
    print(f"Pending Files: {len(state['todo'])}")
    for f in state["todo"]:
        print(f" - {f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/wiki_sync.py [init | resolve | status]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "init":
        cmd_init()
    elif cmd == "resolve":
        cmd_resolve()
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")