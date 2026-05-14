"""Generates Claude Code skill files (.claude/commands/*.md) for scaffolded and retrofitted projects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from proj_toolkit.config import BackendFramework, ProjectConfig

if TYPE_CHECKING:
    from proj_toolkit.ai_writer import StackInfo


@dataclass
class SkillSpec:
    name: str        # becomes the slash command, e.g. "build" -> /build
    content: str     # markdown content of the skill file


def generate_skills(config: ProjectConfig) -> List[SkillSpec]:
    skills = [
        _dev_skill(config),
        _build_skill(config),
        _test_skill(config),
        _commit_skill(),
        _review_skill(),
    ]
    if config.backend_framework == BackendFramework.DJANGO:
        skills.append(_migrate_skill())
    return skills


def _dev_skill(config: ProjectConfig) -> SkillSpec:
    backend_cmd = _backend_dev_cmd(config)
    return SkillSpec(
        name="dev",
        content=f"""\
Start the development servers for the full stack.

## Steps

1. Open two terminal panes (or use tmux/background processes).
2. Start the **frontend** dev server:
   ```bash
   cd frontend
   npm install   # only needed first time or after dependency changes
   npm run dev
   ```
   Frontend will be available at http://localhost:5173

3. Start the **backend** dev server:
   ```bash
   cd backend
{backend_cmd}
   ```
   Backend will be available at http://localhost:{_backend_port(config)}

4. Confirm both servers are running by checking their health endpoints.

If the user provides `$ARGUMENTS`, treat them as additional flags or context for the startup.
""",
    )


def _build_skill(config: ProjectConfig) -> SkillSpec:
    backend_build = _backend_build_cmd(config)
    return SkillSpec(
        name="build",
        content=f"""\
Build both the frontend and backend for production.

## Steps

1. Build the **frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   Output goes to `frontend/dist/`.

2. Build the **backend**:
   ```bash
   cd backend
{backend_build}
   ```

3. Report any build errors to the user and fix them before proceeding.

If `$ARGUMENTS` specifies only `frontend` or `backend`, build only that service.
""",
    )


def _test_skill(config: ProjectConfig) -> SkillSpec:
    test_cmd = _backend_test_cmd(config)
    return SkillSpec(
        name="test",
        content=f"""\
Run the test suite for the project.

## Steps

1. Run **frontend** tests (if a test script exists in `frontend/package.json`):
   ```bash
   cd frontend
   npm test -- --run
   ```
   Skip gracefully if no test script is configured.

2. Run **backend** tests:
   ```bash
   cd backend
{test_cmd}
   ```

3. Report pass/fail counts and any failures with their error messages.
4. If tests fail, investigate the root cause and fix before marking done.

If `$ARGUMENTS` specifies only `frontend` or `backend`, test only that service.
""",
    )


def _commit_skill() -> SkillSpec:
    return SkillSpec(
        name="commit",
        content="""\
Create a well-formed git commit for the current staged and unstaged changes.

## Steps

1. Run `git status` and `git diff` to understand what has changed.
2. Run `git log --oneline -5` to see the recent commit style.
3. Stage all relevant changes:
   ```bash
   git add <specific files>
   ```
   Avoid `git add -A` — stage files selectively to avoid committing `.env` or build artifacts.
4. Write a commit message following this format:
   - First line: `<type>(<scope>): <short summary>` (50 chars max)
   - Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
   - Blank line, then optional body explaining *why* not *what*
5. Commit:
   ```bash
   git commit -m "<message>"
   ```
6. Run `git status` to confirm the working tree is clean.

If `$ARGUMENTS` is provided, use it as the commit message or additional context.
""",
    )


def _review_skill() -> SkillSpec:
    return SkillSpec(
        name="review",
        content="""\
Review the current code changes for quality, correctness, and security.

## Steps

1. Run `git diff HEAD` (or `git diff main...HEAD` for a branch review) to see all changes.
2. Evaluate the diff against this checklist:

   **Correctness**
   - [ ] Logic is correct and handles edge cases
   - [ ] No unintended side effects
   - [ ] Error paths are handled

   **Security**
   - [ ] No secrets or credentials hardcoded
   - [ ] User inputs are validated at boundaries
   - [ ] No obvious injection vectors (SQL, command, XSS)

   **Quality**
   - [ ] Code is readable and self-explanatory
   - [ ] No dead code or unused imports left behind
   - [ ] Consistent with surrounding code style

   **Tests**
   - [ ] New behaviour has test coverage
   - [ ] Existing tests still pass

3. Report findings grouped by severity: **blocking**, **suggestion**, **nit**.
4. If `$ARGUMENTS` specifies a file or directory, scope the review to that path.
""",
    )


def _migrate_skill() -> SkillSpec:
    return SkillSpec(
        name="migrate",
        content="""\
Create and apply Django database migrations.

## Steps

1. If new models or model changes exist, create migrations:
   ```bash
   cd backend
   python manage.py makemigrations
   ```
2. Review the generated migration file in `backend/*/migrations/` — confirm it captures the
   intended schema change.
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```
4. Confirm by running `python manage.py showmigrations` and verifying all are marked `[X]`.

If `$ARGUMENTS` specifies an app name, pass it to `makemigrations` to scope the migration.
""",
    )


# ---------------------------------------------------------------------------
# Retrofit skill generation (no ProjectConfig available)
# ---------------------------------------------------------------------------

def generate_retrofit_skills(stack: "StackInfo", skill_names: List[str]) -> List[SkillSpec]:
    """Generate skill specs for an existing repo based on detected stack."""
    builders = {
        "dev": lambda: _retrofit_dev_skill(stack),
        "build": lambda: _retrofit_build_skill(stack),
        "test": lambda: _retrofit_test_skill(stack),
        "lint": lambda: _retrofit_lint_skill(stack),
        "commit": _commit_skill,
        "review": _review_skill,
        "migrate": _migrate_skill,
        "deploy": _retrofit_deploy_skill,
        "seed": _retrofit_seed_skill,
    }
    skills = []
    for name in skill_names:
        builder = builders.get(name)
        if builder:
            skills.append(builder())
        else:
            skills.append(_generic_skill(name))
    return skills


def _retrofit_dev_skill(stack: "StackInfo") -> SkillSpec:
    steps = _dev_steps_for_stack(stack)
    return SkillSpec(
        name="dev",
        content=f"""\
Start the development server(s) for this project.

## Steps

{steps}

If `$ARGUMENTS` provides additional flags or context, apply them to the appropriate server command.
""",
    )


def _retrofit_build_skill(stack: "StackInfo") -> SkillSpec:
    steps = _build_steps_for_stack(stack)
    return SkillSpec(
        name="build",
        content=f"""\
Build the project for production.

## Steps

{steps}

Report any build errors and fix them before marking this task done.
If `$ARGUMENTS` specifies a subset (e.g. `frontend` or `backend`), build only that part.
""",
    )


def _retrofit_test_skill(stack: "StackInfo") -> SkillSpec:
    cmd = _test_cmd_for_stack(stack)
    return SkillSpec(
        name="test",
        content=f"""\
Run the test suite.

## Steps

1. Run tests:
   ```bash
{cmd}
   ```
2. Report pass/fail counts and failure details.
3. If tests fail, investigate the root cause and fix before marking done.

If `$ARGUMENTS` specifies a path or pattern, scope the test run accordingly.
""",
    )


def _retrofit_lint_skill(stack: "StackInfo") -> SkillSpec:
    cmd = _lint_cmd_for_stack(stack)
    return SkillSpec(
        name="lint",
        content=f"""\
Run the linter and fix any issues.

## Steps

1. Run linter:
   ```bash
{cmd}
   ```
2. Fix all reported issues.
3. Re-run to confirm a clean result.

If `$ARGUMENTS` specifies a path, scope the lint run to that path.
""",
    )


def _retrofit_deploy_skill() -> SkillSpec:
    return SkillSpec(
        name="deploy",
        content="""\
Deploy the project.

## Steps

1. Ensure all tests pass (`/test`) and the build succeeds (`/build`).
2. Check the deployment target and any environment-specific configuration.
3. Execute the deployment command for this project.
4. Verify the deployment succeeded by checking logs or a health endpoint.

If `$ARGUMENTS` specifies an environment (e.g. `staging`, `production`), deploy to that target.
""",
    )


def _retrofit_seed_skill() -> SkillSpec:
    return SkillSpec(
        name="seed",
        content="""\
Seed the database with initial or test data.

## Steps

1. Locate the seed script or fixture files for this project.
2. Ensure the database is running and migrations are applied.
3. Run the seed command.
4. Confirm by querying the database or running a smoke test.

If `$ARGUMENTS` specifies a dataset name or environment, use the appropriate seed file.
""",
    )


def _generic_skill(name: str) -> SkillSpec:
    return SkillSpec(
        name=name,
        content=f"""\
Run the {name} workflow for this project.

## Steps

1. Understand the current state by reading relevant files.
2. Execute the {name} process appropriate for this stack.
3. Report results and any errors encountered.

If `$ARGUMENTS` is provided, use it as additional context or flags.
""",
    )


# --- stack-aware command helpers ---

def _dev_steps_for_stack(stack: "StackInfo") -> str:
    steps = []
    n = 1

    if stack.frontend not in ("none", "unknown"):
        steps.append(
            f"{n}. Start the **frontend** dev server:\n"
            "   ```bash\n"
            f"   cd frontend\n"
            f"   {_frontend_install_cmd(stack)} && {_frontend_dev_cmd(stack)}\n"
            "   ```"
        )
        n += 1

    if stack.backend not in ("none", "unknown"):
        steps.append(
            f"{n}. Start the **backend** dev server:\n"
            "   ```bash\n"
            f"   cd backend\n"
            f"   {_backend_dev_cmd_for_stack(stack)}\n"
            "   ```"
        )
        n += 1

    if not steps:
        steps.append(
            f"{n}. Identify the dev server command from the project's README or Makefile and run it."
        )

    return "\n\n".join(steps)


def _build_steps_for_stack(stack: "StackInfo") -> str:
    steps = []
    n = 1

    if stack.frontend not in ("none", "unknown"):
        steps.append(
            f"{n}. Build the **frontend**:\n"
            "   ```bash\n"
            f"   cd frontend && {_frontend_install_cmd(stack)} && {_frontend_build_cmd(stack)}\n"
            "   ```"
        )
        n += 1

    if stack.backend not in ("none", "unknown"):
        steps.append(
            f"{n}. Build/install the **backend**:\n"
            "   ```bash\n"
            f"   cd backend && {_backend_install_cmd_for_stack(stack)}\n"
            "   ```"
        )
        n += 1

    if not steps:
        steps.append(f"{n}. Locate and run the build command from the project's Makefile or README.")

    return "\n\n".join(steps)


def _test_cmd_for_stack(stack: "StackInfo") -> str:
    if stack.testing == "pytest":
        return "   pytest"
    if stack.testing in ("jest", "vitest"):
        return f"   npm test -- --run" if stack.testing == "vitest" else "   npm test"
    if stack.testing == "mocha":
        return "   npm test"
    if stack.testing == "rspec":
        return "   bundle exec rspec"
    if stack.language == "go":
        return "   go test ./..."
    if stack.language == "rust":
        return "   cargo test"
    return "   # Run tests per the project README"


def _lint_cmd_for_stack(stack: "StackInfo") -> str:
    if stack.language == "python":
        return "   ruff check . && ruff format --check ."
    if stack.language in ("javascript", "typescript"):
        return "   npm run lint"
    if stack.language == "go":
        return "   golangci-lint run"
    if stack.language == "rust":
        return "   cargo clippy"
    return "   # Run linter per the project README"


def _frontend_install_cmd(stack: "StackInfo") -> str:
    if stack.package_manager == "yarn":
        return "yarn"
    if stack.package_manager == "pnpm":
        return "pnpm install"
    return "npm install"


def _frontend_dev_cmd(stack: "StackInfo") -> str:
    if stack.frontend in ("nextjs", "nuxtjs"):
        pm = stack.package_manager if stack.package_manager in ("yarn", "pnpm") else "npm"
        return f"{pm} run dev"
    return "npm run dev"


def _frontend_build_cmd(stack: "StackInfo") -> str:
    pm = stack.package_manager if stack.package_manager in ("yarn", "pnpm") else "npm"
    return f"{pm} run build"


def _backend_dev_cmd_for_stack(stack: "StackInfo") -> str:
    if stack.backend == "django":
        return "pip install -r requirements.txt && python manage.py migrate && python manage.py runserver"
    if stack.backend == "fastapi":
        return "pip install -r requirements.txt && uvicorn app.main:app --reload"
    if stack.backend == "flask":
        return "pip install -r requirements.txt && flask run --debug"
    if stack.backend == "express":
        return "npm install && npm run dev"
    if stack.backend == "nestjs":
        return "npm install && npm run start:dev"
    if stack.backend == "rails":
        return "bundle install && rails server"
    if stack.language == "go":
        return "go run ."
    return "# Start backend per the project README"


def _backend_install_cmd_for_stack(stack: "StackInfo") -> str:
    if stack.language == "python":
        return "pip install -r requirements.txt"
    if stack.language in ("javascript", "typescript"):
        return "npm install"
    if stack.language == "go":
        return "go build ./..."
    if stack.language == "rust":
        return "cargo build --release"
    return "# Install dependencies per the project README"


# --- helpers ---

def _backend_port(config: ProjectConfig) -> int:
    return 3000 if config.backend_framework == BackendFramework.NODE else 8000


def _backend_dev_cmd(config: ProjectConfig) -> str:
    if config.backend_framework == BackendFramework.DJANGO:
        return "   pip install -r requirements.txt   # only needed first time\n   python manage.py migrate\n   python manage.py runserver"
    if config.backend_framework == BackendFramework.FASTAPI:
        return "   pip install -r requirements.txt   # only needed first time\n   uvicorn app.main:app --reload"
    # Node
    return "   npm install   # only needed first time\n   npm run dev"


def _backend_build_cmd(config: ProjectConfig) -> str:
    if config.backend_framework in (BackendFramework.DJANGO, BackendFramework.FASTAPI):
        return "   pip install -r requirements.txt"
    # Node
    return "   npm install\n   npm run build"


def _backend_test_cmd(config: ProjectConfig) -> str:
    if config.backend_framework == BackendFramework.DJANGO:
        return "   python manage.py test"
    if config.backend_framework == BackendFramework.FASTAPI:
        return "   pip install pytest pytest-asyncio httpx\n   pytest"
    # Node
    return "   npm test"
