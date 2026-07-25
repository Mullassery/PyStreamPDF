"""
Document layout validation for heading structure.

Detects heading hierarchy issues, empty headings, and structural problems.
"""

from typing import List, Optional, Tuple

from .types import ValidationIssue, ValidationResult


class LayoutValidator:
    """Validates document layout and heading structure."""

    def __init__(self):
        """Initialize layout validator."""
        pass

    def validate(self, headings: List[Tuple[str, int]]) -> ValidationResult:
        """
        Validate heading structure.

        Args:
            headings: List of (heading_text, level) tuples where level is 1-4

        Returns:
            ValidationResult with detected issues and overall confidence
        """
        if not headings:
            return ValidationResult(status="valid", confidence=1.0)

        issues = []

        # Check hierarchy (level progressions)
        hierarchy_issues = self._check_hierarchy(headings)
        issues.extend(hierarchy_issues)

        # Check for empty headings
        empty_issues = self._check_empty_headings(headings)
        issues.extend(empty_issues)

        # Calculate confidence: 1.0 - (0.15 per issue)
        confidence = max(0.0, 1.0 - (len(issues) * 0.15))

        status = "valid" if not issues else "issues"
        return ValidationResult(status=status, confidence=confidence, issues=issues)

    def _check_hierarchy(self, headings: List[Tuple[str, int]]) -> List[ValidationIssue]:
        """Check heading level progression (no skips when going deeper like H1 → H3)."""
        issues = []

        if len(headings) < 2:
            return issues

        levels = [level for _, level in headings]

        for i in range(len(levels) - 1):
            current_level = levels[i]
            next_level = levels[i + 1]

            # Going deeper (next_level > current_level):
            # Only allow stepping down by one level (H1 → H2, H2 → H3, etc.)
            if next_level > current_level and next_level > current_level + 1:
                issues.append(
                    ValidationIssue(
                        type="hierarchy_jump",
                        severity="medium",
                        description=f"Heading level jumped from H{current_level} to H{next_level} (skipped H{current_level + 1})"
                    )
                )

        return issues

    def _check_empty_headings(self, headings: List[Tuple[str, int]]) -> List[ValidationIssue]:
        """Flag any empty or whitespace-only heading."""
        issues = []

        for idx, (text, level) in enumerate(headings):
            if not text.strip():
                issues.append(
                    ValidationIssue(
                        type="empty_heading",
                        severity="high",
                        description=f"Heading at position {idx} is empty (H{level})"
                    )
                )

        return issues

    def _check_duplicate_h1s(self, headings: List[Tuple[str, int]]) -> Optional[ValidationIssue]:
        """Check for H1s interspersed with lower-level headings (improper structure)."""
        h1_indices = [i for i, (_, level) in enumerate(headings) if level == 1]

        if len(h1_indices) <= 1:
            return None

        # Check if H1s are interspersed with other levels
        # Bad pattern: H1, H2/H3/H4, H1 (indicates improper nesting)
        # OK pattern: H1, H1, H2 (consecutive H1s followed by subsections)
        for i in range(len(h1_indices) - 1):
            curr_idx = h1_indices[i]
            next_idx = h1_indices[i + 1]

            # If H1s are NOT consecutive, check what's between them
            if next_idx - curr_idx > 1:
                # There are headings between these H1s
                # Check if they're lower levels (bad structure)
                between_levels = [level for _, level in headings[curr_idx + 1:next_idx]]
                if any(level > 1 for level in between_levels):
                    # Found interspersed H1s with lower levels in between
                    return ValidationIssue(
                        type="duplicate_h1s",
                        severity="medium",
                        description=f"Document has {len(h1_indices)} H1 headings interspersed with lower-level sections (improper structure)"
                    )

        return None
