"""Unified analysis pipeline connecting OCR → Validation → Intelligence → Structure."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time

from .ocr.provider import OcrResult
from .validation.types import ValidationResult
from .intelligence.types import IntelligenceResult


class AnalysisStage(Enum):
    """Pipeline stages."""
    OCR = "ocr"
    VALIDATION = "validation"
    INTELLIGENCE = "intelligence"
    STRUCTURE = "structure"


@dataclass
class AnalysisMetrics:
    """Track performance and cost of analysis."""
    stage: AnalysisStage
    analyzer_name: str
    duration_ms: float
    memory_bytes: int = 0
    input_size: int = 0
    output_size: int = 0

    @property
    def cost_ratio(self) -> float:
        """Output size per millisecond."""
        if self.duration_ms == 0:
            return 0.0
        return self.output_size / self.duration_ms


@dataclass
class UnifiedAnalysisResult:
    """Complete analysis result with confidence propagation through all stages."""

    # Input
    content: str
    content_type: Optional[str] = None

    # Stage results
    ocr_result: Optional[OcrResult] = None
    validation_result: Optional[ValidationResult] = None
    intelligence_result: Optional[IntelligenceResult] = None

    # Unified confidence (0.0-1.0)
    # Combines: OCR confidence × Validation confidence × Intelligence confidence
    overall_confidence: float = 0.0

    # Breakdown
    ocr_confidence: float = 0.0  # From OcrResult
    validation_confidence: float = 0.0  # From ValidationResult
    intelligence_confidence: float = 0.0  # From IntelligenceResult

    # Error tracking
    errors: List[str] = field(default_factory=list)
    fallback_used: bool = False  # Did we fall back to raw content?

    # Metrics
    metrics: List[AnalysisMetrics] = field(default_factory=list)

    # Structure (for Phase 5d)
    structure_nodes: List[Dict[str, Any]] = field(default_factory=list)
    structure_edges: List[tuple] = field(default_factory=list)

    def compute_confidence(self) -> float:
        """
        Compute unified confidence score.

        Strategy: Multiply all stage confidences, with special handling for missing stages.
        - If a stage failed/returned no result: assume neutral (1.0, not 0.0)
        - If a stage returned low confidence: propagate it
        """
        confidences = []

        if self.ocr_confidence > 0:
            confidences.append(self.ocr_confidence)
        if self.validation_confidence > 0:
            confidences.append(self.validation_confidence)
        if self.intelligence_confidence > 0:
            confidences.append(self.intelligence_confidence)

        # No results = neutral confidence
        if not confidences:
            self.overall_confidence = 1.0
            return 1.0

        # Multiply all confidences (conservative: weakest link matters)
        result = 1.0
        for conf in confidences:
            result *= conf

        self.overall_confidence = max(0.0, min(1.0, result))
        return self.overall_confidence

    def get_recommendation(self) -> str:
        """Get recommendation based on overall confidence."""
        if self.fallback_used:
            return "FALLBACK_USED: Original content unavailable, using raw text"
        if self.overall_confidence >= 0.85:
            return "ACCEPT: High confidence in analysis results"
        if self.overall_confidence >= 0.60:
            return "REVIEW: Medium confidence, manual review recommended"
        return "RERUN: Low confidence, re-analyze with alternative methods"

    def add_metric(self, stage: AnalysisStage, analyzer_name: str, duration_ms: float) -> None:
        """Record performance metric for a stage."""
        metric = AnalysisMetrics(
            stage=stage,
            analyzer_name=analyzer_name,
            duration_ms=duration_ms,
            input_size=len(self.content) if self.content else 0,
        )
        self.metrics.append(metric)

    def add_error(self, stage: AnalysisStage, error: str) -> None:
        """Record error during analysis."""
        self.errors.append(f"[{stage.value}] {error}")

    def total_duration_ms(self) -> float:
        """Total analysis time across all stages."""
        return sum(m.duration_ms for m in self.metrics)

    def most_expensive_stage(self) -> Optional[AnalysisMetrics]:
        """Which stage took the longest?"""
        if not self.metrics:
            return None
        return max(self.metrics, key=lambda m: m.duration_ms)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content_type": self.content_type,
            "overall_confidence": self.overall_confidence,
            "confidence_breakdown": {
                "ocr": self.ocr_confidence,
                "validation": self.validation_confidence,
                "intelligence": self.intelligence_confidence,
            },
            "recommendation": self.get_recommendation(),
            "fallback_used": self.fallback_used,
            "errors": self.errors,
            "metrics": [
                {
                    "stage": m.stage.value,
                    "analyzer": m.analyzer_name,
                    "duration_ms": m.duration_ms,
                    "cost_ratio": m.cost_ratio,
                }
                for m in self.metrics
            ],
        }


class AnalysisPipeline:
    """
    Unified pipeline: OCR → Validation → Intelligence → Structure.

    Handles:
    - Confidence propagation through all stages
    - Error recovery with fallbacks
    - Performance tracking
    - Cost monitoring
    """

    def __init__(self):
        self.results_cache: Dict[str, UnifiedAnalysisResult] = {}

    def analyze(
        self,
        content: str,
        run_ocr: bool = False,
        run_validation: bool = False,
        run_intelligence: bool = False,
    ) -> UnifiedAnalysisResult:
        """
        Run full analysis pipeline with error recovery.

        Args:
            content: Text to analyze
            run_ocr: Include OCR stage (requires image input)
            run_validation: Include validation stage
            run_intelligence: Include intelligence stage

        Returns:
            UnifiedAnalysisResult with all confidence scores propagated
        """
        result = UnifiedAnalysisResult(content=content)

        if not content or not content.strip():
            result.overall_confidence = 0.0
            return result

        # Stage 1: Validation (if requested)
        if run_validation:
            try:
                start = time.time()
                from .validation import TextValidator

                validator = TextValidator()
                validation_result = validator.validate(content)
                duration = (time.time() - start) * 1000

                result.validation_result = validation_result
                result.validation_confidence = validation_result.confidence
                result.add_metric(AnalysisStage.VALIDATION, "TextValidator", duration)

            except Exception as e:
                result.add_error(AnalysisStage.VALIDATION, str(e))

        # Stage 2: Intelligence (if requested)
        if run_intelligence:
            result = self._run_intelligence_stage(result)

        # Compute final confidence
        result.compute_confidence()

        return result

    def _run_intelligence_stage(self, result: UnifiedAnalysisResult) -> UnifiedAnalysisResult:
        """
        Run intelligence analysis with automatic language/format detection.

        Tries multiple analyzers and picks the best match.
        """
        from .intelligence import (
            YAMLAnalyzer,
            JSONAnalyzer,
            CodeAnalyzer,
            LogAnalyzer,
            SQLAnalyzer,
        )

        analyzers = [
            ("yaml", YAMLAnalyzer()),
            ("json", JSONAnalyzer()),
            ("sql", SQLAnalyzer()),
            ("code", CodeAnalyzer()),
            ("log", LogAnalyzer()),
        ]

        best_result = None
        best_confidence = 0.0
        best_name = "unknown"

        for name, analyzer in analyzers:
            try:
                start = time.time()
                intel_result = analyzer.analyze(result.content)
                duration = (time.time() - start) * 1000

                result.add_metric(AnalysisStage.INTELLIGENCE, name, duration)

                # Track best match
                if intel_result.confidence > best_confidence:
                    best_confidence = intel_result.confidence
                    best_result = intel_result
                    best_name = name

            except Exception as e:
                result.add_error(AnalysisStage.INTELLIGENCE, f"{name}: {str(e)}")

        if best_result:
            result.intelligence_result = best_result
            result.intelligence_confidence = best_confidence
            result.content_type = best_name

        return result

    def get_confidence_report(self, result: UnifiedAnalysisResult) -> str:
        """Generate human-readable confidence report."""
        lines = [
            f"Content Type: {result.content_type or 'unknown'}",
            f"Overall Confidence: {result.overall_confidence:.1%}",
            "",
            "Confidence Breakdown:",
            f"  OCR:          {result.ocr_confidence:.1%}",
            f"  Validation:   {result.validation_confidence:.1%}",
            f"  Intelligence: {result.intelligence_confidence:.1%}",
            "",
            f"Recommendation: {result.get_recommendation()}",
        ]

        if result.errors:
            lines.append("")
            lines.append("Errors encountered:")
            for error in result.errors:
                lines.append(f"  • {error}")

        if result.metrics:
            lines.append("")
            lines.append(f"Performance: {result.total_duration_ms():.1f}ms total")
            slowest = result.most_expensive_stage()
            if slowest:
                lines.append(f"  Slowest: {slowest.analyzer_name} ({slowest.duration_ms:.1f}ms)")

        return "\n".join(lines)
