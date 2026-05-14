"""Tests for the Node/Express framework plugin."""

from __future__ import annotations

import json

from proj_toolkit.config import Language
from proj_toolkit.frameworks.backend.node import NodePlugin


def _files(lang: Language) -> dict:
    plugin = NodePlugin()
    specs = plugin.generate_files(lang, "my-app")
    return {s.relative_path: s.content for s in specs}


class TestNodeTypescript:
    def setup_method(self):
        self.files = _files(Language.TYPESCRIPT)

    def test_package_json_exists(self):
        assert "package.json" in self.files

    def test_package_json_valid(self):
        data = json.loads(self.files["package.json"])
        assert "express" in data["dependencies"]

    def test_index_ts_exists(self):
        assert "src/index.ts" in self.files

    def test_index_ts_has_health_endpoint(self):
        assert "/health" in self.files["src/index.ts"]

    def test_tsconfig_exists(self):
        assert "tsconfig.json" in self.files
        data = json.loads(self.files["tsconfig.json"])
        assert data["compilerOptions"]["strict"] is True

    def test_env_example_exists(self):
        assert ".env.example" in self.files

    def test_readme_exists(self):
        assert "README.md" in self.files


class TestNodeJavascript:
    def setup_method(self):
        self.files = _files(Language.JAVASCRIPT)

    def test_index_js_exists(self):
        assert "src/index.js" in self.files

    def test_index_js_has_health_endpoint(self):
        assert "/health" in self.files["src/index.js"]

    def test_no_tsconfig(self):
        assert "tsconfig.json" not in self.files

    def test_uses_require_not_import(self):
        content = self.files["src/index.js"]
        assert "require(" in content


def test_readme_snippet_mentions_health():
    plugin = NodePlugin()
    snippet = plugin.readme_snippet(Language.TYPESCRIPT)
    assert "/health" in snippet
