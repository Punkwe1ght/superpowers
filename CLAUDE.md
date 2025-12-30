# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Superpowers is a skill-based instruction system for AI coding agents. It's not a traditional codebase - it's a **workflow system** that provides structured skills for design, implementation, testing, and debugging. Skills are markdown files with YAML frontmatter that agents invoke to follow disciplined development processes.

**Key insight:** This is a Claude Code plugin, not a library. There's no compilation, no package manager dependencies to install - just markdown skills and JavaScript for skill discovery.

## Architecture

```
superpowers/
├── .claude-plugin/       # Plugin metadata (plugin.json, marketplace.json)
├── skills/               # 14 core workflow skills (each has SKILL.md)
├── commands/             # Slash commands (brainstorm, write-plan, execute-plan)
├── agents/               # Subagent definitions (code-reviewer.md)
├── lib/                  # Skill discovery engine (ES6 JavaScript)
│   └── skills-core.js    # Frontmatter extraction, skill resolution, shadowing
├── hooks/                # Plugin lifecycle hooks
│   ├── hooks.json        # Hook configuration
│   └── session-start.sh  # Bootstrap - injects using-superpowers on startup
└── tests/                # Test suites for skills
```

### Execution Flow

1. **Session Start** → `hooks/session-start.sh` injects `using-superpowers` skill
2. **Skill Discovery** → `lib/skills-core.js` finds skills by parsing YAML frontmatter
3. **Skill Invocation** → Agent uses `Skill` tool → loads `SKILL.md` content
4. **Skill Shadowing** → Personal skills (`~/.claude/skills/`) override superpowers skills

### Skill Format

Every skill lives in `skills/<name>/SKILL.md`:
```yaml
---
name: skill-name
description: Use when [trigger] - [what it does]
---

# Skill Title
[Process content follows...]
```

**Critical:** Descriptions should be trigger-only (when to use). Put process details in the body, not the description.

## Development Commands

### Running Tests

```bash
# Run all fast tests (recommended during development)
cd tests/claude-code && ./run-skill-tests.sh

# Run with verbose output
./run-skill-tests.sh --verbose

# Run specific test
./run-skill-tests.sh --test test-subagent-driven-development.sh

# Run integration tests (slow, 10-30 minutes)
./run-skill-tests.sh --integration

# Run integration test directly
./test-subagent-driven-development-integration.sh
```

### Token Usage Analysis

```bash
# Analyze token usage from any session
python3 tests/claude-code/analyze-token-usage.py ~/.claude/projects/<project>/<session>.jsonl
```

### Local Plugin Development

Enable local dev plugin in `~/.claude/settings.json`:
```json
{
  "enabledPlugins": {
    "superpowers@superpowers-dev": true
  }
}
```

Then run tests **from the superpowers directory** (skills only load from plugin directory).

## Key Files

| File | Purpose |
|------|---------|
| `skills/using-superpowers/SKILL.md` | Bootstrap skill - teaches agent to invoke skills first |
| `skills/test-driven-development/SKILL.md` | RED-GREEN-REFACTOR enforcement |
| `skills/subagent-driven-development/SKILL.md` | Two-stage review workflow |
| `skills/writing-skills/SKILL.md` | How to author new skills |
| `lib/skills-core.js` | Skill discovery and resolution logic |
| `hooks/session-start.sh` | Plugin initialization |
| `.claude-plugin/plugin.json` | Version and metadata |

## Writing Skills

Follow `skills/writing-skills/SKILL.md` for the complete guide. Key points:

- Keep skills under 500 lines
- Use DOT/GraphViz for workflows, tables for principles
- Include worked examples with exact file paths
- Add verification checklists
- Test with the test infrastructure

## Skill Philosophy

- **Rigid skills** (TDD, debugging): Follow exactly - don't adapt away discipline
- **Flexible skills** (brainstorming): Adapt principles to context

The system enforces: test before code, process over guessing, evidence over claims.

## Git Workflow

**Important:** This is a fork of obra/superpowers.

- **NEVER** create pull requests to `obra:main`
- **ONLY** push to `punkwe1ght:main` (origin)
- Branch from main for features: `git checkout -b feature-name`
- Push to your fork: `git push origin feature-name`

## Platform Support

- **Claude Code** (primary): Plugin marketplace integration
- **Codex**: `.codex/` directory, see `docs/README.codex.md`
- **OpenCode**: `.opencode/` directory, see `docs/README.opencode.md`
