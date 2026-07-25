"""Log file intelligence and error detection."""

import re
from typing import Dict, List, Optional, Tuple

from .types import IntelligenceResult


class LogAnalyzer:
    """Analyzes log file content and detects errors."""

    LOG_FORMATS = {
        "syslog": r"^\w{3}\s+\d+ \d{2}:\d{2}:\d{2}",
        "journalctl": r"^\w{3} \d+ \d{2}:\d{2}:\d{2}\.\d+",
        "kernel": r"^\[\s*\d+\.\d+\]",
        "docker": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        "k8s": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
    }

    CRASH_PATTERNS = {"segfault", "segmentation", "oom", "killed", "panic", "backtrace", "core dump"}
    RESOURCE_PATTERNS = {"no space left", "out of memory", "enomem", "too many open files"}

    def analyze(self, text: str) -> IntelligenceResult:
        """Analyze log content."""
        if not text or not text.strip():
            return IntelligenceResult(content_type="unknown", is_valid=True, confidence=0.0)

        lines = text.strip().split("\n")
        log_format = self._detect_format(text)
        issues = []
        metadata = {"log_format": log_format, "entry_count": len(lines)}

        # Parse entries
        errors = []
        warnings = []
        crashes = []
        resource_issues = []

        for line in lines:
            if not line.strip():
                continue

            level = self._extract_level(line)
            if level == "ERROR" or level == "CRITICAL":
                errors.append(line)
            elif level == "WARN":
                warnings.append(line)

            # Check for crash patterns
            if any(pattern in line.lower() for pattern in self.CRASH_PATTERNS):
                crashes.append(line)

            # Check for resource exhaustion
            if any(pattern in line.lower() for pattern in self.RESOURCE_PATTERNS):
                resource_issues.append(line)

        if errors:
            metadata["error_count"] = len(errors)
            issues.append(f"Found {len(errors)} error(s)")

        if warnings and len(warnings) > len(lines) * 0.2:
            metadata["warning_count"] = len(warnings)
            issues.append(f"Excessive warnings: {len(warnings)}/{len(lines)} ({len(warnings)/len(lines)*100:.0f}%)")

        if crashes:
            metadata["crash_patterns"] = crashes[:5]
            issues.append(f"Detected {len(crashes)} crash pattern(s)")

        if resource_issues:
            issues.append(f"Detected {len(resource_issues)} resource exhaustion event(s)")

        is_valid = len(issues) == 0
        confidence = 1.0 if is_valid else max(0.0, 1.0 - (len(issues) * 0.2))

        return IntelligenceResult(
            content_type=log_format if log_format != "unknown" else "syslog",
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            metadata=metadata
        )

    def _detect_format(self, text: str) -> str:
        """Detect log file format."""
        lines = text.split("\n")
        first_lines = "\n".join(lines[:10])

        for fmt, pattern in self.LOG_FORMATS.items():
            if re.search(pattern, first_lines, re.MULTILINE):
                return fmt

        return "unknown"

    def _extract_level(self, line: str) -> Optional[str]:
        """Extract log level from line."""
        line_upper = line.upper()
        if "ERROR" in line_upper or "ERR" in line_upper:
            return "ERROR"
        if "WARN" in line_upper:
            return "WARN"
        if "DEBUG" in line_upper:
            return "DEBUG"
        if "INFO" in line_upper:
            return "INFO"
        if "CRITICAL" in line_upper:
            return "CRITICAL"
        return None
