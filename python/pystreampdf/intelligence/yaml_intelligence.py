"""YAML content intelligence and correction."""

import re
import yaml
from typing import Dict, List

from .types import CorrectionSuggestion, IntelligenceResult


class YAMLAnalyzer:
    """Analyzes YAML content for validity and corrects OCR errors."""

    def __init__(self):
        self.ocr_fixes = {
            "costrnap": "costmap",
            "paramaeter": "parameter",
            "treue": "true",
            "talse": "false",
            "strnap": "snap",
            "controler": "controller",
            "plannar": "planner",
        }

    def analyze(self, text: str) -> IntelligenceResult:
        """Analyze YAML content."""
        if not text or not text.strip():
            return IntelligenceResult(content_type="yaml", is_valid=True, confidence=1.0)

        issues = []
        corrections = []
        corrected_text = None
        metadata = {}

        # Attempt to parse
        try:
            parsed = yaml.safe_load(text)
            is_valid = True
        except yaml.YAMLError as e:
            is_valid = False
            issues.append(f"YAML parse error: {str(e)}")

            # Attempt correction
            corrected_text, suggestions = self._attempt_correction(text)
            corrections.extend(suggestions)

            if corrected_text:
                try:
                    parsed = yaml.safe_load(corrected_text)
                    is_valid = True
                    issues.clear()
                except yaml.YAMLError:
                    parsed = None

        if parsed:
            # Extract metadata
            if isinstance(parsed, dict):
                metadata["key_count"] = len(parsed)
                metadata["root_keys"] = list(parsed.keys())
                metadata["has_nested"] = any(isinstance(v, (dict, list)) for v in parsed.values())
                metadata["has_lists"] = any(isinstance(v, list) for v in parsed.values())

        confidence = 1.0 if is_valid and not issues else max(0.0, 1.0 - (len(issues) * 0.2))

        return IntelligenceResult(
            content_type="yaml",
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            corrections=corrections,
            corrected_text=corrected_text,
            metadata=metadata
        )

    def _attempt_correction(self, text: str) -> tuple[str, List[CorrectionSuggestion]]:
        """Attempt to correct common OCR errors."""
        suggestions = []
        corrected = text

        # Fix known OCR typos
        for typo, correct in self.ocr_fixes.items():
            if typo in corrected:
                corrected = corrected.replace(typo, correct)
                suggestions.append(CorrectionSuggestion(
                    original=typo,
                    corrected=correct,
                    confidence=0.95,
                    description=f"Common OCR typo: {typo} → {correct}"
                ))

        # Fix indentation
        if "\t" in corrected and "  " in corrected:
            corrected = corrected.replace("\t", "  ")
            suggestions.append(CorrectionSuggestion(
                original="mixed tabs/spaces",
                corrected="spaces",
                confidence=0.9,
                description="Normalized mixed indentation to spaces"
            ))

        return corrected, suggestions
