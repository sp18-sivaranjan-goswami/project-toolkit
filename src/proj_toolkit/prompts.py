"""Interactive prompt logic for proj-toolkit."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proj_toolkit.config import (
    BackendFramework,
    FrontendFramework,
    Language,
    ProjectConfig,
    RetrofitConfig,
)
from proj_toolkit.validator import ValidationError, validate_empty_directory, validate_prd_path

console = Console()


def _ask(prompt: str, default: str | None = None) -> str:
    """Prompt for a non-empty string."""
    while True:
        value = typer.prompt(prompt, default=default or "")
        if value.strip():
            return value.strip()
        console.print("[red]Value cannot be empty.[/red]")


def _select(prompt: str, choices: list[str], default: str) -> str:
    """Display numbered choices and return selected value."""
    console.print(f"\n[bold]{prompt}[/bold]")
    for i, choice in enumerate(choices, 1):
        marker = " [dim](default)[/dim]" if choice == default else ""
        console.print(f"  {i}. {choice}{marker}")
    while True:
        raw = typer.prompt(
            f"Enter number [1-{len(choices)}]",
            default=str(choices.index(default) + 1),
        )
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        console.print(f"[red]Please enter a number between 1 and {len(choices)}.[/red]")


def collect_retrofit_config(
    target_dir: Path,
    doc_paths: list[Path],
    model: str,
) -> RetrofitConfig:
    """Prompt flow for retrofit mode (existing, non-empty repo)."""
    console.print(
        Panel.fit(
            "[bold cyan]proj-toolkit — retrofit mode[/bold cyan]\n"
            "Add Claude Code agentic support to an existing project.",
            border_style="cyan",
        )
    )

    # Project name
    default_name = target_dir.name or "my-project"
    project_name = _ask("Project name", default=default_name)

    # Docs — accept additional paths beyond those passed via CLI
    resolved_docs: list[Path] = list(doc_paths)
    if not resolved_docs:
        console.print(
            "\n[dim]You can link documentation (PDF or Markdown) to improve generated context.[/dim]"
        )
        raw = typer.prompt(
            "Path to documentation file (optional, press Enter to skip)",
            default="",
        )
        if raw.strip():
            p = Path(raw.strip()).expanduser().resolve()
            if p.exists() and p.is_file():
                resolved_docs.append(p)
                console.print(f"[green]✓[/green] Doc linked: {p.name}")
            else:
                console.print(f"[yellow]Warning:[/yellow] {p} not found — skipping.")

    # Model
    console.print(
        "\n[dim]Model for file generation:[/dim]\n"
        "  1. Sonnet (default — fast, cost-efficient)\n"
        "  2. Opus   (slower, higher quality for complex repos)\n"
    )
    raw_model = typer.prompt("Enter number [1-2]", default="1")
    chosen_model = (
        "claude-opus-4-7" if raw_model.strip() == "2" else model
    )

    # Conflict warning
    from proj_toolkit.retrofitter import check_conflicts
    conflicts = check_conflicts(target_dir)
    if conflicts:
        console.print(
            "\n[yellow]Warning:[/yellow] These files already exist and will be overwritten:\n"
            + "\n".join(f"  • {c}" for c in conflicts)
        )
        if not typer.confirm("\nProceed and overwrite?", default=False):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(code=0)

    return RetrofitConfig(
        project_name=project_name,
        doc_paths=resolved_docs,
        model=chosen_model,
    )


def collect_config(target_dir: Path) -> ProjectConfig:
    """Run the interactive prompt flow and return a ProjectConfig."""

    console.print(
        Panel.fit(
            "[bold cyan]proj-toolkit[/bold cyan]\n"
            "Scaffold a full-stack monorepo for Claude Code agentic development.",
            border_style="cyan",
        )
    )

    # 1. Validate directory is empty
    try:
        validate_empty_directory(target_dir)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 2. Project name
    default_name = target_dir.resolve().name or "my-project"
    project_name = _ask("Project name", default=default_name)

    # 3. PRD path
    prd_path_str: str | None = None
    while prd_path_str is None:
        raw = _ask("Path to PRD file (Markdown)")
        try:
            resolved = validate_prd_path(raw)
            prd_path_str = str(resolved)
        except ValidationError as e:
            console.print(f"[red]{e}[/red]")

    # 4. Frontend framework
    fe_choices = [f.value for f in FrontendFramework]
    fe_framework = FrontendFramework(
        _select("Frontend framework", fe_choices, FrontendFramework.REACT.value)
    )

    # 5. Frontend language
    fe_lang_choices = [Language.JAVASCRIPT.value, Language.TYPESCRIPT.value]
    fe_language = Language(
        _select("Frontend language", fe_lang_choices, Language.TYPESCRIPT.value)
    )

    # 6. Backend framework
    be_choices = [f.value for f in BackendFramework]
    be_framework = BackendFramework(
        _select("Backend framework", be_choices, BackendFramework.FASTAPI.value)
    )

    # 7. Backend language — only shown for Node
    if be_framework == BackendFramework.NODE:
        be_lang_choices = [Language.JAVASCRIPT.value, Language.TYPESCRIPT.value]
        be_language = Language(
            _select("Backend language", be_lang_choices, Language.TYPESCRIPT.value)
        )
    else:
        be_language = Language.PYTHON

    # 8. Summary + confirm
    _print_summary(
        project_name, prd_path_str, fe_framework, fe_language, be_framework, be_language
    )
    confirmed = typer.confirm("Proceed with scaffolding?", default=False)
    if not confirmed:
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=0)

    return ProjectConfig(
        project_name=project_name,
        prd_path=prd_path_str,
        frontend_framework=fe_framework,
        frontend_language=fe_language,
        backend_framework=be_framework,
        backend_language=be_language,
    )


def _print_summary(
    project_name: str,
    prd_path: str,
    fe_framework: FrontendFramework,
    fe_language: Language,
    be_framework: BackendFramework,
    be_language: Language,
) -> None:
    table = Table(title="Configuration Summary", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="dim")
    table.add_column("Value")

    table.add_row("Project name", project_name)
    table.add_row("PRD path", prd_path)
    table.add_row("Frontend", f"{fe_framework.value} ({fe_language.value})")
    table.add_row("Backend", f"{be_framework.value} ({be_language.value})")

    console.print()
    console.print(table)
    console.print()
