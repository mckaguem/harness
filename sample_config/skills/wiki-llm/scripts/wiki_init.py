import os
import ast
import re
from pathlib import Path

class CodeAnalyzer(ast.NodeVisitor):
    """Visits AST nodes to extract structural items and their internal references."""
    def __init__(self, file_path, file_fqn):
        self.file_path = file_path
        self.file_fqn = file_fqn
        self.items = {} # Maps FQN -> item details
        self.scope_stack = [(file_fqn, file_fqn)] # (parent, current)
        self.current_parent = file_fqn
        self.current_fqn = file_fqn
        
        # Initialize the file itself as an item
        self.items[file_fqn] = {
            "name": file_fqn,
            "type": "file",
            "reference": file_path,
            "parent": None, # Will be set by the generator to its parent module
            "children": set(),
            "uses_names": set()
        }

    def push_scope(self, name, item_type):
        parent_fqn = self.current_fqn
        fqn = f"{parent_fqn}.{name}"
        self.scope_stack.append((parent_fqn, fqn))
        self.current_parent = parent_fqn
        self.current_fqn = fqn
        
        self.items[fqn] = {
            "name": fqn,
            "type": item_type,
            "reference": self.file_path,
            "parent": parent_fqn,
            "children": set(),
            "uses_names": set()
        }
        self.items[parent_fqn]["children"].add(fqn)
        return fqn

    def pop_scope(self):
        self.scope_stack.pop()
        self.current_parent, self.current_fqn = self.scope_stack[-1]

    def visit_ClassDef(self, node):
        fqn = self.push_scope(node.name, "class")
        # Track direct base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.items[fqn]["uses_names"].add(base.id)
            elif isinstance(base, ast.Attribute):
                self.items[fqn]["uses_names"].add(base.attr)
                
        self.generic_visit(node)
        self.pop_scope()

    def visit_FunctionDef(self, node):
        self.push_scope(node.name, "function")
        self.generic_visit(node)
        self.pop_scope()

    def visit_AsyncFunctionDef(self, node):
        self.push_scope(node.name, "function")
        self.generic_visit(node)
        self.pop_scope()

    def visit_Assign(self, node):
        # Heuristic for top-level file or class constants
        if self.items[self.current_fqn]["type"] in ["file", "class"]:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    fqn = self.push_scope(target.id, "constant")
                    self.pop_scope()
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.items[self.current_fqn]["uses_names"].add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            self.items[self.current_fqn]["uses_names"].add(node.attr)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.items[self.current_fqn]["uses_names"].add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.items[self.current_fqn]["uses_names"].add(node.func.attr)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.items[self.file_fqn]["uses_names"].add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.items[self.file_fqn]["uses_names"].add(node.module)
            for alias in node.names:
                self.items[self.file_fqn]["uses_names"].add(f"{node.module}.{alias.name}")
        self.generic_visit(node)


class WikiGenerator:
    def __init__(self, root_dir="./harness_core", wiki_dir="./wiki2"):
        self.root_dir = Path(root_dir).resolve()
        self.wiki_dir = Path(wiki_dir).resolve()
        self.all_items = {}
        self.links = {}      
        self.backlinks = {}  
        self.name_to_fqn = {} 

    def get_file_fqn(self, file_path):
        rel_path = file_path.relative_to(self.root_dir)
        return ".".join(rel_path.with_suffix('').parts)

    def add_modules_for_fqn(self, file_fqn, file_path):
        """Discovers and builds structural tracking for parent modules/directories."""
        parts = file_fqn.split('.')
        for i in range(1, len(parts)):
            mod_parts = parts[:i]
            mod_fqn = ".".join(mod_parts)
            
            if mod_fqn not in self.all_items:
                rel_path = Path(*file_path.relative_to(self.root_dir).parts[:i])
                parent_fqn = ".".join(mod_parts[:-1]) if len(mod_parts) > 1 else None
                
                self.all_items[mod_fqn] = {
                    "name": mod_fqn,
                    "type": "module",
                    "reference": str(rel_path),
                    "parent": parent_fqn,
                    "children": set(),
                    "uses_names": set()
                }
                if parent_fqn:
                    self.all_items[parent_fqn]["children"].add(mod_fqn)

    def parse_project(self):
        """Pass 1: Discover all items (modules, files, and internals)."""
        for path in self.root_dir.rglob("*.py"):
            if any(part.startswith('.') or part in ('venv', 'env', 'wiki', 'tests') for part in path.parts):
                continue
                
            file_fqn = self.get_file_fqn(path)
            rel_path_str = str(path.relative_to(self.root_dir))
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(path))
                    
                analyzer = CodeAnalyzer(rel_path_str, file_fqn)
                analyzer.visit(tree)
                
                # Build directory/module trees up to this file
                self.add_modules_for_fqn(file_fqn, path)
                
                # Link the file to its parent module if applicable
                parts = file_fqn.split('.')
                if len(parts) > 1:
                    parent_mod_fqn = ".".join(parts[:-1])
                    analyzer.items[file_fqn]["parent"] = parent_mod_fqn
                    if parent_mod_fqn in self.all_items:
                        self.all_items[parent_mod_fqn]["children"].add(file_fqn)
                
                # Merge into global tracking database
                for fqn, data in analyzer.items.items():
                    self.all_items[fqn] = data
                    short_name = fqn.split('.')[-1]
                    self.name_to_fqn.setdefault(short_name, []).append(fqn)
                    
            except SyntaxError:
                print(f"Syntax error skipping file: {path}")

    def resolve_references(self):
        """Pass 2: Graph structural maps and usages."""
        for fqn in self.all_items:
            self.links[fqn] = set()
            self.backlinks[fqn] = set()

        for fqn, data in self.all_items.items():
            # 1. Nesting parent-child constraints
            for child_fqn in data.get("children", []):
                self.links[fqn].add(child_fqn)
                self.backlinks[child_fqn].add(fqn)
                
            # 2. Resolving calls/imports/usages
            for used_name in data.get("uses_names", []):
                # Exact match resolution (e.g. standard module/file imports)
                if used_name in self.all_items:
                    if used_name != fqn:
                        self.links[fqn].add(used_name)
                        self.backlinks[used_name].add(fqn)
                # Short name matching resolution
                elif used_name in self.name_to_fqn:
                    for target_fqn in self.name_to_fqn[used_name]:
                        if target_fqn != fqn:
                            self.links[fqn].add(target_fqn)
                            self.backlinks[target_fqn].add(fqn)

    def generate_markdown(self):
        """Pass 3: Generate the Obsidian Markdown wiki assets."""
        for fqn, data in self.all_items.items():
            parts = fqn.split('.')
            
            # The directory structure mirrors the source directory structure up to the leaf's parent container
            dir_parts = parts[:-1]
            target_dir = self.wiki_dir / Path(*dir_parts)
            
            # The leaf filename is explicitly set to the FQN
            target_path = target_dir / f"{fqn}.md"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract and maintain user/LLM descriptions on sync updates
            existing_desc = '""'
            if target_path.exists():
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    desc_match = re.search(r'^description:\s*(.*)$', content, re.MULTILINE)
                    if desc_match:
                        existing_desc = desc_match.group(1).strip()

            # Construct Obsidian standard frontmatter
            md = [
                "---",
                f"name: {data['name']}",
                f"description: {existing_desc}",
                f"type: {data['type']}",
                f"reference: {data['reference']}",
                "---",
                f"\n# {data['name']}\n"
            ]
            
            if data["parent"]:
                md.append(f"**Parent:** [[{data['parent']}]]\n")
            else:
                md.append(f"**Parent:** None (Top-level {data['type'].capitalize()})\n")

            md.append("## References")
            if self.links[fqn]:
                for link in sorted(self.links[fqn]):
                    link_type = "contains" if link in data.get("children", []) else "uses/calls/imports"
                    md.append(f"- [[{link}]] ({link_type})")
            else:
                md.append("*No internal references found.*")
            
            md.append("\n## Back Links")
            if self.backlinks[fqn]:
                for blink in sorted(self.backlinks[fqn]):
                    blink_type = "contained by" if fqn in self.all_items[blink].get("children", []) else "used/called/imported by"
                    md.append(f"- [[{blink}]] ({blink_type})")
            else:
                md.append("*No back links found.*")

            with open(target_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(md))
                
        print(f"Wiki successfully generated at: {self.wiki_dir}")

if __name__ == "__main__":
    generator = WikiGenerator()
    print("Parsing project structure...")
    generator.parse_project()
    print("Resolving relationship maps...")
    generator.resolve_references()
    print("Generating FQN-named Wiki assets...")
    generator.generate_markdown()