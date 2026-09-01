---
name: agent-skills-registry
description: Open Agent Skills standard and CLI package manager. Provides discovery, installation, validation, and versioning for modular AI agent skills.
---

# Agent Skills Registry & Specification

An open standard and ecosystem specification created by Vercel Labs for defining, publishing, and installing modular AI agent capabilities across multiple agent surfaces (Claude Code, Cursor, Codex, Gemini CLI).

## Skill Package Specification

Each skill conformant to the standard contains:

```
skill-directory/
├── SKILL.md            # Metadata, trigger conditions, execution instructions
├── package.json        # Optional dependencies, CLI entry points
├── scripts/            # Executable helper scripts (Node.js / Python / Bash)
└── references/         # In-depth documentation, API schemas, and examples
```

### Standard Frontmatter Schema
```yaml
---
name: my-skill-name
description: Clear, 1-2 sentence description of what the skill does and when it activates.
version: 1.0.0
author: Author Name
tags: [tag1, tag2]
tools: [tool_name1, tool_name2]
---
```

## CLI Operations

- `npx skills add <github-user/repo>`: Install a remote skill package into the local `.agent/skills/` directory.
- `npx skills list`: Display all installed skills, active versions, and health status.
- `npx skills check`: Validate YAML frontmatter, broken links, and schema conformity.
