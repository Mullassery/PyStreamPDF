"""
PyStreamPDF Validation Module

Quality gates for OCR output validation across text, tables, and layout dimensions.
Combines validation results into a confidence score with actionable recommendations.

Example:
    >>> from pystreampdf.validation import ConfidenceScorer, TextValidator
    >>> scorer = ConfidenceScorer()
    >>> score = scorer.score("Extracted text here")
    >>> print(f"Grade: {score.grade}, Confidence: {score.overall:.1%}")
    >>> recommendation = scorer.recommend(score)
    >>> print(f"Action: {recommendation.action}")
"""

from .layout import LayoutValidator
from .scorer import ConfidenceScorer
from .table import TableValidator
from .text import TextValidator
from .types import (
    OcrTable,
    PageConfidenceScore,
    Recommendation,
    TableValidationResult,
    ValidationIssue,
    ValidationResult,
)

__all__ = [
    "ConfidenceScorer",
    "LayoutValidator",
    "OcrTable",
    "PageConfidenceScore",
    "Recommendation",
    "TableValidationResult",
    "TableValidator",
    "TextValidator",
    "ValidationIssue",
    "ValidationResult",
]
