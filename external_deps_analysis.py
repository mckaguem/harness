#!/usr/bin/env python3
"""Categorize external dependencies."""

import json
from collections import defaultdict

# Load the dependency report
with open("dependency_report.json", "r") as f:
    report = json.load(f)

# Get external dependencies
external_deps = set()
for dep in report["external_dependencies"]:
    # Extract the actual module name from "[EXTERNAL] module_name"
    if dep.startswith("[EXTERNAL]"):
        module_name = dep[11:].strip().replace('"', '').replace(',', '')
        external_deps.add(module_name)

# Categorize dependencies
categories = {
    "python_standard_library": {
        "os", "sys", "json", "pathlib", "re", "typing", "dataclasses", 
        "datetime", "time", "subprocess", "urllib.request", "urllib.error",
        "importlib.util", "fnmatch", "collections", "ast", "traceback",
        "tempfile", "contextvars", "__future__"
    },
    "testing_framework": {"pytest", "unittest.mock"},
    "rich_terminal_ui": {"rich.console", "rich.markdown", "rich.panel", "rich.syntax"},
    "prompt_toolkit": {"prompt_toolkit", "prompt_toolkit.history"},
    "openai_api": {"openai"},
    "web_search": {"ddgs"},
    "yaml_parsing": {"yaml"},
    "ollama": {"ollama"},
    "internal_packages": {"agent", "commands", "terminal_io", "tools"}  # These are project modules mis-categorized
}

# Categorize each dependency
categorized = defaultdict(list)
uncategorized = []

for dep in sorted(external_deps):
    categorized_found = False
    for category, modules in categories.items():
        if dep in modules:
            categorized[category].append(dep)
            categorized_found = True
            break
    
    if not categorized_found:
        uncategorized.append(dep)

# Print analysis
print("EXTERNAL DEPENDENCY ANALYSIS")
print("="*60)

print("\nBy Category:")
for category, deps in sorted(categorized.items()):
    print(f"\n{category.replace('_', ' ').title()}:")
    for dep in sorted(deps):
        print(f"  - {dep}")

if uncategorized:
    print(f"\nUncategorized Dependencies ({len(uncategorized)}):")
    for dep in sorted(uncategorized):
        print(f"  - {dep}")

print(f"\n\nTotal External Dependencies Found: {len(external_deps)}")

# Show which are in requirements.txt
print("\nDependencies in requirements.txt:")
requirements = {"prompt_toolkit", "pyyaml", "rich", "openai", "ddgs"}
for dep in external_deps:
    # Map module names to package names
    if dep == "yaml":
        if "pyyaml" in requirements:
            print(f"  ✓ {dep} -> pyyaml")
    elif dep.startswith("rich."):
        if "rich" in requirements:
            print(f"  ✓ {dep} -> rich")
    elif dep.startswith("prompt_toolkit"):
        if "prompt_toolkit" in requirements:
            print(f"  ✓ {dep} -> prompt_toolkit")
    elif dep in requirements:
        print(f"  ✓ {dep}")
    elif ".".join(dep.split(".")[:1]) in requirements:
        base = dep.split(".")[0]
        if base in requirements:
            print(f"  ✓ {dep} -> {base}")
    elif dep == "ollama":
        print(f"  ✗ {dep} (not in requirements.txt - optional?)")

print(f"\n\nMissing from requirements.txt (but might be standard library):")
missing = set()
for dep in external_deps:
    if (dep not in ["yaml", "ollama"] and 
        not dep.startswith("rich.") and 
        not dep.startswith("prompt_toolkit") and
        dep not in requirements and
        dep not in categories["python_standard_library"] and
        dep not in categories["internal_packages"]):
        missing.add(dep)

for dep in sorted(missing):
    print(f"  - {dep}")