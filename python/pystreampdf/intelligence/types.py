"""
Intelligence analysis result types.

Shared data structures for all technical content analyzers (YAML, JSON, Code, Logs).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CorrectionSuggestion:
    """A suggested correction for corrupted or invalid content."""
    original: str
    corrected: str
    confidence: float  # 0.0-1.0
    description: str


@dataclass
class IntelligenceResult:
    """Result of analyzing technical content."""
    content_type: str  # "yaml", "json", "python", "shell", "syslog", etc.
    is_valid: bool
    confidence: float  # 0.0-1.0
    issues: list[str] = field(default_factory=list)
    corrections: list[CorrectionSuggestion] = field(default_factory=list)
    corrected_text: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")
