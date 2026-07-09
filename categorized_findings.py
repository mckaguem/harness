#!/usr/bin/env python3
"""Organize findings by module categories."""

import json
from collections import defaultdict

# Load the dependency report
with open("dependency_report.json", "r") as f:
    report = json.load(f)

print("DEPENDENCY ANALYSIS BY MODULE CATEGORIES")
print("="*80)

# Module categories from the report
categories = report["module_categories"]

# For each category, analyze dependencies
for category_name, modules in sorted(categories.items()):
    if not modules:
        continue
        
    print(f"\n{' ' + category_name.upper() + ' ':-^80}")
    print(f"Modules ({len(modules)}): {', '.join(sorted(modules)[:5])}{' ...' if len(modules) > 5 else ''}")
    
    # Collect imports for modules in this category
    internal_imports = defaultdict(set)
    external_imports = defaultdict(set)
    
    for module in modules:
        if module in report["dependency_graph"]:
            deps = report["dependency_graph"][module]
            for dep in deps:
                if dep.startswith("[EXTERNAL]"):
                    external_imports[module].add(dep[11:])
                else:
                    internal_imports[module].add(dep)
    
    print(f"\n  Dependencies Overview:")
    total_internal = sum(len(v) for v in internal_imports.values())
    total_external = sum(len(v) for v in external_imports.values())
    print(f"    - Total internal imports: {total_internal}")
    print(f"    - Total external imports: {total_external}")
    print(f"    - Avg. imports per module: {(total_internal + total_external) / len(modules):.1f}")
    
    # Show most common external dependencies
    if external_imports:
        all_externals = []
        for deps in external_imports.values():
            all_externals.extend(deps)
        
        from collections import Counter
        ext_counter = Counter(all_externals)
        print(f"\n  Most Common External Dependencies:")
        for ext, count in ext_counter.most_common(5):
            print(f"    - {ext}: {count} modules")
    
    # Show import/export relationships with other categories
    print(f"\n  Cross-Category Dependencies:")
    
    # Find which categories this category imports from
    imports_by_category = defaultdict(set)
    for module in modules:
        if module in report["dependency_graph"]:
            deps = report["dependency_graph"][module]
            for dep in deps:
                if not dep.startswith("[EXTERNAL]"):
                    # Find which category dep belongs to
                    for cat_name, cat_modules in categories.items():
                        if dep in cat_modules:
                            imports_by_category[cat_name].add(module)
                            break
    
    # Find which categories import from this category
    exports_by_category = defaultdict(set)
    for cat_name, cat_modules in categories.items():
        if cat_name == category_name:
            continue
        for module in cat_modules:
            if module in report["dependency_graph"]:
                deps = report["dependency_graph"][module]
                for dep in deps:
                    if not dep.startswith("[EXTERNAL]") and dep in modules:
                        exports_by_category[cat_name].add(module)
    
    if imports_by_category:
        print("    Imports from:")
        for cat_name, importers in sorted(imports_by_category.items()):
            print(f"      - {cat_name}: {len(importers)} modules import")
    
    if exports_by_category:
        print("    Exports to:")
        for cat_name, exporters in sorted(exports_by_category.items()):
            print(f"      - {cat_name}: {len(exporters)} modules import from this category")

# Now show the dependency graph between categories
print(f"\n\n{' CATEGORY DEPENDENCY GRAPH ':=^80}")

# Create category dependency matrix
category_matrix = defaultdict(lambda: defaultdict(int))
for module, deps in report["dependency_graph"].items():
    # Find module's category
    module_cat = None
    for cat_name, cat_modules in categories.items():
        if module in cat_modules:
            module_cat = cat_name
            break
    
    if not module_cat:
        continue
    
    # Track dependencies to other categories
    for dep in deps:
        if not dep.startswith("[EXTERNAL]"):
            # Find dep's category
            dep_cat = None
            for cat_name, cat_modules in categories.items():
                if dep in cat_modules:
                    dep_cat = cat_name
                    break
            
            if dep_cat and dep_cat != module_cat:
                category_matrix[module_cat][dep_cat] += 1

# Print matrix
all_categories = sorted(categories.keys())
print("\nCategory → Category dependencies (number of imports):")
print(" " * 15 + "".join([f"{cat[:8]:>8}" for cat in all_categories]))

for source in all_categories:
    print(f"{source[:14]:<14}", end="")
    for target in all_categories:
        count = category_matrix[source][target]
        if source == target:
            print("       -", end=" ")
        else:
            print(f"{count:>7}", end=" ")
    print()

# Show key dependencies
print(f"\n\n{' KEY DEPENDENCY PATHS ':=^80}")
for source in sorted(category_matrix.keys()):
    for target, count in sorted(category_matrix[source].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {source} → {target}: {count} imports")

print(f"\n\n{' CRITICAL MODULES ANALYSIS ':=^80}")
# Find modules with highest in-degree (most imported from)
all_rev_deps = report["reverse_dependencies"]
critical_modules = []
for module, importers in all_rev_deps.items():
    if len(importers) >= 5:  # At least 5 modules depend on this
        critical_modules.append((module, len(importers)))

critical_modules.sort(key=lambda x: x[1], reverse=True)

print("\nMost Critical Modules (most imported from):")
for module, count in critical_modules[:10]:
    # Find category
    module_cat = None
    for cat_name, cat_modules in categories.items():
        if module in cat_modules:
            module_cat = cat_name
            break
    
    print(f"  {module:<35} ({module_cat}): {count} modules depend on it")
    # Show a few of the dependents
    importers = list(all_rev_deps[module])[:3]
    if importers:
        print(f"    e.g.: {', '.join(importers)}")

print(f"\n\n{' SUMMARY ':=^80}")
print(f"Total Modules Analyzed: {report['summary']['total_modules']}")
print(f"Total Internal Dependencies: {report['summary']['total_internal_dependencies']}")
print(f"Circular Dependencies Found: {report['summary']['circular_dependency_count']}")
print(f"External Dependencies Found: {report['summary']['external_dependency_count']}")

# Architecture health metrics
print(f"\nArchitecture Health Metrics:")
modules_by_cat = {k: len(v) for k, v in categories.items()}
print(f"- Module distribution across {len(categories)} categories:")
for cat, count in sorted(modules_by_cat.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cat}: {count} modules ({count/report['summary']['total_modules']:.1%})")

# Calculate coupling between categories
total_cross_category = sum(sum(counts.values()) for counts in category_matrix.values())
total_possible_cross_category = sum(len(categories) * (len(categories) - 1) for cat in categories.values()) / 2
if total_possible_cross_category > 0:
    coupling_ratio = total_cross_category / total_possible_cross_category
    print(f"- Cross-category coupling: {total_cross_category} / {total_possible_cross_category:.0f} = {coupling_ratio:.3f}")