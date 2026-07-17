"""Tests for enhanced PDF parsing and extraction."""

import pytest
from pystreampdf.extraction import (
    ReadingOrderCorrector,
    TableExtractor,
    SemanticChunker,
    MultimediaAnalyzer,
    CitationTracker,
    TextFragment,
    ElementType,
    ReadingOrder,
    ContentChunk,
    MultimediaElement,
    SourceLocation,
)


class TestReadingOrderCorrector:
    """Test reading order correction."""

    def test_analyze_correct_order(self):
        """Test analysis of correctly ordered text."""
        corrector = ReadingOrderCorrector()
        fragments = [
            TextFragment("Hello", 10, 100, 50, 20),
            TextFragment("world", 70, 100, 50, 20),
            TextFragment("This", 10, 130, 50, 20),
            TextFragment("is", 70, 130, 50, 20),
        ]
        order = corrector.analyze_fragments(fragments)
        assert order == ReadingOrder.CORRECT

    def test_analyze_needs_fixing(self):
        """Test detection of reading order issues."""
        corrector = ReadingOrderCorrector()
        fragments = [
            TextFragment("Hello", 10, 100, 50, 20),
            TextFragment("This", 10, 90, 50, 20),  # Out of order
            TextFragment("world", 70, 110, 50, 20),
            TextFragment("is", 70, 80, 50, 20),  # Out of order
        ]
        order = corrector.analyze_fragments(fragments)
        assert order in [ReadingOrder.NEEDS_FIXING, ReadingOrder.COMPLEX]

    def test_correct_order(self):
        """Test fragment reordering."""
        corrector = ReadingOrderCorrector()
        fragments = [
            TextFragment("world", 70, 100, 50, 20),
            TextFragment("Hello", 10, 100, 50, 20),
            TextFragment("is", 70, 130, 50, 20),
            TextFragment("This", 10, 130, 50, 20),
        ]
        corrected = corrector.correct_order(fragments)
        assert corrected[0].text == "Hello"
        assert corrected[1].text == "world"
        assert corrected[2].text == "This"
        assert corrected[3].text == "is"

    def test_merge_fragments(self):
        """Test fragment merging."""
        corrector = ReadingOrderCorrector()
        fragments = [
            TextFragment("Hello", 10, 100, 50, 20),
            TextFragment("world", 70, 100, 50, 20),
            TextFragment("This", 10, 130, 50, 20),
            TextFragment("is", 70, 130, 50, 20),
        ]
        merged = corrector.merge_fragments(corrector.correct_order(fragments))
        assert "Hello" in merged
        assert "world" in merged
        assert "This" in merged
        assert "is" in merged


class TestTableExtractor:
    """Test table extraction."""

    def test_detect_table_grid(self):
        """Test table grid detection."""
        extractor = TableExtractor()
        elements = [
            {"type": "line", "bbox": (10, 10, 10, 100)},  # Vertical
            {"type": "line", "bbox": (50, 10, 50, 100)},  # Vertical
            {"type": "line", "bbox": (10, 10, 100, 10)},  # Horizontal
            {"type": "line", "bbox": (10, 50, 100, 50)},  # Horizontal
        ]
        grid = extractor.detect_table_grid(elements)
        assert grid is not None
        col_x, row_y = grid
        assert len(col_x) == 2
        assert len(row_y) == 2

    def test_extract_table(self):
        """Test table extraction."""
        extractor = TableExtractor()
        grid = ([10, 50, 100], [10, 50, 100])
        text_elements = [
            {"position": (20, 20), "content": "Name"},
            {"position": (60, 20), "content": "Age"},
            {"position": (20, 60), "content": "Alice"},
            {"position": (60, 60), "content": "30"},
        ]
        table = extractor.extract_table(grid, text_elements)
        assert table.rows == 2
        assert table.cols == 2
        assert len(table.cells) == 4


class TestSemanticChunker:
    """Test semantic chunking."""

    def test_chunk_text(self):
        """Test text chunking."""
        chunker = SemanticChunker(target_chunk_size=100, target_tokens=50)
        content = "Para 1. " * 20 + "\n\n" + "Para 2. " * 20
        chunks = chunker.chunk_content(content, ElementType.TEXT, 1, 2)
        assert len(chunks) >= 1
        assert all(isinstance(c, ContentChunk) for c in chunks)

    def test_chunk_table_stays_whole(self):
        """Test that tables are not split."""
        chunker = SemanticChunker()
        table_content = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1 | Cell 2 |"
        chunks = chunker.chunk_content(table_content, ElementType.TABLE, 1, 1)
        assert len(chunks) == 1
        assert chunks[0].chunk_type == ElementType.TABLE

    def test_token_estimation(self):
        """Test token estimation."""
        chunker = SemanticChunker()
        content = "Hello world this is a test."
        chunks = chunker.chunk_content(content, ElementType.TEXT, 1, 1)
        assert chunks[0].estimated_tokens > 0


class TestMultimediaAnalyzer:
    """Test multimedia detection."""

    def test_detect_images(self):
        """Test image detection."""
        analyzer = MultimediaAnalyzer()
        elements = [
            {
                "type": "image",
                "page": 1,
                "bbox": (10, 20, 100, 150),
            },
        ]
        images = analyzer.detect_images(elements)
        assert len(images) == 1
        assert images[0].type == "image"

    def test_detect_charts(self):
        """Test chart detection."""
        analyzer = MultimediaAnalyzer()
        elements = [
            {
                "type": "chart",
                "page": 1,
                "bbox": (10, 20, 100, 150),
                "chart_type": "bar chart",
            },
        ]
        charts = analyzer.detect_images(elements)
        assert len(charts) == 1
        assert charts[0].type == "chart"
        assert charts[0].description == "bar chart"

    def test_alt_text_generation(self):
        """Test alternative text generation."""
        analyzer = MultimediaAnalyzer()
        image = MultimediaElement(
            type="chart",
            page=1,
            x=10,
            y=20,
            width=90,
            height=130,
            description="bar chart",
            confidence=0.8,
        )
        alt_text = analyzer.generate_alt_text(image)
        assert "page 1" in alt_text
        assert "bar chart" in alt_text


class TestCitationTracker:
    """Test citation and provenance tracking."""

    def test_add_citation(self):
        """Test adding citations."""
        tracker = CitationTracker()
        location = SourceLocation(
            page=1,
            bounding_box=(10, 10, 100, 50),
            text="Important finding",
            offset_start=0,
            offset_end=18,
        )
        tracker.add_citation("Important finding", location)
        assert "Important finding" in tracker.citations

    def test_get_source(self):
        """Test retrieving source."""
        tracker = CitationTracker()
        location = SourceLocation(
            page=1,
            bounding_box=(10, 10, 100, 50),
            text="Important finding",
            offset_start=0,
            offset_end=18,
        )
        tracker.add_citation("Important finding", location)
        found = tracker.get_source("Important finding")
        assert found is not None
        assert found.page == 1

    def test_verify_grounded(self):
        """Test hallucination verification."""
        tracker = CitationTracker()
        chunks = [
            ContentChunk(
                content="The sky is blue.",
                chunk_type=ElementType.TEXT,
                page_start=1,
                page_end=1,
            ),
        ]
        is_grounded = tracker.verify_hallucination("sky is blue", chunks)
        assert is_grounded

    def test_verify_hallucination(self):
        """Test hallucination detection."""
        tracker = CitationTracker()
        chunks = [
            ContentChunk(
                content="The sky is blue.",
                chunk_type=ElementType.TEXT,
                page_start=1,
                page_end=1,
            ),
        ]
        is_grounded = tracker.verify_hallucination("The sky is green", chunks)
        assert not is_grounded


class TestIntegration:
    """Integration tests for extraction pipeline."""

    def test_extraction_pipeline(self):
        """Test full extraction pipeline."""
        # Setup
        corrector = ReadingOrderCorrector()
        chunker = SemanticChunker()
        analyzer = MultimediaAnalyzer()
        tracker = CitationTracker()

        # Simulate extraction
        fragments = [
            TextFragment("Chapter 1", 10, 100, 100, 20, font_size=16, is_bold=True),
            TextFragment("This is", 10, 130, 50, 12),
            TextFragment("important content.", 70, 130, 100, 12),
        ]

        # Correct reading order
        corrected = corrector.correct_order(fragments)
        assert len(corrected) == 3

        # Merge into text
        text = corrector.merge_fragments(corrected)
        assert len(text) > 0

        # Create chunks
        chunks = chunker.chunk_content(text, ElementType.TEXT, 1, 1)
        assert len(chunks) > 0

        # Track citations
        for chunk in chunks:
            location = SourceLocation(
                page=chunk.page_start,
                bounding_box=(10, 100, 200, 150),
                text=chunk.content[:50],
                offset_start=0,
                offset_end=50,
            )
            tracker.add_citation(chunk.content, location)

        assert len(tracker.citations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
