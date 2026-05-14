"""React (Vite) frontend framework plugin."""

from __future__ import annotations

import json
from typing import List

from proj_toolkit.config import Language, register_frontend
from proj_toolkit.frameworks.base import FileSpec, FrameworkPlugin


@register_frontend
class ReactPlugin(FrameworkPlugin):
    name = "react"
    supported_languages = [Language.JAVASCRIPT, Language.TYPESCRIPT]

    def generate_files(self, language: Language, project_name: str) -> List[FileSpec]:
        is_ts = language == Language.TYPESCRIPT
        ext = "tsx" if is_ts else "jsx"
        js_ext = "ts" if is_ts else "js"

        files: List[FileSpec] = []

        # package.json — build devDependencies dict then serialize
        dev_deps: dict = {"@vitejs/plugin-react": "^4.3.1"}
        if is_ts:
            dev_deps["typescript"] = "^5.5.3"
            dev_deps["@types/react"] = "^18.3.5"
            dev_deps["@types/react-dom"] = "^18.3.0"
        dev_deps["vite"] = "^5.4.2"

        pkg = {
            "name": f"{project_name}-frontend",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
            "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
            "devDependencies": dev_deps,
        }
        files.append(FileSpec(
            relative_path="package.json",
            content=json.dumps(pkg, indent=2) + "\n",
        ))

        # vite.config
        files.append(FileSpec(
            relative_path=f"vite.config.{js_ext}",
            content=f"""\
import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({{
  plugins: [react()],
}})
""",
        ))

        # index.html
        files.append(FileSpec(
            relative_path="index.html",
            content=f"""\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.{ext}"></script>
  </body>
</html>
""",
        ))

        # src/main
        files.append(FileSpec(
            relative_path=f"src/main.{ext}",
            content=f"""\
import {{ StrictMode }} from 'react'
import {{ createRoot }} from 'react-dom/client'
import App from './App.{ext}'
import './App.css'

createRoot(document.getElementById('root'){"!" if is_ts else ""}).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
""",
        ))

        # src/App
        files.append(FileSpec(
            relative_path=f"src/App.{ext}",
            content=f"""\
{"import React from 'react'" if is_ts else ""}

function App() {{
  return (
    <div className="App">
      <h1>{project_name}</h1>
      <p>Edit <code>src/App.{ext}</code> to get started.</p>
    </div>
  )
}}

export default App
""",
        ))

        # src/App.css
        files.append(FileSpec(
            relative_path="src/App.css",
            content="""\
.App {
  text-align: center;
  padding: 2rem;
}
""",
        ))

        # tsconfig.json (TypeScript only)
        if is_ts:
            files.append(FileSpec(
                relative_path="tsconfig.json",
                content="""\
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
""",
            ))

        # .gitignore
        files.append(FileSpec(
            relative_path=".gitignore",
            content="""\
node_modules/
dist/
dist-ssr/
*.local
.env
.env.local
""",
        ))

        # README.md
        files.append(FileSpec(
            relative_path="README.md",
            content=f"""\
# {project_name} — Frontend

React + Vite ({language.value}) frontend.

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```
""",
        ))

        return files

    def readme_snippet(self, language: Language) -> str:
        return f"""\
### Frontend (React + Vite — {language.value})

- Source lives in `frontend/src/`
- Run `npm run dev` from `frontend/` to start the dev server (default port 5173)
- Components go in `frontend/src/components/`
- Always run `npm run build` before committing to catch type/lint errors
"""

    def dockerfile_content(self, language: Language, project_name: str) -> str:
        return """\
# Stage 1: build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
