"""Claude API integration for retrofit stack detection and file generation.

Uses the `claude` CLI in headless mode (-p) so that authentication is handled
transparently by Claude Code regardless of whether the user authenticated via
OAuth or API key. Falls back to the Anthropic SDK if ANTHROPIC_API_KEY is set.
"""

from __future__ import annotations

import json
import re
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
# Public API
# ---------------------------------------------------------------------------

def detect_stack(context: "RepoContext", model: str = "claude-sonnet-4-6") -> StackInfo:  # noqa: F821
    """Detect the tech stack by calling Claude. Returns structured StackInfo."""
    prompt = f"""\
Analyze this repository and return a JSON object identifying the tech stack.
Return ONLY the JSON object — no explanation, no markdown fences.

Required JSON schema:
{{
  "language": "<python|javascript|typescript|go|rust|java|ruby|other>",
  "frontend": "<react|vue|angular|svelte|nextjs|nuxtjs|none|unknown>",
  "backend": "<django|fastapi|flask|express|nestjs|rails|spring|none|unknown>",
  "database": "<postgresql|mysql|sqlite|mongodb|redis|none|unknown>",
  "testing": "<pytest|jest|vitest|mocha|rspec|none|unknown>",
  "package_manager": "<npm|yarn|pnpm|pip|poetry|cargo|bundler|unknown>",
  "is_monorepo": <true|false>,
  "notable_patterns": ["<up to 5 patterns>"],
  "confidence": "<high|medium|low>"
}}

Repository context:

{context.to_prompt_text()}
"""
    raw = _call_claude(prompt, model=model)
    data = _parse_json(raw)
    return StackInfo(
        language=data.get("language", "unknown"),
        frontend=data.get("frontend", "unknown"),
        backend=data.get("backend", "unknown"),
        database=data.get("database", "unknown"),
        testing=data.get("testing", "unknown"),
        package_manager=data.get("package_manager", "unknown"),
        is_monorepo=bool(data.get("is_monorepo", False)),
        notable_patterns=data.get("notable_patterns", []),
        confidence=data.get("confidence", "low"),
    )


def generate_retrofit_files(
    project_name: str,
    context: "RepoContext",  # noqa: F821
    stack: StackInfo,
    model: str = "claude-sonnet-4-6",
) -> RetrofitFiles:
    """Call Claude to generate all retrofit documentation files."""
    prompt = f"""\
You are an expert developer assistant specialising in Claude Code agentic workflows.
Generate three Markdown documentation files for the project "{project_name}".
Base everything on the actual repository — do not use generic placeholders.

## Detected Stack
{stack.to_summary()}

## Repository Context
{context.to_prompt_text()}

---

Output the three files using EXACTLY these delimiters (nothing before the first delimiter):

<<<CLAUDE.md>>>
Write CLAUDE.md here — root-level instructions for Claude Code agents.
Include: project overview, exact dev/test/build/lint commands for this stack,
key file paths, coding conventions inferred from the code, agent boundaries.

<<<context.md>>>
Write claude/context.md here — structured reference for agents.
Include: architecture overview, module/directory descriptions based on the real
directory structure, key dependencies, data flow if inferrable, external services.

<<<AGENTS.md>>>
Write claude/AGENTS.md here — multi-agent coordination rules.
Define agent boundaries based on the actual directory layout, task file protocol,
and any repo-specific constraints agents must respect.

<<<SKILLS>>>
List slash command skill names for this stack, one per line, no bullets.
Choose only from: dev, build, test, commit, review, migrate, lint, deploy, seed
"""
    raw = _call_claude(prompt, model=model)
    return _parse_retrofit_files(raw)


# ---------------------------------------------------------------------------
# Transport: claude CLI (primary) or Anthropic SDK (fallback)
# ---------------------------------------------------------------------------

def _call_claude(prompt: str, model: str = "claude-sonnet-4-6") -> str:
    """Call Claude via the `claude` CLI or Anthropic SDK and return the text response."""
    if shutil.which("claude"):
        return _call_via_cli(prompt, model)
    return _call_via_sdk(prompt, model)


def _call_via_cli(prompt: str, model: str) -> str:
    """Use `claude -p` (Claude Code headless mode). Handles auth transparently."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json", "--model", model],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI exited with code {result.returncode}.\n"
            f"stderr: {result.stderr.strip()}"
        )
    try:
        data = json.loads(result.stdout)
        return data.get("result", result.stdout)
    except json.JSONDecodeError:
        return result.stdout


def _call_via_sdk(prompt: str, model: str) -> str:
    """Fall back to direct Anthropic SDK (requires ANTHROPIC_API_KEY)."""
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract first JSON object from the text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"Could not parse JSON from response:\n{text[:300]}")


def _parse_retrofit_files(raw: str) -> RetrofitFiles:
    def _extract(marker: str, next_markers: List[str]) -> str:
        start_tag = f"<<<{marker}>>>"
        start = raw.find(start_tag)
        if start == -1:
            return ""
        start += len(start_tag)
        end = len(raw)
        for nm in next_markers:
            pos = raw.find(f"<<<{nm}>>>", start)
            if 0 < pos < end:
                end = pos
        return raw[start:end].strip()

    claude_md = _extract("CLAUDE.md", ["context.md", "AGENTS.md", "SKILLS"])
    context_md = _extract("context.md", ["AGENTS.md", "SKILLS"])
    agents_md = _extract("AGENTS.md", ["SKILLS"])
    skills_raw = _extract("SKILLS", [])

    suggested_skills = [
        line.strip().lstrip("- ").strip()
        for line in skills_raw.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    return RetrofitFiles(
        claude_md=claude_md,
        context_md=context_md,
        agents_md=agents_md,
        suggested_skills=suggested_skills,
    )
