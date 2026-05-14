"""FastAPI backend framework plugin."""

from __future__ import annotations

from typing import List

from proj_toolkit.config import Language, register_backend
from proj_toolkit.frameworks.base import FileSpec, FrameworkPlugin


@register_backend
class FastAPIPlugin(FrameworkPlugin):
    name = "fastapi"
    supported_languages = [Language.PYTHON]

    def generate_files(self, language: Language, project_name: str) -> List[FileSpec]:
        files: List[FileSpec] = []

        # app/main.py
        files.append(FileSpec(
            relative_path="app/main.py",
            content=f"""\
from fastapi import FastAPI

app = FastAPI(title="{project_name}", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {{"status": "ok"}}
""",
        ))

        # app/__init__.py
        files.append(FileSpec(relative_path="app/__init__.py", content=""))

        # app/routers/__init__.py
        files.append(FileSpec(relative_path="app/routers/__init__.py", content=""))

        # app/models/__init__.py
        files.append(FileSpec(relative_path="app/models/__init__.py", content=""))

        # requirements.txt
        files.append(FileSpec(
            relative_path="requirements.txt",
            content="""\
fastapi>=0.111
uvicorn[standard]>=0.30
pydantic>=2.0
python-dotenv>=1.0
""",
        ))

        # .env.example
        files.append(FileSpec(
            relative_path=".env.example",
            content="""\
APP_ENV=development
PORT=8000
""",
        ))

        # README.md
        files.append(FileSpec(
            relative_path="README.md",
            content=f"""\
# {project_name} — Backend (FastAPI)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

- API docs: `http://localhost:8000/docs`
- Health check: `GET /health`
""",
        ))

        return files

    def readme_snippet(self, language: Language) -> str:
        return """\
### Backend (FastAPI)

- App entrypoint: `backend/app/main.py`
- Run `uvicorn app.main:app --reload` from `backend/` (default port 8000)
- Routers go in `backend/app/routers/`, Pydantic models in `backend/app/models/`
- Interactive docs: `http://localhost:8000/docs`
- Health endpoint: `GET /health`
"""

    def dockerfile_content(self, language: Language, project_name: str) -> str:
        return """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
