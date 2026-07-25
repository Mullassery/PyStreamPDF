"""
Composite confidence scoring and recommendation engine.

Combines text, table, and layout validation into a single confidence score
and provides actionable recommendations for OCR output quality.
"""

from typing import List, Optional, Tuple

from .layout import LayoutValidator
from .table import OcrTable, TableValidator
from .text import TextValidator
from .types import PageConfidenceScore, Recommendation


class ConfidenceScorer:
    """Scores OCR output quality across multiple dimensions."""

    def __init__(
        self,
        text_weight: float = 0.5,
        table_weight: float = 0.3,
        layout_weight: float = 0.2
    ):
        """
        Initialize confidence scorer.

        Args:
            text_weight: Weight for text quality score (default 0.5)
            table_weight: Weight for table structure score (default 0.3)
            layout_weight: Weight for layout hierarchy score (default 0.2)
        """
        self.text_weight = text_weight
        self.table_weight = table_weight
        self.layout_weight = layout_weight

        # Normalize weights
        total = text_weight + table_weight + layout_weight
        self.text_weight /= total
        self.table_weight /= total
        self.layout_weight /= total

        self._text_validator = TextValidator()
        self._table_validator = TableValidator()
        self._layout_validator = LayoutValidator()

    def score(
        self,
        text: str,
        tables: Optional[List[OcrTable]] = None,
        headings: Optional[List[Tuple[str, int]]] = None,
        ocr_confidence: Optional[float] = None
    ) -> PageConfidenceScore:
        """
        Score OCR output quality.

        Args:
            text: Extracted text to validate
            tables: Optional list of extracted tables to validate
            headings: Optional list of (heading_text, level) tuples to validate
            ocr_confidence: Optional base OCR provider confidence (0.0-1.0)

        Returns:
            PageConfidenceScore with component scores and letter grade
        """
        # Validate text
        text_result = self._text_validator.validate(text)
        text_score = text_result.confidence

        # Validate tables (if provided)
        if tables:
            table_scores = [
                self._table_validator.validate(table).confidence
                for table in tables
            ]
            table_score = sum(table_scores) / len(table_scores) if table_scores else 1.0
        else:
            table_score = 1.0  # No tables = perfect table score

        # Validate layout (if provided)
        if headings:
            layout_result = self._layout_validator.validate(headings)
            layout_score = layout_result.confidence
        else:
            layout_score = 1.0  # No headings = perfect layout score

        # Calculate weighted overall score
        overall_score = (
            self.text_weight * text_score +
            self.table_weight * table_score +
            self.layout_weight * layout_score
        )

        # Factor in OCR provider confidence if provided
        if ocr_confidence is not None:
            overall_score *= ocr_confidence

        # Clamp to [0.0, 1.0]
        overall_score = max(0.0, min(1.0, overall_score))

        # Assign letter grade
        grade = self._grade(overall_score)

        return PageConfidenceScore(
            overall=overall_score,
            text=text_score,
            tables=table_score,
            layout=layout_score,
            grade=grade
        )

    def recommend(
        self,
        score: PageConfidenceScore,
        current_provider: Optional[str] = None
    ) -> Recommendation:
        """
        Recommend action based on confidence score.

        Args:
            score: PageConfidenceScore from score()
            current_provider: Name of provider that generated this (for context)

        Returns:
            Recommendation with action and reasoning
        """
        if score.overall >= 0.85:
            return Recommendation(
                action="accept",
                reason=f"Confidence score {score.overall:.1%} meets quality threshold (>85%)",
                confidence=score.overall
            )

        if score.overall >= 0.60:
            return Recommendation(
                action="review",
                reason=f"Confidence score {score.overall:.1%} is acceptable but below optimal. Review before use.",
                confidence=min(1.0, score.overall + 0.1)
            )

        # Overall < 0.60: recommend re-run
        suggested_provider = self._suggest_provider(score, current_provider)

        return Recommendation(
            action="re_run",
            reason=f"Confidence score {score.overall:.1%} is below acceptable threshold (<60%). Recommended to re-extract with {suggested_provider}.",
            suggested_provider=suggested_provider,
            confidence=0.8
        )

    def _suggest_provider(self, score: PageConfidenceScore, current: Optional[str]) -> str:
        """Suggest which OCR provider to use based on failure mode."""
        # Determine which dimension is weakest
        weakest_score = min(score.text, score.tables, score.layout)

        if score.text == weakest_score and score.text < 0.6:
            # Text quality issues → use high-quality text OCR
            return "unlimited_ocr"
        elif score.tables == weakest_score and score.tables < 0.6:
            # Table issues → use table-optimized OCR
            return "mistral_ocr"
        else:
            # Layout or overall issues → use general-purpose OCR
            return "deepseek_ocr"

    @staticmethod
    def _grade(score: float) -> str:
        """Assign letter grade based on confidence score."""
        if score > 0.9:
            return "A"
        elif score > 0.75:
            return "B"
        elif score > 0.6:
            return "C"
        elif score > 0.45:
            return "D"
        else:
            return "F"
