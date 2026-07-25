"""
PyStreamPDF OCR Module

Pluggable OCR provider framework with support for Tesseract, PaddleOCR, and custom providers.

Example:
    >>> from pystreampdf.ocr import OcrManager, OcrPipeline
    >>> manager = OcrManager.auto()  # Auto-detect installed providers
    >>> pipeline = OcrPipeline(manager)
    >>> pages = pipeline.process_document("document.pdf", provider_name="paddle")
"""

from .manager import OcrManager
from .pipeline import OcrPipeline, ProcessedPage
from .provider import OcrCapabilities, OcrProvider, OcrResult, TextRegion
from .providers import PaddleProvider, TesseractProvider

__all__ = [
    "OcrProvider",
    "OcrResult",
    "TextRegion",
    "OcrCapabilities",
    "OcrManager",
    "OcrPipeline",
    "ProcessedPage",
    "TesseractProvider",
    "PaddleProvider",
]
