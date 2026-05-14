"""Typer CLI entry point for proj-toolkit."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from proj_toolkit.prompts import collect_config, collect_retrofit_config
from proj_toolkit.scaffolder import scaffold
from proj_toolkit.validator import is_directory_empty

app = typer.Typer(
    name="proj-toolkit",
    help="Scaffold a new monorepo or add Claude Code support to an existing project.",
    add_completion=False,
)
console = Console()


@app.command()
def main(
    directory: Path = typer.Argument(
        default=Path("."),
        help="Target directory (empty = new project, non-empty = retrofit mode).",
        show_default=True,
    ),
    docs: Optional[List[Path]] = typer.Option(
        None,
        "--docs",
        "-d",
        help="Path to a documentation file (PDF or Markdown) to include in analysis. Repeatable.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    model: str = typer.Option(
        "claude-sonnet-4-6",
        "--model",
        "-m",
        help="Claude model for retrofit generation (e.g. claude-opus-4-7 for higher quality).",
    ),
) -> None:
    """
    Run proj-toolkit in the target DIRECTORY.

    \b
    Empty directory   → interactive scaffold of a new full-stack monorepo.
    Non-empty directory → retrofit mode: analyse the existing codebase with Claude
                          and generate CLAUDE.md, claude/, and .claude/commands/.
    """
    target = directory.resolve()

    if not target.exists():
        target.mkdir(parents=True)

    if is_directory_empty(target):
        _run_scaffold(target)
    else:
        _run_retrofit(target, docs or [], model)


# ---------------------------------------------------------------------------
# Scaffold path (new project)
# ---------------------------------------------------------------------------

def _run_scaffold(target: Path) -> None:
    config = collect_config(target)
    console.print("\n[bold]Generating project...[/bold]\n")
    scaffold(config, target)
    console.print(
        f"\n[bold green]Done![/bold green] "
        f"Project [bold]{config.project_name}[/bold] scaffolded in [cyan]{target}[/cyan]\n"
        "Next steps:\n"
        "  1. Review [bold]CLAUDE.md[/bold]\n"
        "  2. Open the monorepo in your editor\n"
        "  3. Start coding with Claude Code!\n"
    )


# ---------------------------------------------------------------------------
# Retrofit path (existing project)
# ---------------------------------------------------------------------------

def _run_retrofit(target: Path, doc_paths: List[Path], model: str) -> None:
    from rich.status import Status

    from proj_toolkit.ai_writer import detect_stack, generate_retrofit_files
    from proj_toolkit.detector import collect_repo_context
    from proj_toolkit.retrofitter import preview_files, retrofit

    config = collect_retrofit_config(target, doc_paths, model)

    # Phase 1 — collect context (no LLM)
    with Status("[bold]Scanning repository...[/bold]", console=console):
        context = collect_repo_context(target, config.doc_paths)

    # Phase 2 — detect stack (Sonnet, fast)
    with Status("[bold]Detecting tech stack...[/bold]", console=console):
        try:
            stack = detect_stack(context)
        except Exception as exc:
            _handle_api_error(exc)
            raise typer.Exit(code=1)

    console.print(f"\n[bold]Detected stack[/bold] (confidence: [cyan]{stack.confidence}[/cyan]):")
    for line in stack.to_summary().splitlines():
        console.print(f"  {line}")

    if not typer.confirm("\nDoes this look correct? Proceed with generating files?", default=True):
        console.print("[yellow]Aborted. You can re-run after adjusting the repository structure.[/yellow]")
        raise typer.Exit(code=0)

    # Phase 3 — generate documentation files
    model_label = "Opus" if "opus" in config.model else "Sonnet"
    with Status(f"[bold]Generating documentation with {model_label}...[/bold]", console=console):
        try:
            files = generate_retrofit_files(
                project_name=config.project_name,
                context=context,
                stack=stack,
                model=config.model,
            )
        except Exception as exc:
            _handle_api_error(exc)
            raise typer.Exit(code=1)

    # Phase 4 — preview + confirm
    preview_files(files, stack)

    if not typer.confirm("Write these files to disk?", default=True):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=0)

    # Phase 5 — write
    retrofit(config, target, stack, files)


def _handle_api_error(exc: Exception) -> None:
    msg = str(exc)
    if "authentication" in msg.lower() or "api_key" in msg.lower() or "auth" in msg.lower():
        console.print(
            "[bold red]Authentication error:[/bold red] Could not authenticate with Claude.\n"
            "Make sure Claude Code is installed and run [bold]claude auth[/bold] to log in."
        )
    elif "rate limit" in msg.lower():
        console.print(
            "[bold red]Rate limit error:[/bold red] Too many requests. Wait a moment and try again."
        )
    else:
        console.print(f"[bold red]Error calling Claude:[/bold red] {exc}")
