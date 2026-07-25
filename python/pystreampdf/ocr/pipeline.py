"""
OCR Pipeline for hybrid text/OCR document processing.

Routes text-based pages through existing extraction and scanned pages through OCR.
"""

from dataclasses import dataclass
from typing import List, Optional
import time

from .manager import OcrManager
from .provider import OcrResult


@dataclass
class ProcessedPage:
    """A page processed by the OCR pipeline."""
    page_number: int
    text: str  # Full extracted text
    confidence: float  # 0.0-1.0
    is_scanned: bool  # True if OCR was used, False if text-based
    source: str  # "text" or "ocr"
    ocr_result: Optional[OcrResult] = None  # OCR result if scanned


class OcrPipeline:
    """
    Hybrid pipeline: uses existing Rust extraction for text PDFs,
    falls back to OCR for scanned pages.
    """

    def __init__(self, ocr_manager: Optional[OcrManager] = None):
        """
        Initialize the pipeline.

        Args:
            ocr_manager: OcrManager instance (if None, creates auto-configured manager)
        """
        self.ocr_manager = ocr_manager or OcrManager.auto()

    def process_document(
        self, pdf_path: str, provider_name: Optional[str] = None
    ) -> List[ProcessedPage]:
        """
        Process all pages in a PDF.

        Text-based pages use existing Rust extraction.
        Scanned pages are processed via OCR.

        Args:
            pdf_path: Path to PDF file
            provider_name: OCR provider to use for scanned pages

        Returns:
            List of ProcessedPage

        Raises:
            ImportError: If pymupdf not installed when scanned pages need processing
            FileNotFoundError: If PDF not found
        """
        # Import here to avoid hard dependency
        try:
            import pystreampdf
        except ImportError as e:
            raise ImportError(
                "pystreampdf core module required. Install with: pip install pystreampdf"
            ) from e

        # Open PDF using existing Rust bindings
        doc = pystreampdf.open(pdf_path)
        processed_pages = []

        for page_idx in range(doc.page_count):
            page = doc.page(page_idx + 1)  # Pages are 1-indexed in Rust API

            if page.is_likely_scanned:
                # Process via OCR
                processed = self._process_scanned_page(
                    pdf_path, page_idx + 1, provider_name
                )
            else:
                # Use existing text extraction
                processed = ProcessedPage(
                    page_number=page_idx + 1,
                    text=page.text,
                    confidence=1.0,  # Text extraction is highly reliable
                    is_scanned=False,
                    source="text"
                )

            processed_pages.append(processed)

        return processed_pages

    def _process_scanned_page(
        self, pdf_path: str, page_number: int, provider_name: Optional[str] = None
    ) -> ProcessedPage:
        """
        Process a single scanned page via OCR.

        Args:
            pdf_path: Path to PDF
            page_number: 1-indexed page number
            provider_name: OCR provider to use

        Returns:
            ProcessedPage

        Raises:
            ImportError: If pymupdf not installed
        """
        try:
            import fitz
        except ImportError as e:
            raise ImportError(
                "pymupdf required for scanned PDF processing. "
                "Install with: pip install pymupdf"
            ) from e

        # Extract image from PDF page
        pdf_doc = fitz.open(pdf_path)
        page = pdf_doc[page_number - 1]  # 0-indexed in pymupdf
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
        image_data = pix.tobytes("png")
        pdf_doc.close()

        # Extract via OCR
        start_time = time.time()
        ocr_result = self.ocr_manager.extract(image_data, provider_name, page_number)
        processing_time = (time.time() - start_time) * 1000  # ms

        # Ensure result has metadata
        ocr_result.processing_time_ms = processing_time
        ocr_result.page_number = page_number

        return ProcessedPage(
            page_number=page_number,
            text=ocr_result.text,
            confidence=ocr_result.confidence,
            is_scanned=True,
            source="ocr",
            ocr_result=ocr_result
        )
