"""
PyStreamPDF Intelligence Module

Domain-specific understanding of technical content: YAML, JSON, source code, and logs.

Example:
    >>> from pystreampdf.intelligence import CodeAnalyzer, JSONAnalyzer
    >>> code = CodeAnalyzer()
    >>> result = code.analyze("def main(): pass")
    >>> print(f"Language: {result.metadata['language']}")
"""

from .code_intelligence import CodeAnalyzer
from .json_intelligence import JSONAnalyzer
from .log_intelligence import LogAnalyzer
from .sql_intelligence import SQLAnalyzer
from .types import CorrectionSuggestion, IntelligenceResult
from .yaml_intelligence import YAMLAnalyzer

__all__ = [
    "YAMLAnalyzer",
    "JSONAnalyzer",
    "CodeAnalyzer",
    "LogAnalyzer",
    "SQLAnalyzer",
    "IntelligenceResult",
    "CorrectionSuggestion",
]
