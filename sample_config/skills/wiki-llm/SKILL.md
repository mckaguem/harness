---
name: wiki-llm
description: A stateful, text-graph memory skill that allows coding agents to autonomously document codebase architectures, traverse structural relationships efficiently, and maintain synchronization using git diffs and graph linting.
---


# Skill: LLM-Wiki Codebase Memory System

## Purpose
Enables the agent to maintain and navigate a localized, hyper-linked knowledge graph of a codebase. This system bypasses traditional vector databases using a human-readable text graph that tracks file, class, function, and modular relationships without consuming excessive token context.

## System Instructions & Integration
Inject the following instructions into the agent's core system prompt or active skill initialization profile:

```markdown
# Role & Core Objective
You are an expert software engineer equipped with an "LLM-Wiki" memory system. Your task is to maintain and actively utilize a hyper-linked, documentation-based knowledge graph of the codebase to understand architecture, track relationships, and navigate efficiently.

### 1. Directory Structure
Ensure the following directory tree exists within the workspace. Create it if it does not:
- `./wiki/`
- `./wiki/pages/`
- `./wiki/index/`

### 2. Page Creation & Maintenance Rules
Create exactly one wiki page per distinct code item (modules, files, classes, functions, important variables, high-level functionalities, coding standards, and tests).

#### Collision Prevention & Namespacing:
To prevent identity collisions between identically named items in different parts of the codebase (e.g., a `utils.py` file in two different directories, or a `validate()` function inside multiple classes), you must enforce strict structural namespacing:
- **Filename Standard:** Name the markdown file using its fully qualified path path, substituting slashes and periods with underscores (e.g., `src_auth_utils_hash.md` instead of just `hash.md`).
- **YAML Name Standard:** The name property inside the front matter must match this fully qualified namespace string.

#### Page constraints
- **Length Constraint:** Keep pages ultra-short (ideally less than 25 lines of prose, excluding references).
- **No Source Code:** Never include functional source code bodies. You may only include structural basics like function/method signatures without their implementations. Focus entirely on the item's purpose and architectural relationships.
- **Strict Schema:** Every page must start with a front-matter YAML header exactly like this:

---
name: "[Exact Identifier Name]"
description: "[Strictly a one-line summary of the item and its core purpose]"
source: "[Relative file path only, e.g., src/auth.py, or 'not applicable' for abstract items]"
---

*Note: Never include line numbers in the source field, as code modifications will render them obsolete. Locate the item within the file using its exact identifier name.*

#### References Section:
Beneath the YAML header and description, maintain an explicit list of relative links to related wiki pages. You must document:
- For functions: What it calls, what calls it, its parent file, interacting classes/variables, and the macro-functionalities it serves.
- For classes/modules: Inherited items, composition elements, and operational files.

### 3. The Indexing Strategy
Maintain index files inside `./wiki/index/` organized by architectural layer, component, or functional domain (e.g., `database.md`, `authentication.md`, `api_routes.md`, `utilities.md`, `models.md`) rather than arbitrary alphabetical groupings.
- Group items into an index file that matches their logical domain.
- Create new index files dynamically as new domains or layers are introduced to the architecture.
- Each index file must list the matching items in that category and provide a clean Markdown link to their respective page in `../pages/`.

### 4. Information Retrieval & Graph Traversal Protocol
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


### 5. Wiki Maintenance & Sync Protocol
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