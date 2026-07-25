"""PyStreamPDF - Intelligence Engine for PDFs.

Intelligent PDF parsing, retrieval, and context extraction for AI agents.
Reduces token usage by 10-50x while maintaining accuracy.
"""

__version__ = "2.1.0"  # Phase 5c + Critical Gaps + Phase 5d + Phase 5e

# Optional: Rust core bindings (requires maturin build)
try:
    from pystreampdf._core import open, load_index
except ImportError:
    open = None
    load_index = None

# Python extraction and parsing modules
from .extraction import (
    ReadingOrderCorrector,
    TableExtractor,
    SemanticChunker,
    MultimediaAnalyzer,
    CitationTracker,
    ElementType,
    ReadingOrder,
    ContentChunk,
    TableStructure,
    MultimediaElement,
    SourceLocation,
    TextFragment,
)

# Caching and token budget configuration
from .token_budget import TokenBudgetConfig, BudgetRule
from .cache import PDFCache, CachedDocument

# OCR module (optional)
try:
    from .ocr import (
        OcrManager,
        OcrProvider,
        OcrResult,
        OcrPipeline,
        ProcessedPage,
        TextRegion,
        OcrCapabilities,
        TesseractProvider,
        PaddleProvider,
    )
except ImportError:
    OcrManager = None
    OcrProvider = None
    OcrResult = None
    OcrPipeline = None
    ProcessedPage = None
    TextRegion = None
    OcrCapabilities = None
    TesseractProvider = None
    PaddleProvider = None

# Validation module (optional)
try:
    from .validation import (
        TextValidator,
        TableValidator,
        LayoutValidator,
        ConfidenceScorer,
        ValidationIssue,
        ValidationResult,
        TableValidationResult,
        OcrTable,
        PageConfidenceScore,
        Recommendation,
    )
except ImportError:
    TextValidator = None
    TableValidator = None
    LayoutValidator = None
    ConfidenceScorer = None
    ValidationIssue = None
    ValidationResult = None
    TableValidationResult = None
    OcrTable = None
    PageConfidenceScore = None
    Recommendation = None

# Intelligence module (optional)
try:
    from .intelligence import (
        YAMLAnalyzer,
        JSONAnalyzer,
        CodeAnalyzer,
        LogAnalyzer,
        SQLAnalyzer,
        IntelligenceResult,
        CorrectionSuggestion,
    )
except ImportError:
    YAMLAnalyzer = None
    JSONAnalyzer = None
    CodeAnalyzer = None
    LogAnalyzer = None
    SQLAnalyzer = None
    IntelligenceResult = None
    CorrectionSuggestion = None

# Unified analysis pipeline (Phase 5c integration)
try:
    from .pipeline import (
        AnalysisPipeline,
        UnifiedAnalysisResult,
        AnalysisStage,
        AnalysisMetrics,
    )
except ImportError:
    AnalysisPipeline = None
    UnifiedAnalysisResult = None
    AnalysisStage = None
    AnalysisMetrics = None

# Structure recovery (Phase 5d foundation)
try:
    from .structure import (
        DocumentGraph,
        GraphNode,
        GraphEdge,
        RelationshipExtractor,
        RelationType,
    )
except ImportError:
    DocumentGraph = None
    GraphNode = None
    GraphEdge = None
    RelationshipExtractor = None
    RelationType = None

__all__ = [
    # Core (optional)
    *((["open", "load_index"]) if open and load_index else []),
    # Extraction & parsing
    "ReadingOrderCorrector",
    "TableExtractor",
    "SemanticChunker",
    "MultimediaAnalyzer",
    "CitationTracker",
    "ElementType",
    "ReadingOrder",
    "ContentChunk",
    "TableStructure",
    "MultimediaElement",
    "SourceLocation",
    "TextFragment",
    # Caching and token budgets
    "TokenBudgetConfig",
    "BudgetRule",
    "PDFCache",
    "CachedDocument",
    # OCR (optional)
    *((["OcrManager", "OcrProvider", "OcrResult", "OcrPipeline", "ProcessedPage", "TextRegion", "OcrCapabilities", "TesseractProvider", "PaddleProvider"]) if OcrManager is not None else []),
    # Validation (optional)
    *((["TextValidator", "TableValidator", "LayoutValidator", "ConfidenceScorer", "ValidationIssue", "ValidationResult", "TableValidationResult", "OcrTable", "PageConfidenceScore", "Recommendation"]) if TextValidator is not None else []),
    # Intelligence (optional)
    *((["YAMLAnalyzer", "JSONAnalyzer", "CodeAnalyzer", "LogAnalyzer", "SQLAnalyzer", "IntelligenceResult", "CorrectionSuggestion"]) if YAMLAnalyzer is not None else []),
    # Pipeline (optional)
    *((["AnalysisPipeline", "UnifiedAnalysisResult", "AnalysisStage", "AnalysisMetrics"]) if AnalysisPipeline is not None else []),
    # Structure recovery (optional)
    *((["DocumentGraph", "GraphNode", "GraphEdge", "RelationshipExtractor", "RelationType"]) if DocumentGraph is not None else []),
]
