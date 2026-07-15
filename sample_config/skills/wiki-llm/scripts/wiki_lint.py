import os
import re
import sys

PAGES_DIR = "./wiki/pages"
INDEX_DIR = "./wiki/index"

def extract_yaml_fields(content):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, "Missing or malformed YAML front-matter wrapper."
    
    lines = match.group(1).split('\n')
    fields = {}
    for line in lines:
        if ':' in line:
            k, v = line.split(':', 1)
            fields[k.strip()] = v.strip().strip('"').strip("'")
            
    required = ["name", "description", "source"]
    missing = [r for r in required if r not in fields]
    if missing:
        return None, f"Missing required YAML fields: {missing}"
        
    return fields, None

def extract_links(content):
    # Matches both absolute-style pages/file.md and relative ../pages/file.md formats
    return re.findall(r'\]\((?:\.\./pages/|pages/)?([a-zA-Z0-9_\-\.]+)\)', content)

def run_lint():
    errors = 0
    warnings = 0
    
    if not os.path.exists(PAGES_DIR) or not os.path.exists(INDEX_DIR):
        print("Error: Core wiki directories are missing. Run init first.")
        sys.exit(1)

    all_pages = set(os.listdir(PAGES_DIR))
    indexed_pages = set()
    
    # Adjacency matrices for graph validation
    forward_graph = {} # page -> [dependencies]
    backward_graph = {} # page -> [dependents]
    
    print("=== Phase 1: Linting Page Formats & Dangling Links ===")
    for page in all_pages:
        page_path = os.path.join(PAGES_DIR, page)
        forward_graph[page] = []
        if page not in backward_graph:
            backward_graph[page] = []
            
        with open(page_path, 'r') as f:
            content = f.read()
            
        # 1. Check YAML compliance
        fields, yaml_err = extract_yaml_fields(content)
        if yaml_err:
            print(f"[ERROR] {page}: {yaml_err}")
            errors += 1
            
        # 2. Check line length recommendations
        lines = content.splitlines()
        if len(lines) > 40: # 25 lines soft prose limit + references
            print(f"[WARN] {page}: Page is long ({len(lines)} lines). Keep it concise.")
            warnings += 1
            
        # 3. Track links and find dangling references
        links = extract_links(content)
        for link in links:
            if link not in all_pages:
                print(f"[ERROR] {page}: Contains dangling reference to non-existent page '{link}'")
                errors += 1
            else:
                forward_graph[page].append(link)
                if link not in backward_graph:
                    backward_graph[link] = []
                backward_graph[link].append(page)

    print("\n=== Phase 2: Linting Domain Indices ===")
    for index_file in os.listdir(INDEX_DIR):
        if not index_file.endswith('.md'):
            continue
        with open(os.path.join(INDEX_DIR, index_file), 'r') as f:
            content = f.read()
            
        links = extract_links(content)
        if not links:
            print(f"[WARN] Index file '{index_file}' contains no links to pages.")
            warnings += 1
        for link in links:
            if link not in all_pages:
                print(f"[ERROR] Index '{index_file}': Points to a non-existent page '{link}'")
                errors += 1
            else:
                indexed_pages.add(link)

    print("\n=== Phase 3: Structural Graph Integrity (Symmetry & Orphans) ===")
    # 1. Check for Orphan Pages (Not tracked in any domain index)
    orphans = all_pages - indexed_pages
    for orphan in orphans:
        print(f"[ERROR] Orphan Page: '{orphan}' exists but is not registered in any index file.")
        errors += 1

    # 2. Check for Missing Reciprocal Links (Symmetry Check)
    for source, targets in forward_graph.items():
        for target in targets:
            if source not in forward_graph.get(target, []):
                print(f"[ERROR] Asymmetric Relationship: '{source}' links to '{target}', but '{target}' does not provide a reciprocal back-link.")
                errors += 1

    print("\n==========================================")
    print(f"Linting Complete: {errors} Error(s), {warnings} Warning(s).")
    
    if errors > 0:
        sys.exit(1)
    else:
        print("Success: Wiki graph is completely healthy and synchronized.")
        sys.exit(0)

if __name__ == "__main__":
    run_lint()