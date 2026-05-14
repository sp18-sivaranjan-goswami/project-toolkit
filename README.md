# proj-toolkit

CLI scaffolding tool for full-stack monorepos pre-configured for Claude Code agentic development.

> **Requires** [Claude Code](https://claude.ai/code) to be installed and authenticated (`claude auth`).

## Installation

Not yet on PyPI — install directly from GitHub:

```bash
pip install git+https://github.com/sp18-sivaranjan-goswami/project-toolkit.git
```

## Usage

### New project (empty directory)

```bash
mkdir my-project && cd my-project
proj-toolkit
```

proj-toolkit will interactively ask for your stack choices and scaffold a full monorepo with `frontend/`, `backend/`, `claude/`, `CLAUDE.md`, Dockerfiles, and `.claude/commands/` skill files.

### Existing project (retrofit mode)

Run proj-toolkit inside any non-empty repository and it will automatically enter retrofit mode:

```bash
cd my-existing-repo
proj-toolkit
```

It will:
1. Scan your repository structure and config files
2. Use Claude (Sonnet by default) to detect your tech stack
3. Generate a `CLAUDE.md`, `claude/context.md`, `claude/AGENTS.md`, and `.claude/commands/` skill files tailored to your actual codebase
4. Show a preview and ask for confirmation before writing anything

**With linked documentation:**

```bash
proj-toolkit --docs ./architecture.pdf --docs ./onboarding.md
```

**With Opus for higher-quality output on complex repos:**

```bash
proj-toolkit --model claude-opus-4-7
```

### Options

```
Arguments:
  DIRECTORY   Target directory. Empty = new project, non-empty = retrofit mode.
              Defaults to current directory.

Options:
  --docs  -d  FILE   Documentation file (PDF or Markdown) to include in analysis.
                     Can be passed multiple times.
  --model -m  TEXT   Claude model for retrofit generation.
                     [default: claude-sonnet-4-6]
```

## What gets generated

| Path | Description |
|---|---|
| `CLAUDE.md` | Root-level instructions for Claude Code agents |
| `claude/context.md` | Architecture overview and module reference |
| `claude/AGENTS.md` | Multi-agent coordination rules and boundaries |
| `claude/tasks/` | Task lock files (agents claim work here) |
| `claude/decisions/` | Architecture decision records |
| `.claude/commands/` | Slash command skill files (`/dev`, `/test`, `/build`, etc.) |
| `frontend/` | React app (new projects only) |
| `backend/` | Django / FastAPI / Node app (new projects only) |
| `docker-compose.yml` | Orchestration (new projects only) |

## Development

```bash
git clone https://github.com/sp18-sivaranjan-goswami/project-toolkit.git
cd project-toolkit
pip install -e ".[dev]"
pytest tests/ --cov=src/proj_toolkit
```
