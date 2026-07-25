"""Tests for code intelligence analyzer."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
from pystreampdf.intelligence import CodeAnalyzer


class TestCodeAnalyzerLanguageDetection(unittest.TestCase):
    """Language detection tests."""

    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_detect_python_shebang(self):
        text = "#!/usr/bin/env python\nprint('hello')"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("language"), "python")

    def test_detect_python_keywords(self):
        text = "def hello():\n    print('world')\n    return True"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("language"), "python")

    def test_detect_rust(self):
        text = "fn main() {\n    println!(\"Hello\");\n}"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("language"), "rust")

    def test_detect_cpp(self):
        text = "#include <iostream>\nint main() { return 0; }"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("language"), "cpp")

    def test_detect_javascript(self):
        text = "import React from 'react';\nexport default App;"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("language"), "javascript")

    def test_detect_shell(self):
        text = "#!/bin/bash\necho 'hello world'"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("language"), "shell")

    def test_unknown_language(self):
        text = "some random text"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("language"), "unknown")


class TestPythonValidation(unittest.TestCase):
    """Python-specific validation tests."""

    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_valid_python_simple(self):
        text = "def hello():\n    return 42"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.content_type, "python")

    def test_valid_python_with_class(self):
        text = """
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertIn("Calculator", result.metadata.get("class_names", []))

    def test_valid_python_with_imports(self):
        text = """
import os
from pathlib import Path
import json

def read_file(path):
    return open(path).read()
"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.metadata.get("import_names", [])) > 0)

    def test_invalid_python_syntax_error(self):
        text = "def broken():\n  if True\n    return 42"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.issues) > 0)

    def test_invalid_python_indentation_mixed(self):
        text = "def mixed():\n    x = 1\n\ty = 2"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Mixed tabs and spaces" in issue or "inconsistent use of tabs" in issue for issue in result.issues))

    def test_python_function_extraction(self):
        text = """
def func1():
    pass

def func2():
    pass

class MyClass:
    def method1(self):
        pass
"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        funcs = result.metadata.get("function_names", [])
        self.assertIn("func1", funcs)
        self.assertIn("func2", funcs)
        self.assertIn("method1", funcs)

    def test_python_class_extraction(self):
        text = """
class FirstClass:
    pass

class SecondClass:
    pass
"""
        result = self.analyzer.analyze(text)
        classes = result.metadata.get("class_names", [])
        self.assertIn("FirstClass", classes)
        self.assertIn("SecondClass", classes)

    def test_python_import_extraction(self):
        text = """
import os
import sys
from pathlib import Path
from typing import List, Dict
"""
        result = self.analyzer.analyze(text)
        imports = result.metadata.get("import_names", [])
        self.assertIn("os", imports)
        self.assertIn("sys", imports)
        self.assertIn("pathlib", imports)
        self.assertIn("typing", imports)

    def test_python_line_count(self):
        text = "def f():\n    pass\n\ndef g():\n    pass"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("line_count"), 5)


class TestBracketBalancing(unittest.TestCase):
    """Bracket balancing tests."""

    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_balanced_brackets(self):
        text = "def check(): return [1, 2, 3]"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_unbalanced_parens(self):
        text = "if (a > b { return; }"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_unbalanced_brackets(self):
        text = "arr = [1, 2, 3"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_unbalanced_braces(self):
        text = "if true { console.log('test'); "
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_brackets_in_strings(self):
        text = 'x = "bracket: }"; y = {}'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)


class TestCodeAnalyzerMetadata(unittest.TestCase):
    """Metadata extraction tests."""

    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_content_type_matches_language(self):
        text = "def f():\n    pass"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.content_type, result.metadata.get("language"))

    def test_empty_code(self):
        result = self.analyzer.analyze("")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 0.0)

    def test_confidence_valid_code(self):
        text = "def f(): return 42"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 1.0)

    def test_confidence_invalid_code_degrades(self):
        text = "def broken(\n  if True:"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertLess(result.confidence, 0.85)


class TestComplexCodeScenarios(unittest.TestCase):
    """Complex real-world code scenarios."""

    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_python_async_code(self):
        text = """
async def fetch_data():
    import requests
    data = await get_from_api()
    return data
"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertIn(result.metadata.get("language"), ["python", "javascript"])

    def test_python_decorators(self):
        text = """
@app.route('/api/users')
@require_auth
def list_users():
    return []
"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_python_type_hints(self):
        text = """
def greet(name: str) -> str:
    return f"Hello, {name}"
"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_multiline_strings(self):
        text = '''
def multiline():
    """
    This is a docstring
    that spans multiple lines
    """
    return True
'''
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_lambda_expressions(self):
        text = "square = lambda x: x ** 2\nresult = map(square, [1, 2, 3])"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()
