# proj-toolkit

CLI scaffolding tool for full-stack monorepos pre-configured for Claude Code agentic development.

## Installation

```bash
pip install proj-toolkit
```

## Usage

```bash
mkdir my-project && cd my-project
proj-toolkit
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ --cov=src/proj_toolkit
```
