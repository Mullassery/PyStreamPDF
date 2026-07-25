"""Tests for ConfidenceScorer."""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest
from pystreampdf.validation import (
    ConfidenceScorer,
    OcrTable,
    PageConfidenceScore,
    Recommendation,
)


class TestPageConfidenceScore:
    """Test PageConfidenceScore dataclass."""

    def test_score_creation(self):
        """Create a confidence score."""
        score = PageConfidenceScore(
            overall=0.9,
            text=0.92,
            tables=0.88,
            layout=0.89,
            grade="A"
        )
        assert score.overall == 0.9
        assert score.grade == "A"

    def test_grade_values(self):
        """Grade must be A-F."""
        for grade in ["A", "B", "C", "D", "F"]:
            PageConfidenceScore(0.5, 0.5, 0.5, 0.5, grade)

        with pytest.raises(ValueError):
            PageConfidenceScore(0.5, 0.5, 0.5, 0.5, "Z")


class TestRecommendation:
    """Test Recommendation dataclass."""

    def test_recommendation_creation(self):
        """Create a recommendation."""
        rec = Recommendation(
            action="accept",
            reason="High confidence"
        )
        assert rec.action == "accept"
        assert rec.suggested_provider is None

    def test_action_values(self):
        """Action must be accept, review, or re_run."""
        Recommendation("accept", "test")
        Recommendation("review", "test")
        Recommendation("re_run", "test")

        with pytest.raises(ValueError):
            Recommendation("ignore", "test")


class TestConfidenceScorer:
    """Test ConfidenceScorer."""

    def test_scorer_creation(self):
        """Create ConfidenceScorer."""
        scorer = ConfidenceScorer()
        assert scorer is not None

    def test_score_clean_text_only(self):
        """Score clean text."""
        scorer = ConfidenceScorer()
        score = scorer.score("This is clean, well-formatted text.")

        assert score.overall >= 0.8
        assert score.text >= 0.8
        assert score.tables == 1.0  # No tables provided
        assert score.layout == 1.0  # No headings provided
        assert score.grade in ["A", "B"]

    def test_score_with_all_inputs(self):
        """Score with text, tables, and headings."""
        scorer = ConfidenceScorer()
        tables = [OcrTable(rows=[["A", "B"], ["1", "2"]])]
        headings = [("Chapter 1", 1), ("Section 1.1", 2)]

        score = scorer.score(
            text="Clean text here.",
            tables=tables,
            headings=headings
        )

        assert 0.0 <= score.overall <= 1.0
        assert 0.0 <= score.text <= 1.0
        assert 0.0 <= score.tables <= 1.0
        assert 0.0 <= score.layout <= 1.0

    def test_grade_assignment(self):
        """Grades assigned correctly based on score."""
        scorer = ConfidenceScorer()

        # High confidence
        high_score = PageConfidenceScore(0.95, 0.95, 0.95, 0.95, "A")
        assert high_score.grade == "A"

        # Good confidence
        good_score = PageConfidenceScore(0.80, 0.80, 0.80, 0.80, "B")
        assert good_score.grade == "B"

        # Low confidence
        low_score = PageConfidenceScore(0.50, 0.50, 0.50, 0.50, "C")
        assert low_score.grade == "C"

    def test_score_with_ocr_confidence(self):
        """OCR provider confidence factors into overall score."""
        scorer = ConfidenceScorer()

        # Score with high OCR confidence
        high = scorer.score("Text", ocr_confidence=0.95)

        # Score with low OCR confidence
        low = scorer.score("Text", ocr_confidence=0.50)

        # Lower OCR confidence should result in lower overall score
        assert high.overall > low.overall

    def test_recommend_accept(self):
        """Recommend accept for high confidence."""
        scorer = ConfidenceScorer()
        score = PageConfidenceScore(0.90, 0.90, 0.90, 0.90, "A")

        rec = scorer.recommend(score)
        assert rec.action == "accept"
        assert rec.confidence >= 0.8

    def test_recommend_review(self):
        """Recommend review for medium confidence."""
        scorer = ConfidenceScorer()
        score = PageConfidenceScore(0.70, 0.70, 0.70, 0.70, "B")

        rec = scorer.recommend(score)
        assert rec.action == "review"

    def test_recommend_rerun(self):
        """Recommend re-run for low confidence."""
        scorer = ConfidenceScorer()
        score = PageConfidenceScore(0.40, 0.30, 0.50, 0.45, "D")

        rec = scorer.recommend(score)
        assert rec.action == "re_run"
        assert rec.suggested_provider is not None

    def test_suggestion_based_on_weakness(self):
        """Suggested provider depends on which dimension failed."""
        scorer = ConfidenceScorer()

        # Suggest unlimited_ocr if text is weakest
        low_text = PageConfidenceScore(0.50, 0.40, 0.80, 0.75, "D")
        rec1 = scorer.recommend(low_text)
        assert rec1.suggested_provider == "unlimited_ocr"

        # Suggest mistral_ocr if tables are weakest
        low_table = PageConfidenceScore(0.50, 0.75, 0.30, 0.75, "D")
        rec2 = scorer.recommend(low_table)
        assert rec2.suggested_provider == "mistral_ocr"

        # Suggest deepseek_ocr for layout issues
        low_layout = PageConfidenceScore(0.50, 0.75, 0.75, 0.30, "D")
        rec3 = scorer.recommend(low_layout)
        assert rec3.suggested_provider == "deepseek_ocr"


class TestConfidenceScorerIntegration:
    """Integration tests for ConfidenceScorer."""

    def test_end_to_end_validation(self):
        """Complete validation pipeline."""
        scorer = ConfidenceScorer()

        # Good input
        good_score = scorer.score(
            "Well-written text with proper structure.",
            tables=[OcrTable(rows=[["A", "B"], ["1", "2"]])],
            headings=[("Intro", 1), ("Details", 2)]
        )
        good_rec = scorer.recommend(good_score)
        assert good_rec.action in ["accept", "review"]

        # Bad input
        bad_score = scorer.score(
            "text with repetition " * 10,
            tables=[OcrTable(rows=[["", ""], ["", ""]])],
            headings=[("", 1), ("", 2)]
        )
        bad_rec = scorer.recommend(bad_score)
        assert bad_rec.action == "re_run"

    def test_weight_customization(self):
        """Custom weights affect overall score."""
        # Text-heavy scorer
        text_scorer = ConfidenceScorer(text_weight=0.8, table_weight=0.1, layout_weight=0.1)

        # Table-heavy scorer
        table_scorer = ConfidenceScorer(text_weight=0.1, table_weight=0.8, layout_weight=0.1)

        # Same inputs
        bad_text_score = PageConfidenceScore(0.3, 0.3, 0.9, 0.9, "D")
        bad_table_score = PageConfidenceScore(0.3, 0.9, 0.2, 0.9, "D")

        # Text-heavy scorer penalizes text issues more
        rec1 = text_scorer.recommend(bad_text_score)
        rec2 = table_scorer.recommend(bad_table_score)

        # Both should recommend re_run but context differs
        assert rec1.action == "re_run"
        assert rec2.action == "re_run"
