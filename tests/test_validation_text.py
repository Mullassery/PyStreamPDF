"""Tests for TextValidator."""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest
from pystreampdf.validation import TextValidator, ValidationIssue, ValidationResult


class TestValidationIssue:
    """Test ValidationIssue dataclass."""

    def test_issue_creation(self):
        """Create a validation issue."""
        issue = ValidationIssue(
            type="truncation",
            severity="high",
            description="Text is truncated"
        )
        assert issue.type == "truncation"
        assert issue.severity == "high"
        assert issue.confidence == 1.0

    def test_issue_severity_values(self):
        """Severity must be high, medium, or low."""
        ValidationIssue("test", "high", "desc")
        ValidationIssue("test", "medium", "desc")
        ValidationIssue("test", "low", "desc")

        with pytest.raises(ValueError):
            ValidationIssue("test", "critical", "desc")

    def test_issue_confidence_range(self):
        """Confidence must be 0.0-1.0."""
        ValidationIssue("test", "high", "desc", confidence=0.5)
        ValidationIssue("test", "high", "desc", confidence=0.0)
        ValidationIssue("test", "high", "desc", confidence=1.0)

        with pytest.raises(ValueError):
            ValidationIssue("test", "high", "desc", confidence=-0.1)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_result_creation(self):
        """Create a validation result."""
        result = ValidationResult(status="valid", confidence=0.95)
        assert result.status == "valid"
        assert result.confidence == 0.95
        assert result.issues == []

    def test_result_with_issues(self):
        """ValidationResult with issues."""
        issues = [
            ValidationIssue("truncation", "high", "Text truncated"),
            ValidationIssue("repetition", "medium", "Repeated text"),
        ]
        result = ValidationResult(status="issues", confidence=0.5, issues=issues)
        assert len(result.issues) == 2
        assert result.status == "issues"


class TestTextValidator:
    """Test TextValidator."""

    def test_validator_creation(self):
        """Create TextValidator."""
        validator = TextValidator()
        assert validator is not None

    def test_validate_clean_text(self):
        """Validate clean text returns valid status."""
        validator = TextValidator()
        result = validator.validate("Hello world. This is clean text.")

        assert result.status == "valid"
        assert result.confidence >= 0.8
        assert len(result.issues) == 0

    def test_validate_empty_text(self):
        """Empty text is valid."""
        validator = TextValidator()
        result = validator.validate("")
        assert result.status == "valid"
        assert result.confidence == 1.0

    def test_detect_truncation(self):
        """Detect truncated text (no terminal punctuation)."""
        validator = TextValidator()
        result = validator.validate("This sentence has no punctuation at the end")

        # Check for truncation issue
        assert any(issue.type == "truncation" for issue in result.issues)

    def test_detect_repetition(self):
        """Detect repeated n-grams."""
        validator = TextValidator()
        # Repeat a phrase multiple times
        text = "hello world " * 5
        result = validator.validate(text)

        assert result.status == "issues"
        assert any(issue.type == "repetition" for issue in result.issues)

    def test_detect_corrupted_chars(self):
        """Detect corrupted characters (U+FFFD)."""
        validator = TextValidator()
        text = "This text has a replacement char: � in the middle."
        result = validator.validate(text)

        assert any(issue.type == "corruption" for issue in result.issues)

    def test_detect_control_chars(self):
        """Detect control characters."""
        validator = TextValidator()
        text = "Text with control \x01 character."
        result = validator.validate(text)

        assert any(issue.type == "corruption" for issue in result.issues)

    def test_broken_line_sequence_hyphen(self):
        """Detect line ending with hyphen (OCR artifact)."""
        validator = TextValidator()
        text = "This is a word at the end of a line-\nnext line starts here."
        result = validator.validate(text)

        assert any(issue.type == "line_sequence" for issue in result.issues)

    def test_confidence_range(self):
        """Confidence score is 0.0-1.0."""
        validator = TextValidator()

        clean_result = validator.validate("Clean text.")
        assert 0.0 <= clean_result.confidence <= 1.0

        dirty_result = validator.validate("Text with repet " * 10)
        assert 0.0 <= dirty_result.confidence <= 1.0


class TestTextValidatorIntegration:
    """Integration tests for TextValidator."""

    def test_multi_issue_text(self):
        """Text with multiple issues lowers confidence."""
        validator = TextValidator()
        # Text with truncation, repetition, and corruption
        text = "hello world hello world hello world hello world Text with replacement char: � no period"

        result = validator.validate(text)

        assert result.status == "issues"
        # Multiple issues should lower confidence significantly
        assert result.confidence < 0.6

    def test_realistic_ocr_output(self):
        """Validate realistic OCR output."""
        validator = TextValidator()
        # Simulate OCR output with some errors
        text = """
        Chapter 1: Introduction

        This document provides an overview of the system.
        The system is designed for high performance.
        The system is optimized for efficiency.
        The system is scalable and robust.
        """

        result = validator.validate(text)

        # Should detect the repetition
        assert any(issue.type == "repetition" for issue in result.issues)
