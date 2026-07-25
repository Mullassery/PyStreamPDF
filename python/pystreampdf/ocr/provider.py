"""
OCR Provider abstraction layer.

Defines the base OcrProvider interface and common data structures for OCR results.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TextRegion:
    """A region of text extracted by OCR with spatial and confidence information."""
    text: str
    confidence: float  # 0.0-1.0
    bbox: tuple  # (x, y, width, height) in pixel coordinates
    language: Optional[str] = None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")


@dataclass
class OcrResult:
    """Complete OCR extraction result for a single image or page."""
    text: str  # Full extracted text
    confidence: float  # Overall confidence 0.0-1.0
    regions: List[TextRegion] = field(default_factory=list)  # Per-region details
    provider_name: str = ""  # Name of OCR provider that generated this
    page_number: Optional[int] = None  # Page number if from multi-page PDF
    processing_time_ms: Optional[float] = None  # Time to extract (for perf tracking)
    metadata: Dict = field(default_factory=dict)  # Provider-specific metadata

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")


@dataclass
class OcrCapabilities:
    """Capabilities and limits of an OCR provider."""
    supports_handwriting: bool = False
    supports_tables: bool = False
    supports_formulas: bool = False
    supported_languages: List[str] = field(default_factory=list)  # e.g. ["en", "fr"]
    max_image_size: Optional[tuple] = None  # (width, height) in pixels


class OcrProvider(ABC):
    """Abstract base class for OCR providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g. 'tesseract', 'paddle', 'unlimited_ocr')."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Provider version string."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> OcrCapabilities:
        """Capabilities of this provider."""
        pass

    @abstractmethod
    def extract(self, image_data: bytes, page_number: Optional[int] = None) -> OcrResult:
        """
        Extract text from image data.

        Args:
            image_data: Image bytes (PNG, JPEG, etc.)
            page_number: Optional page number for tracking

        Returns:
            OcrResult with extracted text and regions

        Raises:
            ImportError: If required dependencies are not installed
            ValueError: If image_data is invalid
        """
        pass

    def extract_batch(self, images: List[tuple]) -> List[OcrResult]:
        """
        Extract text from multiple images.

        Args:
            images: List of (image_data: bytes, page_number: int) tuples

        Returns:
            List of OcrResult, one per image

        Default implementation calls extract() for each image.
        Subclasses can override for true batch processing.
        """
        return [self.extract(img_data, page_num) for img_data, page_num in images]

    def is_available(self) -> bool:
        """
        Check if this provider is available (dependencies installed, etc).

        Returns:
            True if provider can be used, False otherwise
        """
        return True
