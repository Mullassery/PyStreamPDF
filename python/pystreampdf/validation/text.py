"""
Text quality validation for OCR output.

Detects truncation, repetition, character corruption, and broken line sequences.
"""

import re
from typing import List

from .types import ValidationIssue, ValidationResult


class TextValidator:
    """Validates OCR-extracted text quality."""

    def __init__(self, repetition_window: int = 5):
        """
        Initialize text validator.

        Args:
            repetition_window: Window size for repetition detection (n-grams)
        """
        self.repetition_window = repetition_window

    def validate(self, text: str) -> ValidationResult:
        """
        Validate text quality.

        Args:
            text: Extracted text to validate

        Returns:
            ValidationResult with detected issues and overall confidence
        """
        if not text or not text.strip():
            return ValidationResult(status="valid", confidence=1.0)

        issues = []

        # Check truncation
        if self._has_truncation(text):
            issues.append(
                ValidationIssue(
                    type="truncation",
                    severity="high",
                    description="Text appears truncated at end (incomplete sentence)"
                )
            )

        # Check repetition
        if self._has_repetition(text):
            issues.append(
                ValidationIssue(
                    type="repetition",
                    severity="medium",
                    description="Significant text repetition detected"
                )
            )

        # Check corrupted characters
        corrupted = self._find_corrupted_chars(text)
        if corrupted:
            issues.append(
                ValidationIssue(
                    type="corruption",
                    severity="high",
                    description=f"Found {len(corrupted)} corrupted/control characters"
                )
            )

        # Check broken line sequences
        if self._has_broken_sequence(text):
            issues.append(
                ValidationIssue(
                    type="line_sequence",
                    severity="medium",
                    description="Line reading order or continuity appears broken"
                )
            )

        # Calculate overall confidence: 1.0 - (0.25 per issue), min 0.0
        confidence = max(0.0, 1.0 - (len(issues) * 0.25))

        status = "valid" if not issues else "issues"
        return ValidationResult(status=status, confidence=confidence, issues=issues)

    def _has_truncation(self, text: str) -> bool:
        """Detect if text is truncated (incomplete final sentence)."""
        lines = text.strip().split("\n")
        if not lines:
            return False

        last_line = lines[-1].strip()
        if not last_line or len(last_line) < 5:
            return False

        # Check if last line ends with terminal punctuation
        terminal_chars = {'.', '!', '?', '…', '。'}
        if last_line[-1] in terminal_chars:
            return False

        # Flag as truncated if:
        # 1. Ends without punctuation
        # 2. Contains at least one complete word
        words = last_line.split()
        if len(words) > 0 and len(words[-1]) > 2:
            # Looks like an incomplete sentence (no ending punctuation)
            return True

        return False

    def _has_repetition(self, text: str) -> bool:
        """Detect repeated words or phrases (OCR corruption pattern)."""
        words = text.split()
        if len(words) < 10:  # Need reasonable text length
            return False

        # Simple approach: check for repeated individual words
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if word_lower and len(word_lower) > 2:  # Ignore short words like "the", "a"
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # If any word appears more than 3 times in relatively short text, it's likely repetition
        for word, count in word_freq.items():
            if count >= 4:  # 4+ occurrences = repetition
                return True

        return False

    def _find_corrupted_chars(self, text: str) -> List[str]:
        """Find corrupted/control characters in text."""
        corrupted = []

        for char in text:
            # Check for replacement character (U+FFFD)
            if char == '�':
                corrupted.append(char)
            # Check for control characters (except common ones like \n, \r, \t)
            elif ord(char) < 0x20 and char not in '\n\r\t':
                corrupted.append(char)
            # Check for other suspicious Unicode ranges
            elif ord(char) in range(0x7F, 0x9F):
                corrupted.append(char)

        return corrupted

    def _has_broken_sequence(self, text: str) -> bool:
        """Detect broken line sequences or OCR artifacts."""
        lines = text.split("\n")

        for line in lines:
            if not line.strip():
                continue

            # Check if line ends with hyphen (OCR line-break artifact)
            if line.rstrip().endswith("-"):
                return True

            # Check if line starts with lowercase after newline
            # (suggests line break in middle of word)
            if line[0].islower() and len(line) > 1:
                # Allow if it's a proper lowercase start (e.g., "eBay")
                if len(lines) > 1 and lines.index(line) > 0:
                    prev_line = lines[lines.index(line) - 1].strip()
                    if prev_line and prev_line[-1].isalpha():
                        return True  # Likely word split across lines

        return False
