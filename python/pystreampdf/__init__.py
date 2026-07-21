"""PyStreamPDF - Intelligence Engine for PDFs.

Intelligent PDF parsing, retrieval, and context extraction for AI agents.
Reduces token usage by 10-50x while maintaining accuracy.
"""

__version__ = "2.2.0"

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

# OCR and configuration modules
from .ocr import (
    OCRProcessor,
    OCRConfig,
    OCRBackend,
    OCRResult,
    process_scanned_pdf,
)

from .config import (
    TokenBudgetConfig,
    RetrievalConfig,
    FilteringConfig,
    suggest_budget_for_use_case,
)

from .search import (
    SearchResult,
    SearchFilter,
    SearchResults,
    combine_filters,
)

from .query_analyzer import (
    QueryAnalyzer,
    AutoBudgetSelector,
    QueryAnalysis,
    TokenBudgetLevel,
    auto_select_budget,
)

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
    # OCR & configuration
    "OCRProcessor",
    "OCRConfig",
    "OCRBackend",
    "OCRResult",
    "process_scanned_pdf",
    "TokenBudgetConfig",
    "RetrievalConfig",
    "FilteringConfig",
    "suggest_budget_for_use_case",
    # Search & filtering
    "SearchResult",
    "SearchFilter",
    "SearchResults",
    "combine_filters",
    # Query analysis & auto-budget selection
    "QueryAnalyzer",
    "AutoBudgetSelector",
    "QueryAnalysis",
    "TokenBudgetLevel",
    "auto_select_budget",
]
