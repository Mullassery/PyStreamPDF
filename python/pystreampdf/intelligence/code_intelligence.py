"""Source code intelligence and validation."""

import ast
import re
from typing import Dict, List, Optional, Set

from .types import IntelligenceResult


class CodeAnalyzer:
    """Analyzes source code for language, syntax, and structure."""

    LANGUAGE_KEYWORDS = {
        "python": {"def", "class", "import", "from", "if", "for", "while", "try", "except"},
        "rust": {"fn", "struct", "impl", "use", "pub", "let", "mut", "match", "unsafe"},
        "cpp": {"include", "class", "void", "int", "return", "namespace", "template"},
        "javascript": {"function", "const", "let", "import", "export", "async", "await"},
        "shell": {"if", "then", "else", "do", "done", "case", "esac", "for"},
    }

    def analyze(self, text: str) -> IntelligenceResult:
        """Analyze source code."""
        if not text or not text.strip():
            return IntelligenceResult(content_type="unknown", is_valid=True, confidence=0.0)

        language = self._detect_language(text)
        issues = []
        metadata = {"language": language, "line_count": len(text.split("\n"))}

        if language == "python":
            issues, python_meta = self._validate_python(text)
            metadata.update(python_meta)
        else:
            # Heuristic checks for other languages
            if not self._check_brackets_balanced(text):
                issues.append("Unbalanced brackets")

        is_valid = len(issues) == 0
        confidence = 1.0 if is_valid else max(0.0, 1.0 - (len(issues) * 0.25))

        return IntelligenceResult(
            content_type=language,
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            metadata=metadata
        )

    def _detect_language(self, text: str) -> str:
        """Detect programming language."""
        lines = text.split("\n")

        # Check shebang
        if lines and lines[0].startswith("#!"):
            if "python" in lines[0]:
                return "python"
            if "bash" in lines[0] or "sh" in lines[0]:
                return "shell"

        # Check for language-specific patterns
        if "fn main()" in text or "use std::" in text:
            return "rust"
        if "#include <" in text or "namespace " in text:
            return "cpp"
        if "import React" in text or "export default" in text:
            return "javascript"

        # Keyword frequency scoring
        scores = {}
        for lang, keywords in self.LANGUAGE_KEYWORDS.items():
            score = sum(1 for kw in keywords if re.search(rf"\b{kw}\b", text))
            if score > 0:
                scores[lang] = score

        if scores:
            return max(scores, key=scores.get)

        return "unknown"

    def _validate_python(self, text: str) -> tuple[List[str], Dict]:
        """Validate Python code."""
        issues = []
        metadata = {}

        # Try to parse
        try:
            tree = ast.parse(text)
            # Extract structure
            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            imports = []
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    imports.extend([alias.name for alias in n.names])
                elif isinstance(n, ast.ImportFrom):
                    imports.append(n.module or "")

            metadata["function_names"] = functions
            metadata["class_names"] = classes
            metadata["import_names"] = [i for i in imports if i]

        except SyntaxError as e:
            issues.append(f"Syntax error at line {e.lineno}: {e.msg}")

        # Check indentation consistency
        if "\t" in text and "    " in text:
            issues.append("Mixed tabs and spaces in indentation")

        return issues, metadata

    def _check_brackets_balanced(self, text: str) -> bool:
        """Check if brackets are balanced."""
        stack = []
        pairs = {"(": ")", "[": "]", "{": "}"}
        in_string = False
        string_char = None

        for char in text:
            if char in ('"', "'") and (not in_string or string_char == char):
                in_string = not in_string
                string_char = char if in_string else None
                continue

            if in_string:
                continue

            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack or pairs[stack.pop()] != char:
                    return False

        return len(stack) == 0
