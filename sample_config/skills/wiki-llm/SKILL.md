---
name: wiki-llm
description: A stateful, text-graph memory skill that allows coding agents to autonomously document codebase architectures, traverse structural relationships efficiently, and maintain synchronization using git diffs and graph linting.
compatibility: Python 3.x, Obsidian
metadata:
  version: 2.0.0
  automation_script: wiki_init.py
---

# Skill: LLM-Wiki Codebase Memory System

## Purpose
Enables the agent to maintain and navigate a localized, hyper-linked knowledge graph of a codebase. This system replaces traditional vector databases with a human-readable text graph that tracks module, file, class, function, and constant relationships without consuming excessive token context.

## Core Architecture & Directory Rules

### 1. Wiki Generation Automation (`wiki_init.py`)
* The text-graph wiki structure is automatically built and refreshed using the codebase exploration script named `wiki_init.py`.
* `wiki_init.py` utilizes Python's Abstract Syntax Tree (`ast`) module to perform static analysis across the codebase.
* The script maps out scopes, processes direct references, automatically constructs parent-child chains, and populates the wiki directory.
* When running updates or synchronization lifecycles, `wiki_init.py` is configured to preserve existing frontmatter descriptions that have been manually added or updated.

### 2. File Naming Convention
* Every page generated in the wiki is written as an Obsidian-compatible Markdown file.
* The filename for each page must be the item's Fully Qualified Name (FQN), such as `mymodule.myfile.MyClass.md` or `mymodule.myfile.md`.
* Pages must exist for all structural layers, including top-level directories (`modules`) and individual Python source files (`files`).
* The files are saved inside a nested directory layout under `./wiki` that reflects the original layout of the source codebase, while the leaf filename itself retains the complete FQN.

## Note Layout and Frontmatter Specification
Each individual Markdown page represents exactly one codebase item and must adhere to a strict 25-line maximum limit (excluding link listings). Source code bodies must never be pasted onto a page; only structural definitions like abstract function or method signatures are permitted.

### Required YAML Frontmatter
Every note must contain the following structural properties at the very top of the file:
* `name`: The name of the codebase element written in Python FQN format (e.g., `mymodule.myfile.MyClass.myFunction`).
* `description`: A one-line summary explaining the item's purpose, which is left empty by default upon initialization and preserved during subsequent synchronization runs.
* `type`: A category string restricted to one of the following: `module`, `file`, `class`, `function`, or `constant`.
* `reference`: The path to the element relative to the project root directory. For `module` and `file` types, this is their own relative path. For `class`, `function`, and `constant` types, this is the relative path to the Python file where they are defined.

## Relationship and Link Protocols
To keep the structural map clean and readable for the agent, links must adhere strictly to a direct-containment schema.

### 1. Direct References Only
* Pages must only link to items they reference or interact with directly.
* A function page includes links to other functions it explicitly invokes, or classes/constants it directly uses.
* A class page links directly to the methods it contains or the base classes it derives from.
* **Strict Avoidance of Indirect Linking:** A class page must never link directly to an external function just because one of its methods calls that function. The class links to its method, and the method page links to the external function.

### 2. Parent Links
* Every page must feature exactly one explicit link pointing to its immediate structural parent container.
* A method page links to its containing class page.
* A class or function defined at the file level links to its containing file page.
* A file page links to its parent module directory page, and a sub-module links to its parent module page.

### 3. Back Links
* Every page must contain a dedicated `## Back Links` section.
* Whenever a page links to another item, the target item's page must include a reverse link tracking that relationship.
* Back-links must be labeled clearly to describe the nature of the inverse relationship, using notations such as `(contained by)` or `(used/called/imported by)`.

##  Information Retrieval & Graph Traversal Protocol
When tasked with resolving a query, tracking down an architectural bug, or understanding a system layout, you must use the `wiki_nav.py` tool inside your tools directory to crawl the wiki graph. 

Do not guess links manually. Run this loop:

1. **Initialize the Search:** 
   Identify the core domain keywords of your task and run:
   `python tools/wiki_nav.py init [keyword1] [keyword2]`
   This returns the path and YAML header of the first candidate page.

2. **The Traversal Loop:**
   Look closely at the `TARGET_PAGE` path and the `description` field inside the returned YAML header.
   
   - **If the item seems RELEVANT to your query:**
     1. Read the full page by running: `python tools/wiki_nav.py read`
     2. Process its text context.
     3. Tell the state machine to harvest its links and advance by running: `python tools/wiki_nav.py expand`
     
   - **If the item is IRRELEVANT to your query:**
     1. Immediately prune this branch of the graph without reading the full file.
     2. Advance to the next unvisited branch by running: `python tools/wiki_nav.py prune`

3. **Termination:**
   Repeat Step 2 until the tool outputs `SEARCH_COMPLETE`. Compile your answer based only on the full pages you read during the loop.


## Wiki Maintenance & Sync Protocol
Whenever code modifications, file additions, or deletions occur in the codebase workspace, you must execute a strict, incremental synchronization loop using the `tools/wiki_sync.py` tool. Do not try to scan the entire workspace manually. 

Execute this loop exactly as follows:

#### Step 1: Initialize the Sync Queue
Run the following initialization command:
`python tools/wiki_sync.py init`

- If the tool returns `NO_CHANGES_DETECTED`, halt; no further action is required.
- If changes are present, the tool will return the first `CURRENT_SYNC_TARGET` along with its specific text-based git diff context.

#### Step 2: Process the Target File Incremental Steps
For the given `CURRENT_SYNC_TARGET`, systematically perform these micro-evaluation tasks:

1. **Identify Affected Elements:** Review the provided Git Diff context to determine which specific structural elements (modules, classes, functions, global variables, or micro-functionalities) were added, altered, or deleted inside that file.
2. **Handle Updates & Creations:**
   - **Existing Items:** If a wiki page already exists for an altered item in `./wiki/pages/`, read the page and update its details based on the new file logic.
   - **New Items:** If a new function, class, or functionality was introduced, create a brand-new wiki page adhering to the core page rules (YAML header, no functional code bodies, under 25 lines)[cite: 1].
3. **Enforce Cross-Reference Symmetry:**
   - If you add or modify a reference link on Page A pointing to Page B, you must open Page B and insert a reciprocal back-link pointing back to Page A.
4. **Clean Up Deletions:**
   - If an entire code item was completely removed from the file, locate its corresponding page in `./wiki/pages/` and delete the file.
   - **Crucial:** Search the remaining wiki files for any incoming markdown links pointing to the deleted page and erase those dead links to maintain graph integrity.
5. **Update Domain Indices:** If any items were added or deleted, open the corresponding domain index file inside `./wiki/index/` and add or remove its link accordingly[cite: 1].

#### Step 3: Advance the Queue
Once all actions related to the elements of the current file are completely executed, notify the state machine and request the next target file by running:
`python tools/wiki_sync.py resolve`

#### Step 4: Validate Graph Integrity
Before declaring a development task complete, you must run the graph compiler to check for formatting mistakes, structural orphans, or dead Markdown references:
`python tools/wiki_lint.py`

- If the tool outputs `[ERROR]` lines, read the output carefully, trace the offending files, repair the formatting or missing links, and run the linter again.
- Do not conclude your turn until the linter outputs: `Success: Wiki graph is completely healthy and synchronized.`

Repeat **Step 2** and **Step 3** continuously until the script outputs `SYNC_COMPLETE`.