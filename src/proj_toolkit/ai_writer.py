"""Claude API integration for retrofit stack detection and file generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import anthropic

from proj_toolkit.detector import RepoContext

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class StackInfo:
    language: str
    frontend: str
    backend: str
    database: str
    testing: str
    package_manager: str
    is_monorepo: bool
    notable_patterns: List[str]
    confidence: str

    def to_summary(self) -> str:
        lines = [
            f"- Language: {self.language}",
            f"- Frontend: {self.frontend}",
            f"- Backend: {self.backend}",
            f"- Database: {self.database}",
            f"- Testing: {self.testing}",
            f"- Package manager: {self.package_manager}",
            f"- Monorepo: {self.is_monorepo}",
            f"- Confidence: {self.confidence}",
        ]
        if self.notable_patterns:
            lines.append(f"- Notable patterns: {', '.join(self.notable_patterns)}")
        return "\n".join(lines)


@dataclass
class RetrofitFiles:
    claude_md: str
    context_md: str
    agents_md: str
    suggested_skills: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

_DETECT_TOOL: Dict[str, Any] = {
    "name": "report_stack",
    "description": "Report the detected technology stack for the repository.",
    "input_schema": {
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": "Primary programming language",
                "enum": ["python", "javascript", "typescript", "go", "rust", "java", "ruby", "other"],
            },
            "frontend": {
                "type": "string",
                "description": "Frontend framework, or 'none' if backend-only",
                "enum": ["react", "vue", "angular", "svelte", "nextjs", "nuxtjs", "none", "unknown"],
            },
            "backend": {
                "type": "string",
                "description": "Backend framework",
                "enum": ["django", "fastapi", "flask", "express", "nestjs", "rails", "spring", "none", "unknown"],
            },
            "database": {
                "type": "string",
                "enum": ["postgresql", "mysql", "sqlite", "mongodb", "redis", "none", "unknown"],
            },
            "testing": {
                "type": "string",
                "enum": ["pytest", "jest", "vitest", "mocha", "rspec", "unknown", "none"],
            },
            "package_manager": {
                "type": "string",
                "enum": ["npm", "yarn", "pnpm", "pip", "poetry", "cargo", "bundler", "unknown"],
            },
            "is_monorepo": {
                "type": "boolean",
                "description": "True if this appears to be a monorepo with multiple apps/packages",
            },
            "notable_patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 5 notable patterns, e.g. 'REST API', 'GraphQL', 'Docker Compose', 'GitHub Actions CI'",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "How confident you are in this detection",
            },
        },
        "required": [
            "language", "frontend", "backend", "database",
            "testing", "package_manager", "is_monorepo",
            "notable_patterns", "confidence",
        ],
    },
}

_GENERATE_TOOL: Dict[str, Any] = {
    "name": "write_retrofit_files",
    "description": "Write the three Claude Code documentation files for the repository.",
    "input_schema": {
        "type": "object",
        "properties": {
            "claude_md": {
                "type": "string",
                "description": (
                    "Content of CLAUDE.md — root-level instructions for Claude Code agents. "
                    "Include: project overview, stack-specific commands (dev/test/build/lint), "
                    "key file paths, inferred coding conventions, and agent boundaries. "
                    "Be specific to this repo, not generic."
                ),
            },
            "context_md": {
                "type": "string",
                "description": (
                    "Content of claude/context.md — structured reference for agents. "
                    "Include: architecture overview, module/directory descriptions, "
                    "key dependencies, data flow if inferrable, external services."
                ),
            },
            "agents_md": {
                "type": "string",
                "description": (
                    "Content of claude/AGENTS.md — multi-agent coordination rules. "
                    "Define agent boundaries based on actual directory layout, "
                    "task file protocol, and repo-specific constraints."
                ),
            },
            "suggested_skills": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["dev", "build", "test", "commit", "review", "migrate", "lint", "deploy", "seed"],
                },
                "description": "Slash command skill names appropriate for this stack",
            },
        },
        "required": ["claude_md", "context_md", "agents_md", "suggested_skills"],
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_stack(context: RepoContext) -> StackInfo:
    """Call Claude Sonnet to identify the tech stack. Uses tool_use for reliable structure."""
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are a software architecture expert. "
            "Analyze the repository context and call report_stack with your findings."
        ),
        tools=[_DETECT_TOOL],
        tool_choice={"type": "any"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyze this repository and report the tech stack:\n\n"
                    + context.to_prompt_text()
                ),
            }
        ],
    )

    tool_input = _extract_tool_input(response, "report_stack")
    return StackInfo(
        language=tool_input["language"],
        frontend=tool_input["frontend"],
        backend=tool_input["backend"],
        database=tool_input["database"],
        testing=tool_input["testing"],
        package_manager=tool_input["package_manager"],
        is_monorepo=tool_input["is_monorepo"],
        notable_patterns=tool_input.get("notable_patterns", []),
        confidence=tool_input["confidence"],
    )


def generate_retrofit_files(
    project_name: str,
    context: RepoContext,
    stack: StackInfo,
    model: str = "claude-sonnet-4-6",
) -> RetrofitFiles:
    """Call Claude to generate all retrofit documentation files via tool_use."""
    client = anthropic.Anthropic()

    prompt = (
        f'Generate Claude Code documentation files for the project "{project_name}".\n\n'
        f"## Detected Stack\n{stack.to_summary()}\n\n"
        f"## Repository Context\n{context.to_prompt_text()}\n\n"
        "Call write_retrofit_files with precise, repo-specific content for each file. "
        "Do not use generic templates — base everything on the actual files and structure shown above."
    )

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=(
            "You are an expert developer assistant specialising in Claude Code agentic workflows. "
            "You write precise, actionable documentation for Claude Code agents. "
            "Your files are specific to the actual codebase, never generic placeholders."
        ),
        tools=[_GENERATE_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_input = _extract_tool_input(response, "write_retrofit_files")
    return RetrofitFiles(
        claude_md=tool_input["claude_md"],
        context_md=tool_input["context_md"],
        agents_md=tool_input["agents_md"],
        suggested_skills=tool_input.get("suggested_skills", []),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tool_input(response: anthropic.types.Message, tool_name: str) -> Dict[str, Any]:
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input  # type: ignore[return-value]
    raise RuntimeError(
        f"Claude did not call the expected tool '{tool_name}'. "
        f"Stop reason: {response.stop_reason}. "
        f"Response: {response.content}"
    )
