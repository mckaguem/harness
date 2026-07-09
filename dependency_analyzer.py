#!/usr/bin/env python3
"""Analyze import dependencies in the Harness project."""

import ast
import os
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple
import json

class ImportAnalyzer:
    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.modules = {}  # module_path -> module_name
        self.imports = defaultdict(set)  # module -> imported modules
        self.reverse_imports = defaultdict(set)  # imported module -> importers
        
    def discover_modules(self):
        """Find all Python modules in the project."""
        for path in self.root.rglob("*.py"):
            if "__pycache__" in str(path) or ".venv" in str(path):
                continue
                
            # Convert path to module name
            rel_path = path.relative_to(self.root)
            module_parts = []
            
            # Handle special cases for files in root
            if rel_path.parent == Path("."):
                module_name = rel_path.stem
            else:
                # For subdirectories, use proper module notation
                module_parts = list(rel_path.parent.parts) + [rel_path.stem]
                module_name = ".".join(module_parts)
                
            self.modules[str(path)] = module_name
            
    def extract_imports(self, filepath: str) -> Set[str]:
        """Extract all imports from a Python file."""
        imports = set()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return imports
            
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return imports
            
        # Store module context for relative imports
        module_name = self.modules.get(filepath, "")
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                # Handle from ... import *
                if node.names:
                    for alias in node.names:
                        # For "from X import Y", track X
                        if node.module:
                            imports.add(node.module)
                        
        return imports
    
    def resolve_import(self, imp: str, importer_path: str) -> str:
        """Try to resolve an import to a module in our project."""
        # First check if it's a standard project module
        for module_path, module_name in self.modules.items():
            if module_name == imp:
                return module_name
                
        # Check for relative imports
        if imp.startswith("."):
            # This is a relative import - we need importer's location
            importer_dir = Path(importer_path).parent
            rel_parts = imp.split(".")
            
            # Count leading dots
            dot_count = 0
            for char in imp:
                if char == ".":
                    dot_count += 1
                else:
                    break
            
            # Remove leading dots
            if dot_count > 0:
                base_module = imp[dot_count:] if dot_count < len(imp) else ""
                
                # Go up dot_count-1 directories from importer
                target_dir = importer_dir
                for _ in range(dot_count - 1):
                    target_dir = target_dir.parent
                
                # Look for module in target_dir
                if base_module:
                    # Convert to possible file paths
                    possible_paths = [
                        target_dir / f"{base_module}.py",
                        target_dir / base_module / "__init__.py"
                    ]
                else:
                    # Import from parent directory
                    possible_paths = [target_dir / "__init__.py"]
                
                for possible_path in possible_paths:
                    if possible_path.exists():
                        # Convert to module name
                        rel_to_root = possible_path.relative_to(self.root)
                        if possible_path.name == "__init__.py":
                            module_parts = list(rel_to_root.parent.parts)
                        else:
                            module_parts = list(rel_to_root.parent.parts) + [rel_to_root.stem]
                        return ".".join(module_parts)
        
        # Check if it's likely a local import without dots
        # (e.g., "from tools import ..." when importer is in root)
        importer_dir = Path(importer_path).parent
        possible_path = importer_dir / f"{imp}.py"
        if possible_path.exists():
            rel_to_root = possible_path.relative_to(self.root)
            module_parts = list(rel_to_root.parent.parts) + [rel_to_root.stem]
            return ".".join(module_parts)
            
        # Could be external or we couldn't resolve it
        return f"[EXTERNAL] {imp}"
    
    def analyze(self):
        """Run full analysis."""
        print("Discovering modules...")
        self.discover_modules()
        
        print(f"Found {len(self.modules)} Python modules")
        
        print("Analyzing imports...")
        for filepath, module_name in self.modules.items():
            imports = self.extract_imports(filepath)
            
            for imp in imports:
                resolved = self.resolve_import(imp, filepath)
                if resolved.startswith("[EXTERNAL]"):
                    # Track as external
                    self.imports[module_name].add(resolved)
                else:
                    # Internal import
                    self.imports[module_name].add(resolved)
                    self.reverse_imports[resolved].add(module_name)
                    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies using DFS."""
        visited = set()
        stack = set()
        cycles = []
        
        def dfs(node, path):
            visited.add(node)
            stack.add(node)
            current_path = path + [node]
            
            for neighbor in self.imports[node]:
                # Skip external dependencies
                if neighbor.startswith("[EXTERNAL]"):
                    continue
                    
                if neighbor not in self.imports:
                    # Neighbor might be external or not discovered
                    continue
                    
                if neighbor in stack:
                    # Found a cycle
                    start_idx = current_path.index(neighbor)
                    cycle = current_path[start_idx:]
                    if cycle not in cycles:
                        cycles.append(cycle.copy())
                elif neighbor not in visited:
                    dfs(neighbor, current_path)
                    
            stack.remove(node)
            
        for module in self.imports:
            if module not in visited:
                dfs(module, [])
                
        return cycles
    
    def categorize_modules(self) -> Dict[str, List[str]]:
        """Categorize modules by their directory/purpose."""
        categories = defaultdict(list)
        
        for module_path, module_name in self.modules.items():
            rel_path = Path(module_path).relative_to(self.root)
            
            if str(rel_path).startswith("agent/"):
                categories["agent"].append(module_name)
            elif str(rel_path).startswith("tools/"):
                categories["tools"].append(module_name)
            elif str(rel_path).startswith("session/"):
                categories["session"].append(module_name)
            elif str(rel_path).startswith("terminal_io/"):
                categories["terminal_io"].append(module_name)
            elif str(rel_path).startswith("commands/"):
                categories["commands"].append(module_name)
            elif str(rel_path).startswith("tests/"):
                categories["tests"].append(module_name)
            elif str(rel_path) == "harness.py":
                categories["main"].append("harness")
            elif str(rel_path) == "config.py":
                categories["config"].append("config")
            elif "model/" in str(rel_path):
                categories["model"].append(module_name)
            elif "skills/" in str(rel_path):
                categories["skills"].append(module_name)
            else:
                categories["other"].append(module_name)
                
        return categories
    
    def get_external_dependencies(self) -> Set[str]:
        """Get all external dependencies."""
        externals = set()
        for imports in self.imports.values():
            for imp in imports:
                if imp.startswith("[EXTERNAL]"):
                    externals.add(imp)
        return externals
    
    def generate_report(self):
        """Generate comprehensive dependency report."""
        categories = self.categorize_modules()
        cycles = self.find_circular_dependencies()
        externals = self.get_external_dependencies()
        
        report = {
            "module_categories": {k: sorted(v) for k, v in categories.items()},
            "dependency_graph": {k: sorted(list(v)) for k, v in self.imports.items()},
            "reverse_dependencies": {k: sorted(list(v)) for k, v in self.reverse_imports.items()},
            "circular_dependencies": [list(c) for c in cycles],
            "external_dependencies": sorted(list(externals)),
            "summary": {
                "total_modules": len(self.modules),
                "total_internal_dependencies": sum(len(v) for v in self.imports.values()),
                "circular_dependency_count": len(cycles),
                "external_dependency_count": len(externals)
            }
        }
        
        return report


def main():
    analyzer = ImportAnalyzer("/workspaces/harness")
    analyzer.analyze()
    
    report = analyzer.generate_report()
    
    print("\n" + "="*80)
    print("DEPENDENCY ANALYSIS REPORT")
    print("="*80)
    
    print(f"\nSummary:")
    print(f"  Total modules: {report['summary']['total_modules']}")
    print(f"  Internal dependencies: {report['summary']['total_internal_dependencies']}")
    print(f"  Circular dependencies found: {report['summary']['circular_dependency_count']}")
    print(f"  External dependencies: {report['summary']['external_dependency_count']}")
    
    print("\nModule Categories:")
    for category, modules in report['module_categories'].items():
        print(f"  {category}: {len(modules)} modules")
        if len(modules) <= 10:
            for mod in modules[:10]:
                print(f"    - {mod}")
        else:
            print(f"    (showing first 10 of {len(modules)})")
            for mod in modules[:10]:
                print(f"      - {mod}")
    
    print("\nCircular Dependencies:")
    if report['circular_dependencies']:
        for i, cycle in enumerate(report['circular_dependencies'], 1):
            print(f"  Cycle {i}: {' → '.join(cycle)}")
    else:
        print("  No circular dependencies found!")
    
    print("\nExternal Dependencies:")
    for ext in report['external_dependencies'][:20]:  # Show first 20
        print(f"  {ext}")
    if len(report['external_dependencies']) > 20:
        print(f"  ... and {len(report['external_dependencies']) - 20} more")
    
    print("\nSample Dependency Graph (first 10 modules):")
    for i, (module, deps) in enumerate(list(report['dependency_graph'].items())[:10]):
        print(f"  {module}:")
        for dep in deps[:5]:
            print(f"    → {dep}")
        if len(deps) > 5:
            print(f"    ... and {len(deps) - 5} more")
    
    # Save full report
    with open("dependency_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nFull report saved to dependency_report.json")

if __name__ == "__main__":
    main()