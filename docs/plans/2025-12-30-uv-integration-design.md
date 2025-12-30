# uv Integration Design

**Date:** 2025-12-30
**Status:** Approved
**Scope:** Mandatory uv usage for all Python work, both internal and user-facing

## Overview

Integrate `uv` as the required Python development tool throughout superpowers. This replaces all pip/poetry references with uv commands and establishes uv as the standard for dependency management, virtual environments, tool running, and Python version management.

## Requirements

1. **Hard requirement** - No fallback to pip/poetry. Skills assume uv is installed.
2. **Full dev environment** - uv for dependencies, venvs, tool running (`uvx`), Python versions
3. **Both internal and user-facing** - Superpowers development AND skills guiding user projects
4. **Dual pattern support** - pyproject.toml (preferred for new projects), requirements.txt (legacy)

## Design

### 1. New Skill: `using-uv`

**Location:** `skills/using-uv/SKILL.md`

**Frontmatter:**
```yaml
---
name: using-uv
description: Use when working with Python projects - covers dependency management, virtual environments, tool running, and Python versions
---
```

**Content sections:**
1. **Why uv** - Brief rationale (speed, single tool, replaces pip/poetry/pyenv/pipx)
2. **New projects** - `uv init`, `uv add <dep>`, `uv sync`, `uv run <script>`
3. **Legacy projects** - `uv venv`, `uv pip install -r requirements.txt`
4. **Tool running** - `uvx ruff check .`, `uvx pytest` (no install needed)
5. **Python versions** - `uv python install 3.12`, `uv python pin 3.12`
6. **Quick reference table** - Common commands at a glance

### 2. Skill Updates

#### `using-git-worktrees`

**Current Python detection:**
```bash
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi
```

**New Python detection:**
```bash
# Python (uv required)
if [ -f pyproject.toml ]; then uv sync; fi
if [ -f requirements.txt ] && [ ! -f pyproject.toml ]; then uv pip install -r requirements.txt; fi
```

- pyproject.toml takes precedence if both exist
- Add note: "Python projects require uv. See `superpowers:using-uv` for setup."

#### `test-driven-development`

- Change `pytest` examples to `uv run pytest`

#### `writing-plans`

- Update task examples from `pytest` to `uv run pytest`

#### `finishing-a-development-branch`

- Add uv-specific Python test pattern

### 3. Documentation Updates

#### CLAUDE.md

Add "Development Requirements" section:
```markdown
## Development Requirements

- **Python:** `uv` is required for all Python work. No pip/poetry fallback.
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - See `superpowers:using-uv` skill for patterns
```

#### docs/testing.md

Change:
```bash
python3 tests/claude-code/analyze-token-usage.py ~/.claude/projects/...
```

To:
```bash
uv run tests/claude-code/analyze-token-usage.py ~/.claude/projects/...
```

#### tests/claude-code/analyze-token-usage.py

Add header comment:
```python
#!/usr/bin/env python3
# Run with: uv run analyze-token-usage.py <session.jsonl>
```

### 4. Files Unchanged

- `brainstorming` - no Python tooling references
- `subagent-driven-development` - no Python tooling references
- `requesting-code-review` - no Python tooling references
- `receiving-code-review` - no Python tooling references
- `dispatching-parallel-agents` - no Python tooling references
- `verification-before-completion` - no Python tooling references
- `systematic-debugging` - no Python tooling references
- Node.js, Rust, Go tooling in `using-git-worktrees` - unchanged

## Implementation Tasks

1. Create `skills/using-uv/SKILL.md`
2. Update `skills/using-git-worktrees/SKILL.md` - Python detection logic
3. Update `skills/test-driven-development/SKILL.md` - pytest examples
4. Update `skills/writing-plans/SKILL.md` - task examples
5. Update `skills/finishing-a-development-branch/SKILL.md` - test patterns
6. Update `CLAUDE.md` - add Development Requirements section
7. Update `docs/testing.md` - Python script invocation
8. Update `tests/claude-code/analyze-token-usage.py` - add header comment
