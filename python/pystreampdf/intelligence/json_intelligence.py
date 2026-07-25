"""JSON content intelligence and recovery."""

import json
import re
from typing import Any, Dict, List, Optional

from .types import CorrectionSuggestion, IntelligenceResult


class JSONAnalyzer:
    """Analyzes JSON content and attempts to recover from common errors."""

    def analyze(self, text: str) -> IntelligenceResult:
        """Analyze JSON content."""
        if not text or not text.strip():
            return IntelligenceResult(content_type="json", is_valid=True, confidence=1.0)

        issues = []
        corrections = []
        corrected_text = None
        metadata = {}
        parsed = None

        # Try to parse
        try:
            parsed = json.loads(text)
            is_valid = True
        except json.JSONDecodeError as e:
            is_valid = False
            issues.append(f"JSON parse error at position {e.pos}: {e.msg}")

            # Attempt recovery
            corrected_text, suggestions = self._attempt_recovery(text)
            corrections.extend(suggestions)

            if corrected_text:
                try:
                    parsed = json.loads(corrected_text)
                    is_valid = True
                    issues.clear()
                except json.JSONDecodeError:
                    pass

        if parsed:
            metadata = self._extract_metadata(parsed)

        confidence = 1.0 if is_valid and not issues else max(0.0, 1.0 - (len(issues) * 0.2))

        return IntelligenceResult(
            content_type="json",
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            corrections=corrections,
            corrected_text=corrected_text,
            metadata=metadata
        )

    def _attempt_recovery(self, text: str) -> tuple[str, List[CorrectionSuggestion]]:
        """Attempt to recover from common JSON errors."""
        suggestions = []
        corrected = text.strip()

        # Fix trailing commas
        if ",}" in corrected or ",]" in corrected:
            orig = corrected
            corrected = re.sub(r",(\s*[}\]])", r"\1", corrected)
            if orig != corrected:
                suggestions.append(CorrectionSuggestion(
                    original=",}",
                    corrected="}",
                    confidence=0.95,
                    description="Removed trailing comma before closing brace"
                ))

        # Fix single quotes to double quotes (limited)
        if "'" in corrected and '"' in corrected:
            orig = corrected
            # Only fix in key positions
            corrected = re.sub(r"'([^']+)':", r'"\1":', corrected)
            if orig != corrected:
                suggestions.append(CorrectionSuggestion(
                    original="'key':",
                    corrected='"key":',
                    confidence=0.85,
                    description="Converted single-quoted keys to double-quoted"
                ))

        # Fix missing commas between objects
        if "}{" in corrected:
            corrected = corrected.replace("}{", "},{")
            suggestions.append(CorrectionSuggestion(
                original="}{",
                corrected="},{",
                confidence=0.9,
                description="Added missing comma between objects"
            ))

        return corrected, suggestions

    def _extract_metadata(self, obj: Any) -> Dict:
        """Extract metadata from parsed JSON."""
        metadata = {}

        if isinstance(obj, dict):
            metadata["top_level_type"] = "object"
            metadata["key_count"] = len(obj)
            metadata["inferred_purpose"] = self._infer_purpose(obj)
            metadata["nesting_depth"] = self._calculate_depth(obj)
        elif isinstance(obj, list):
            metadata["top_level_type"] = "array"
            metadata["element_count"] = len(obj)
            metadata["inferred_purpose"] = "data_array"
            if obj:
                metadata["nesting_depth"] = self._calculate_depth(obj[0])

        return metadata

    def _infer_purpose(self, obj: Dict) -> str:
        """Infer the purpose of a JSON object."""
        keys = set(obj.keys())

        if {"data", "result", "status"} & keys:
            return "api_response"
        if {"host", "port", "url", "version"} & keys:
            return "config"
        if {"error", "message", "code"} & keys:
            return "error_response"

        return "unknown"

    def _calculate_depth(self, obj: Any, depth: int = 0) -> int:
        """Calculate nesting depth."""
        if isinstance(obj, dict):
            if not obj:
                return depth
            return max(self._calculate_depth(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return depth
            return max(self._calculate_depth(v, depth + 1) for v in obj)
        return depth
