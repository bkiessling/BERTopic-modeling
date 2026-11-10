"""Protect the pure domain layer from framework-specific imports."""

import ast
from pathlib import Path
import unittest


class ArchitectureTests(unittest.TestCase):
    def test_domain_modules_do_not_import_web_frameworks(self):
        root = Path(__file__).resolve().parents[2] / "server" / "services"
        for path in root.rglob("*.py"):
            with self.subTest(module=str(path.relative_to(root))):
                tree = ast.parse(path.read_text())
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module.split(".")[0])
                self.assertFalse(set(imports) & {"streamlit", "fastapi", "starlette"})
