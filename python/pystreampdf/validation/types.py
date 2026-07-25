"""
Validation data types and result containers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationIssue:
    """A single validation issue found during analysis."""
    type: str               # e.g. "truncation", "repetition", "corruption", "hierarchy_jump"
    severity: str           # "high", "medium", or "low"
    description: str        # Human-readable description
    confidence: float = 1.0  # 0.0-1.0: confidence that this is a real issue

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")
        if self.severity not in ("high", "medium", "low"):
            raise ValueError(f"severity must be 'high', 'medium', or 'low', got {self.severity}")


@dataclass
class ValidationResult:
    """Result of validating a single text or structure."""
    status: str                                   # "valid" or "issues"
    confidence: float                             # 0.0-1.0: overall confidence in extraction quality
    issues: List[ValidationIssue] = field(default_factory=list)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")
        if self.status not in ("valid", "issues"):
            raise ValueError(f"status must be 'valid' or 'issues', got {self.status}")


@dataclass
class TableValidationResult:
    """Result of validating a table structure."""
    status: str                                   # "valid" or "issues"
    confidence: float                             # 0.0-1.0
    estimated_accuracy: float = 1.0               # 0.0-1.0: fraction of cells that are plausible
    issues: List[ValidationIssue] = field(default_factory=list)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")
        if not 0.0 <= self.estimated_accuracy <= 1.0:
            raise ValueError(f"estimated_accuracy must be 0.0-1.0, got {self.estimated_accuracy}")


@dataclass
class OcrTable:
    """Minimal OCR-extracted table structure."""
    rows: List[List[str]]                    # Row-major: list of rows, each row is list of cell strings
    page_number: Optional[int] = None
    header: Optional[List[str]] = None       # Optional header row


@dataclass
class PageConfidenceScore:
    """Composite confidence score for a page across multiple dimensions."""
    overall: float                           # 0.0-1.0: weighted combination
    text: float                              # 0.0-1.0: text quality score
    tables: float                            # 0.0-1.0: table structure score
    layout: float                            # 0.0-1.0: layout hierarchy score
    grade: str                               # "A", "B", "C", "D", or "F"

    def __post_init__(self):
        if not 0.0 <= self.overall <= 1.0:
            raise ValueError(f"overall must be 0.0-1.0, got {self.overall}")
        if not 0.0 <= self.text <= 1.0:
            raise ValueError(f"text must be 0.0-1.0, got {self.text}")
        if not 0.0 <= self.tables <= 1.0:
            raise ValueError(f"tables must be 0.0-1.0, got {self.tables}")
        if not 0.0 <= self.layout <= 1.0:
            raise ValueError(f"layout must be 0.0-1.0, got {self.layout}")
        if self.grade not in ("A", "B", "C", "D", "F"):
            raise ValueError(f"grade must be A-F, got {self.grade}")


@dataclass
class Recommendation:
    """Recommendation for how to handle validated content."""
    action: str                              # "accept", "review", or "re_run"
    reason: str                              # Human-readable reason
    suggested_provider: Optional[str] = None  # Provider to re-run with (e.g. "unlimited_ocr", "mistral_ocr")
    confidence: float = 1.0                  # 0.0-1.0: confidence in this recommendation

    def __post_init__(self):
        if self.action not in ("accept", "review", "re_run"):
            raise ValueError(f"action must be 'accept', 'review', or 're_run', got {self.action}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")
