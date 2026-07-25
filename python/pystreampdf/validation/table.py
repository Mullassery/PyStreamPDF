"""
Table structure validation for OCR output.

Detects missing columns, broken cells, and inconsistent table structure.
"""

from collections import Counter
from typing import List, Optional

from .text import TextValidator
from .types import OcrTable, TableValidationResult, ValidationIssue


class TableValidator:
    """Validates OCR-extracted table structure."""

    def __init__(self, min_row_consistency: float = 0.7):
        """
        Initialize table validator.

        Args:
            min_row_consistency: Minimum fraction of rows that must have consistent column count
        """
        self.min_row_consistency = min_row_consistency
        self._text_validator = TextValidator()

    def validate(self, table: OcrTable) -> TableValidationResult:
        """
        Validate table structure.

        Args:
            table: OcrTable to validate

        Returns:
            TableValidationResult with detected issues and accuracy estimate
        """
        if not table.rows:
            return TableValidationResult(
                status="issues",
                confidence=0.0,
                estimated_accuracy=0.0,
                issues=[
                    ValidationIssue(
                        type="empty_table",
                        severity="high",
                        description="Table has no rows"
                    )
                ]
            )

        issues = []

        # Check column consistency
        col_issue = self._check_column_consistency(table.rows)
        if col_issue:
            issues.append(col_issue)

        # Check for empty cells
        empty_issue = self._check_empty_cells(table.rows)
        if empty_issue:
            issues.append(empty_issue)

        # Check for corrupted cells
        corrupted_issues = self._check_corrupted_cells(table.rows)
        issues.extend(corrupted_issues)

        # Estimate accuracy
        accuracy = self._estimate_accuracy(table.rows)

        # Calculate confidence
        confidence = max(0.0, accuracy - (len(issues) * 0.1))

        status = "valid" if not issues else "issues"
        return TableValidationResult(
            status=status,
            confidence=confidence,
            estimated_accuracy=accuracy,
            issues=issues
        )

    def _check_column_consistency(self, rows: List[List[str]]) -> Optional[ValidationIssue]:
        """Check if rows have consistent number of columns."""
        if not rows:
            return None

        col_counts = [len(row) for row in rows]
        mode_count = Counter(col_counts).most_common(1)[0][0]

        # Count rows that deviate from mode
        deviations = sum(1 for count in col_counts if count != mode_count)
        deviation_ratio = deviations / len(col_counts) if col_counts else 0

        # If >30% of rows deviate, flag as issue
        if deviation_ratio > 0.3:
            return ValidationIssue(
                type="column_inconsistency",
                severity="high",
                description=f"Table column count inconsistent: {deviations}/{len(rows)} rows deviate from expected {mode_count}"
            )

        return None

    def _check_empty_cells(self, rows: List[List[str]]) -> Optional[ValidationIssue]:
        """Check for excessive empty cells."""
        if not rows:
            return None

        total_cells = sum(len(row) for row in rows)
        if total_cells == 0:
            return None

        empty_count = sum(
            1 for row in rows for cell in row if not cell.strip()
        )
        empty_ratio = empty_count / total_cells

        # If >50% of cells are empty, flag as incomplete extraction
        if empty_ratio > 0.5:
            return ValidationIssue(
                type="empty_cells",
                severity="high",
                description=f"Table has {empty_ratio:.1%} empty cells (incomplete extraction)"
            )

        return None

    def _check_corrupted_cells(self, rows: List[List[str]]) -> List[ValidationIssue]:
        """Check cells for corrupted text."""
        issues = []

        for row_idx, row in enumerate(rows):
            for cell_idx, cell in enumerate(row):
                if not cell.strip():
                    continue

                # Use text validator to check cell content
                corrupted = self._text_validator._find_corrupted_chars(cell)
                if corrupted:
                    issues.append(
                        ValidationIssue(
                            type="corrupted_cell",
                            severity="medium",
                            description=f"Cell at row {row_idx}, col {cell_idx} contains corrupted characters"
                        )
                    )

        return issues

    def _estimate_accuracy(self, rows: List[List[str]]) -> float:
        """Estimate accuracy of cell extraction (0.0-1.0)."""
        if not rows:
            return 0.0

        total_cells = sum(len(row) for row in rows)
        if total_cells == 0:
            return 0.0

        # Count plausible cells: non-empty and printable
        plausible_count = 0
        for row in rows:
            for cell in row:
                if cell.strip():
                    # Check if cell contains mostly printable characters
                    non_printable = sum(1 for c in cell if ord(c) < 0x20 and c not in '\n\r\t')
                    if non_printable == 0:
                        plausible_count += 1

        return plausible_count / total_cells
