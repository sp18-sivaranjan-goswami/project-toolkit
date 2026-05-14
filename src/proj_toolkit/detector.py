"""Collects context from an existing repository without making any LLM calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "target", "vendor", "eggs", ".eggs",
    ".tox", "htmlcov", ".turbo", ".vercel", ".output",
}

_ROOT_CONFIG_FILES = [
    "package.json", "pyproject.toml", "setup.cfg", "requirements.txt",
    "requirements-dev.txt", "go.mod", "Cargo.toml", "Gemfile",
    "Makefile", "docker-compose.yml", "docker-compose.yaml",
    "tsconfig.json", "vite.config.ts", "vite.config.js",
    "next.config.js", "next.config.ts", "nuxt.config.ts",
    "tailwind.config.js", "tailwind.config.ts",
    "manage.py", "app.py", "main.py",
]

_SUBDIR_CONFIG_FILES = ["package.json", "pyproject.toml", "requirements.txt", "go.mod"]

_MAX_FILE_CHARS = 8_000


@dataclass
class RepoContext:
    tree: str
    config_files: Dict[str, str]
    doc_content: Optional[str] = None

    def to_prompt_text(self) -> str:
        parts = ["## Directory Tree\n\n```\n" + self.tree + "\n```"]

        if self.config_files:
            parts.append("## Key Configuration Files")
            for path, content in self.config_files.items():
                parts.append(f"### `{path}`\n```\n{content}\n```")

        if self.doc_content:
            parts.append("## Linked Documentation\n\n" + self.doc_content)

        return "\n\n".join(parts)


def collect_repo_context(target_dir: Path, doc_paths: List[Path]) -> RepoContext:
    """Build a RepoContext from an existing directory. No network calls."""
    tree = _build_tree(target_dir)
    config_files = _read_config_files(target_dir)
    doc_content = _read_docs(doc_paths) if doc_paths else None
    return RepoContext(tree=tree, config_files=config_files, doc_content=doc_content)


def _build_tree(root: Path, max_depth: int = 4) -> str:
    lines: List[str] = [root.name + "/"]

    def _walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            all_entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        # Keep visible entries and selected dotfiles
        important_dotfiles = {".env.example", ".github", ".gitignore", ".dockerignore"}
        entries = [
            e for e in all_entries
            if (not e.name.startswith(".") or e.name in important_dotfiles)
            and e.name not in _SKIP_DIRS
        ]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + entry.name + ("/" if entry.is_dir() else ""))
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1)

    _walk(root, "", 1)
    return "\n".join(lines)


def _read_config_files(root: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}

    for name in _ROOT_CONFIG_FILES:
        p = root / name
        if p.exists() and p.is_file():
            result[name] = _read_truncated(p)

    # One level deep for frontend/, backend/, src/, app/, etc.
    for subdir in sorted(root.iterdir()):
        if not subdir.is_dir() or subdir.name in _SKIP_DIRS or subdir.name.startswith("."):
            continue
        for name in _SUBDIR_CONFIG_FILES:
            p = subdir / name
            if p.exists() and p.is_file():
                result[f"{subdir.name}/{name}"] = _read_truncated(p)

    return result


def _read_truncated(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return content[:_MAX_FILE_CHARS]
    except OSError:
        return "[unreadable]"


def _read_docs(doc_paths: List[Path]) -> str:
    parts: List[str] = []
    for path in doc_paths:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            parts.append(f"### {path.name}\n\n{_extract_pdf(path)}")
        else:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                parts.append(f"### {path.name}\n\n{content[:12_000]}")
            except OSError:
                parts.append(f"### {path.name}\n\n[Could not read file]")
    return "\n\n".join(parts)


def _extract_pdf(path: Path) -> str:
    try:
        import pypdf  # type: ignore
        reader = pypdf.PdfReader(str(path))
        texts = [page.extract_text() or "" for page in reader.pages[:20]]
        return "\n".join(texts)[:15_000]
    except ImportError:
        return (
            "[PDF parsing requires the `pypdf` package. "
            "Install it with: pip install 'proj-toolkit[pdf]']\n"
            f"File skipped: {path}"
        )
    except Exception as exc:
        return f"[Could not parse PDF: {exc}]"
