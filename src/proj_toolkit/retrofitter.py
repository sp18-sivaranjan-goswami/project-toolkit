"""Writes agentic support files into an existing repository."""

from __future__ import annotations

from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from proj_toolkit.ai_writer import RetrofitFiles, StackInfo
from proj_toolkit.config import RetrofitConfig
from proj_toolkit.skills import generate_retrofit_skills

console = Console()


def check_conflicts(target_dir: Path) -> List[str]:
    """Return paths of files that already exist and would be overwritten."""
    candidates = [
        target_dir / "CLAUDE.md",
        target_dir / "claude" / "context.md",
        target_dir / "claude" / "AGENTS.md",
    ]
    return [str(p.relative_to(target_dir)) for p in candidates if p.exists()]


def preview_files(files: RetrofitFiles, stack: StackInfo) -> None:
    """Print a preview of the generated file contents to the terminal."""
    console.print("\n[bold]Preview of generated files:[/bold]\n")

    for label, content in [
        ("CLAUDE.md", files.claude_md),
        ("claude/context.md", files.context_md),
        ("claude/AGENTS.md", files.agents_md),
    ]:
        preview_lines = content.strip().splitlines()[:12]
        preview = "\n".join(preview_lines)
        if len(content.strip().splitlines()) > 12:
            preview += "\n…"
        console.print(Panel(
            Syntax(preview, "markdown", theme="github-dark", word_wrap=True),
            title=f"[cyan]{label}[/cyan]",
            expand=False,
        ))

    if files.suggested_skills:
        console.print(
            f"\n[dim]Skill files:[/dim] "
            + ", ".join(f"[cyan]/{s}[/cyan]" for s in files.suggested_skills)
        )
    console.print()


def retrofit(
    config: RetrofitConfig,
    target_dir: Path,
    stack: StackInfo,
    files: RetrofitFiles,
) -> None:
    """Write all agentic support files into the existing repo."""
    written: List[str] = []

    # CLAUDE.md
    _write(target_dir / "CLAUDE.md", files.claude_md, target_dir, written)

    # claude/ directory
    claude_dir = target_dir / "claude"
    claude_dir.mkdir(exist_ok=True)
    _write(claude_dir / "context.md", files.context_md, target_dir, written)
    _write(claude_dir / "AGENTS.md", files.agents_md, target_dir, written)

    for subdir in ("tasks", "decisions"):
        d = claude_dir / subdir
        d.mkdir(exist_ok=True)
        gk = d / ".gitkeep"
        if not gk.exists():
            gk.touch()
    written.extend(["claude/tasks/", "claude/decisions/"])

    # .claude/commands/ skill files
    commands_dir = target_dir / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    skill_specs = generate_retrofit_skills(stack, files.suggested_skills)
    for skill in skill_specs:
        _write(commands_dir / f"{skill.name}.md", skill.content, target_dir, written)

    # Summary
    console.print("\n[bold green]Done![/bold green] Files written:\n")
    for name in written:
        console.print(f"  [green]✓[/green] {name}")

    console.print(
        f"\n[bold]Next steps:[/bold]\n"
        f"  1. Review [bold]CLAUDE.md[/bold] and adjust any commands or paths that need fixing\n"
        f"  2. Review [bold]claude/AGENTS.md[/bold] and refine the agent boundaries for your workflow\n"
        f"  3. Open this directory with Claude Code and start building!\n"
    )


def _write(path: Path, content: str, base: Path, written: List[str]) -> None:
    path.write_text(content, encoding="utf-8")
    try:
        written.append(str(path.relative_to(base)))
    except ValueError:
        written.append(str(path))
