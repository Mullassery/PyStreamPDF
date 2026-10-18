"""PyStreamPDF - Intelligence Engine for PDFs.

Intelligent PDF parsing, retrieval, and context extraction for AI agents.
Actual token savings depend on your documents — see the README's "Token
Savings" section rather than relying on a fixed multiplier here.
"""

__version__ = "2.3.2"  # Real MCP tool implementations (extract/OCR/validate/etc.), previously all hardcoded fixture data

# Optional: Rust core bindings (requires maturin build)
try:
    from pystreampdf._core import load_index, open
except ImportError:
    open = None
    load_index = None

# Python extraction and parsing modules
from .cache import CachedDocument, PDFCache
from .extraction import (
    CitationTracker,
    ContentChunk,
    ElementType,
    MultimediaAnalyzer,
    MultimediaElement,
    ReadingOrder,
    ReadingOrderCorrector,
    SemanticChunker,
    SourceLocation,
    TableExtractor,
    TableStructure,
    TextFragment,
)

# Caching and token budget configuration
from .token_budget import BudgetRule, TokenBudgetConfig

# Dashboard and CLI utilities
try:
    from .cli_dashboard import (
        DashboardMetrics,
        PyStreamPDFDashboard,
        RichDashboard,
        SimpleDashboard,
        TextualDashboard,
    )
except ImportError:
    DashboardMetrics = None
    SimpleDashboard = None
    RichDashboard = None
    TextualDashboard = None
    PyStreamPDFDashboard = None

# Excel export utilities
try:
    from .excel_export import (
        ExcelExporter,
        ExtractedTable,
        PDFToExcelPipeline,
    )
except ImportError:
    ExtractedTable = None
    ExcelExporter = None
    PDFToExcelPipeline = None

# OCR module (optional)
try:
    from .ocr import (
        OcrCapabilities,
        OcrManager,
        OcrPipeline,
        OcrProvider,
        OcrResult,
        PaddleProvider,
        ProcessedPage,
        TesseractProvider,
        TextRegion,
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
        ConfidenceScorer,
        LayoutValidator,
        OcrTable,
        PageConfidenceScore,
        Recommendation,
        TableValidationResult,
        TableValidator,
        TextValidator,
        ValidationIssue,
        ValidationResult,
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
        CodeAnalyzer,
        CorrectionSuggestion,
        IntelligenceResult,
        JSONAnalyzer,
        LogAnalyzer,
        SQLAnalyzer,
        YAMLAnalyzer,
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
        AnalysisMetrics,
        AnalysisPipeline,
        AnalysisStage,
        UnifiedAnalysisResult,
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
        GraphEdge,
        GraphNode,
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
    # Dashboard and CLI (optional)
    *((["DashboardMetrics", "SimpleDashboard", "RichDashboard", "TextualDashboard", "PyStreamPDFDashboard"]) if DashboardMetrics is not None else []),
    # Excel export (optional)
    *((["ExtractedTable", "ExcelExporter", "PDFToExcelPipeline"]) if ExtractedTable is not None else []),
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
