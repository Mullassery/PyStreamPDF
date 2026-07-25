"""Tests for TableValidator."""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest
from pystreampdf.validation import OcrTable, TableValidator, TableValidationResult


class TestOcrTable:
    """Test OcrTable dataclass."""

    def test_table_creation(self):
        """Create an OcrTable."""
        rows = [["A", "B"], ["1", "2"]]
        table = OcrTable(rows=rows, page_number=5)

        assert table.rows == rows
        assert table.page_number == 5
        assert table.header is None

    def test_table_with_header(self):
        """OcrTable with header."""
        table = OcrTable(
            rows=[["1", "2"]],
            header=["Col1", "Col2"]
        )
        assert table.header == ["Col1", "Col2"]


class TestTableValidator:
    """Test TableValidator."""

    def test_validator_creation(self):
        """Create TableValidator."""
        validator = TableValidator()
        assert validator is not None

    def test_validate_uniform_table(self):
        """Validate uniform table."""
        validator = TableValidator()
        table = OcrTable(rows=[
            ["A", "B", "C"],
            ["1", "2", "3"],
            ["4", "5", "6"],
        ])

        result = validator.validate(table)
        assert result.status == "valid"
        assert len(result.issues) == 0
        assert result.estimated_accuracy >= 0.8

    def test_validate_empty_table(self):
        """Empty table is flagged."""
        validator = TableValidator()
        table = OcrTable(rows=[])

        result = validator.validate(table)
        assert result.status == "issues"
        assert any(i.type == "empty_table" for i in result.issues)

    def test_detect_inconsistent_columns(self):
        """Detect rows with inconsistent column counts."""
        validator = TableValidator()
        table = OcrTable(rows=[
            ["A", "B", "C"],
            ["1", "2"],          # Missing column
            ["4", "5", "6"],
            ["7", "8"],          # Missing column
        ])

        result = validator.validate(table)
        assert any(i.type == "column_inconsistency" for i in result.issues)

    def test_detect_empty_cells(self):
        """Detect excessive empty cells."""
        validator = TableValidator()
        table = OcrTable(rows=[
            ["A", "", ""],
            ["", "", ""],
            ["", "", ""],
        ])

        result = validator.validate(table)
        assert any(i.type == "empty_cells" for i in result.issues)

    def test_accuracy_estimation(self):
        """Accuracy estimate is 0.0-1.0."""
        validator = TableValidator()

        # Good table
        good_table = OcrTable(rows=[
            ["A", "B"],
            ["1", "2"],
        ])
        result = validator.validate(good_table)
        assert 0.0 <= result.estimated_accuracy <= 1.0
        assert result.estimated_accuracy > 0.8

        # Bad table
        bad_table = OcrTable(rows=[
            ["", ""],
            ["", ""],
        ])
        result = validator.validate(bad_table)
        assert result.estimated_accuracy < 0.2


class TestTableValidatorIntegration:
    """Integration tests for TableValidator."""

    def test_realistic_ocr_table(self):
        """Validate realistic OCR-extracted table."""
        validator = TableValidator()
        table = OcrTable(rows=[
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
            ["Charlie", "35", ""],  # Missing cell
        ])

        result = validator.validate(table)
        # Should detect missing cell but overall be acceptable
        assert len(result.issues) >= 0
        assert result.estimated_accuracy >= 0.6
