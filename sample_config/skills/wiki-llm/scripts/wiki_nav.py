import os
import sys
import json
import re

STATE_FILE = "./wiki/.search_state.json"
PAGES_DIR = "./wiki/pages"
INDEX_DIR = "./wiki/index"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"stack": [], "visited": [], "current": None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def extract_yaml_header(file_path):
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    with open(file_path, 'r') as f:
        content = f.read()
    
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        return f"---\n{match.group(1)}\n---"
    return "Warning: No YAML header found."

def extract_links(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        content = f.read()
    
    links = re.findall(r'\]\((?:\.\./pages/|pages/)?([a-zA-Z0-9_\-\.]+)\)', content)
    
    resolved_paths = []
    for link in links:
        full_path = os.path.join(PAGES_DIR, link)
        if os.path.exists(full_path):
            resolved_paths.append(full_path)
    return resolved_paths

def get_next_available(state):
    while state["stack"]:
        candidate = state["stack"].pop()
        if candidate not in state["visited"]:
            state["current"] = candidate
            save_state(state)
            header = extract_yaml_header(candidate)
            return f"TARGET_PAGE: {candidate}\n{header}"
            
    state["current"] = None
    save_state(state)
    return "SEARCH_COMPLETE: No more relevant pages left in the traversal stack."

def cmd_init(keywords):
    stack = []
    if not os.path.exists(INDEX_DIR):
        print(f"Error: Index directory {INDEX_DIR} does not exist. Initialize your wiki first.")
        sys.exit(1)
        
    for file in os.listdir(INDEX_DIR):
        if file.endswith('.md'):
            file_path = os.path.join(INDEX_DIR, file)
            with open(file_path, 'r') as f:
                content = f.read().lower()
                
            if any(kw.lower() in file.lower() or kw.lower() in content for kw in keywords):
                stack.extend(extract_links(file_path))
                
    stack = list(dict.fromkeys(stack))
    state = {"stack": stack, "visited": [], "current": None}
    print(f"Initialized search with {len(stack)} root pages found in indices.")
    print(get_next_available(state))

def cmd_expand():
    state = load_state()
    curr = state["current"]
    if not curr:
        print("Error: No active search session. Run 'init' first.")
        return
    state["visited"].append(curr)
    
    child_links = extract_links(curr)
    for link in child_links:
        if link not in state["visited"] and link not in state["stack"]:
            state["stack"].append(link)
            
    print(get_next_available(state))

def cmd_prune():
    state = load_state()
    curr = state["current"]
    if not curr:
        print("Error: No active search session. Run 'init' first.")
        return
    state["visited"].append(curr)
    print(get_next_available(state))

def cmd_read():
    state = load_state()
    curr = state["current"]
    if curr and os.path.exists(curr):
        with open(curr, 'r') as f:
            print(f.read())
    else:
        print("Error: No active page to read.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python wiki_nav.py [init <keywords...> | expand | prune | read]")
        sys.exit(1)
        
        cmd = sys.argv[1]
    if cmd == "init":
        cmd_init(sys.argv[2:])
    elif cmd == "expand":
        cmd_expand()
    elif cmd == "prune":
        cmd_prune()
    elif cmd == "read":
        cmd_read()
    else:
        print(f"Unknown command: {cmd}")