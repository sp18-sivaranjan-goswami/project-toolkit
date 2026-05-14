"""Node/Express backend framework plugin."""

from __future__ import annotations

from typing import List

from proj_toolkit.config import Language, register_backend
from proj_toolkit.frameworks.base import FileSpec, FrameworkPlugin


@register_backend
class NodePlugin(FrameworkPlugin):
    name = "node"
    supported_languages = [Language.JAVASCRIPT, Language.TYPESCRIPT]

    def generate_files(self, language: Language, project_name: str) -> List[FileSpec]:
        is_ts = language == Language.TYPESCRIPT
        ext = "ts" if is_ts else "js"
        files: List[FileSpec] = []

        # package.json
        dev_deps = ""
        if is_ts:
            dev_deps = """\
    "typescript": "^5.5.3",
    "@types/node": "^22.0.0",
    "@types/express": "^4.17.21",
    "ts-node": "^10.9.2","""

        start_script = "ts-node src/index.ts" if is_ts else "node src/index.js"
        dev_script = (
            "ts-node --watch src/index.ts" if is_ts else "node --watch src/index.js"
        )

        files.append(FileSpec(
            relative_path="package.json",
            content=f"""\
{{
  "name": "{project_name}-backend",
  "version": "0.0.1",
  "private": true,
  "scripts": {{
    "start": "{start_script}",
    "dev": "{dev_script}"
  }},
  "dependencies": {{
    "express": "^4.19.2",
    "dotenv": "^16.4.5"
  }},
  "devDependencies": {{
{dev_deps}
    "nodemon": "^3.1.4"
  }}
}}
""",
        ))

        # src/index.ts or src/index.js
        if is_ts:
            content = f"""\
import express, {{ Request, Response }} from 'express'
import * as dotenv from 'dotenv'

dotenv.config()

const app = express()
const PORT = process.env.PORT ?? 3000

app.use(express.json())

app.get('/health', (_req: Request, res: Response) => {{
  res.json({{ status: 'ok' }})
}})

app.listen(PORT, () => {{
  console.log(`{project_name} backend listening on http://localhost:${{PORT}}`)
}})

export default app
"""
        else:
            content = f"""\
const express = require('express')
require('dotenv').config()

const app = express()
const PORT = process.env.PORT || 3000

app.use(express.json())

app.get('/health', (req, res) => {{
  res.json({{ status: 'ok' }})
}})

app.listen(PORT, () => {{
  console.log(`{project_name} backend listening on http://localhost:${{PORT}}`)
}})

module.exports = app
"""

        files.append(FileSpec(relative_path=f"src/index.{ext}", content=content))

        # tsconfig.json (TypeScript only)
        if is_ts:
            files.append(FileSpec(
                relative_path="tsconfig.json",
                content="""\
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
""",
            ))

        # .env.example
        files.append(FileSpec(
            relative_path=".env.example",
            content="""\
PORT=3000
NODE_ENV=development
""",
        ))

        # .gitignore
        files.append(FileSpec(
            relative_path=".gitignore",
            content="""\
node_modules/
dist/
.env
*.local
""",
        ))

        # README.md
        files.append(FileSpec(
            relative_path="README.md",
            content=f"""\
# {project_name} — Backend (Node/Express)

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Health check: `GET /health`
""",
        ))

        return files

    def readme_snippet(self, language: Language) -> str:
        return f"""\
### Backend (Node/Express — {language.value})

- Entrypoint: `backend/src/index.{("ts" if language == Language.TYPESCRIPT else "js")}`
- Run `npm run dev` from `backend/` to start with hot-reload (default port 3000)
- Health endpoint: `GET /health`
"""

    def dockerfile_content(self, language: Language, project_name: str) -> str:
        if language == Language.TYPESCRIPT:
            return """\
# Stage 1: build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npx tsc

# Stage 2: run
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["node", "dist/index.js"]
"""
        return """\
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"""
