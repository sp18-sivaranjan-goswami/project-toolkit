"""Tests for the React framework plugin."""

from __future__ import annotations

import json

from proj_toolkit.config import Language
from proj_toolkit.frameworks.frontend.react import ReactPlugin


def _files(lang: Language) -> dict:
    plugin = ReactPlugin()
    specs = plugin.generate_files(lang, "my-app")
    return {s.relative_path: s.content for s in specs}


class TestReactTypescript:
    def setup_method(self):
        self.files = _files(Language.TYPESCRIPT)

    def test_package_json_exists(self):
        assert "package.json" in self.files

    def test_package_json_valid(self):
        data = json.loads(self.files["package.json"])
        assert data["name"] == "my-app-frontend"
        assert "react" in data["dependencies"]
        assert "vite" in data["devDependencies"]

    def test_vite_config_ts(self):
        assert "vite.config.ts" in self.files

    def test_main_tsx(self):
        assert "src/main.tsx" in self.files

    def test_app_tsx(self):
        assert "src/App.tsx" in self.files

    def test_tsconfig_present(self):
        assert "tsconfig.json" in self.files
        data = json.loads(self.files["tsconfig.json"])
        assert data["compilerOptions"]["jsx"] == "react-jsx"

    def test_index_html_references_tsx(self):
        assert "main.tsx" in self.files["index.html"]

    def test_readme_exists(self):
        assert "README.md" in self.files


class TestReactJavascript:
    def setup_method(self):
        self.files = _files(Language.JAVASCRIPT)

    def test_vite_config_js(self):
        assert "vite.config.js" in self.files

    def test_main_jsx(self):
        assert "src/main.jsx" in self.files

    def test_app_jsx(self):
        assert "src/App.jsx" in self.files

    def test_no_tsconfig(self):
        assert "tsconfig.json" not in self.files

    def test_index_html_references_jsx(self):
        assert "main.jsx" in self.files["index.html"]


def test_readme_snippet_contains_vite():
    plugin = ReactPlugin()
    snippet = plugin.readme_snippet(Language.TYPESCRIPT)
    assert "vite" in snippet.lower() or "npm run dev" in snippet
