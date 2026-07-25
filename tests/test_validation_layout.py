"""Tests for LayoutValidator."""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest
from pystreampdf.validation import LayoutValidator


class TestLayoutValidator:
    """Test LayoutValidator."""

    def test_validator_creation(self):
        """Create LayoutValidator."""
        validator = LayoutValidator()
        assert validator is not None

    def test_validate_valid_hierarchy(self):
        """Valid heading hierarchy H1 -> H2 -> H3."""
        validator = LayoutValidator()
        headings = [
            ("Chapter 1", 1),
            ("Section 1.1", 2),
            ("Subsection 1.1.1", 3),
            ("Chapter 2", 1),
            ("Section 2.1", 2),
        ]

        result = validator.validate(headings)
        assert result.status == "valid"
        assert len(result.issues) == 0
        assert result.confidence >= 0.8

    def test_validate_empty_headings(self):
        """Empty heading list is valid."""
        validator = LayoutValidator()
        result = validator.validate([])
        assert result.status == "valid"

    def test_detect_hierarchy_jump(self):
        """Detect level jump H1 -> H3 (skip H2)."""
        validator = LayoutValidator()
        headings = [
            ("Chapter", 1),
            ("Subsubsection", 3),  # Jump from 1 to 3
        ]

        result = validator.validate(headings)
        assert result.status == "issues"
        assert any(i.type == "hierarchy_jump" for i in result.issues)

    def test_detect_empty_heading(self):
        """Detect empty heading text."""
        validator = LayoutValidator()
        headings = [
            ("Chapter 1", 1),
            ("", 2),  # Empty heading
            ("Section", 2),
        ]

        result = validator.validate(headings)
        assert any(i.type == "empty_heading" for i in result.issues)

    def test_multiple_h1s_are_valid(self):
        """Multiple H1s with proper subsection structure are valid."""
        validator = LayoutValidator()
        headings = [
            ("Document Title", 1),
            ("Section 1", 2),
            ("Main Title", 1),  # Second H1 is valid (new chapter)
            ("Section 2", 2),
        ]

        result = validator.validate(headings)
        # Multiple H1s with proper structure should be valid
        assert result.status == "valid"
        assert not any(i.type == "duplicate_h1s" for i in result.issues)

    def test_consecutive_h1s_ok(self):
        """Consecutive H1s without section headers are OK."""
        validator = LayoutValidator()
        headings = [
            ("First Title", 1),
            ("Second Title", 1),
            ("Section 1", 2),
        ]

        result = validator.validate(headings)
        # Should not flag duplicate_h1s if consecutive
        assert not any(i.type == "duplicate_h1s" for i in result.issues)

    def test_confidence_score(self):
        """Confidence decreases with issues."""
        validator = LayoutValidator()

        clean = [("Chapter", 1), ("Section", 2)]
        clean_result = validator.validate(clean)

        dirty = [("Chapter", 1), ("", 2), ("Sub", 3)]
        dirty_result = validator.validate(dirty)

        assert clean_result.confidence > dirty_result.confidence


class TestLayoutValidatorIntegration:
    """Integration tests for LayoutValidator."""

    def test_realistic_document_structure(self):
        """Validate realistic document heading structure."""
        validator = LayoutValidator()
        headings = [
            ("Introduction", 1),
            ("Background", 2),
            ("Motivation", 3),
            ("Related Work", 2),
            ("Methodology", 1),
            ("Approach", 2),
            ("Implementation", 2),
            ("Results", 1),
            ("Analysis", 2),
            ("Conclusion", 1),
        ]

        result = validator.validate(headings)
        # Well-structured document should have no issues
        assert result.status == "valid"
        assert result.confidence >= 0.8
