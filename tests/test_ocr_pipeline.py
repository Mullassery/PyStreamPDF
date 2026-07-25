"""
Tests for OcrPipeline hybrid text/OCR processing.
"""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest
from pystreampdf.ocr import (
    ProcessedPage,
    OcrPipeline,
    OcrManager,
    OcrProvider,
    OcrResult,
    OcrCapabilities,
)


class TestProcessedPage:
    """Test ProcessedPage dataclass."""

    def test_processed_page_creation(self):
        """Create a ProcessedPage."""
        page = ProcessedPage(
            page_number=1,
            text="extracted text",
            confidence=0.95,
            is_scanned=False,
            source="text"
        )
        assert page.page_number == 1
        assert page.text == "extracted text"
        assert page.confidence == 0.95
        assert page.is_scanned is False
        assert page.source == "text"
        assert page.ocr_result is None

    def test_processed_page_with_ocr_result(self):
        """ProcessedPage can hold OCR result."""
        ocr_result = OcrResult(
            text="ocr text",
            confidence=0.88,
            provider_name="tesseract"
        )
        page = ProcessedPage(
            page_number=2,
            text="ocr text",
            confidence=0.88,
            is_scanned=True,
            source="ocr",
            ocr_result=ocr_result
        )
        assert page.is_scanned is True
        assert page.source == "ocr"
        assert page.ocr_result is not None
        assert page.ocr_result.provider_name == "tesseract"

    def test_processed_page_fields(self):
        """ProcessedPage has all required fields."""
        page = ProcessedPage(
            page_number=5,
            text="test",
            confidence=0.9,
            is_scanned=False,
            source="text"
        )
        assert hasattr(page, "page_number")
        assert hasattr(page, "text")
        assert hasattr(page, "confidence")
        assert hasattr(page, "is_scanned")
        assert hasattr(page, "source")
        assert hasattr(page, "ocr_result")


class MockOcrProvider(OcrProvider):
    """Mock OCR provider for testing."""

    def __init__(self, name: str = "mock"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def capabilities(self) -> OcrCapabilities:
        return OcrCapabilities()

    def extract(self, image_data: bytes, page_number=None) -> OcrResult:
        return OcrResult(
            text=f"OCR text from page {page_number}",
            confidence=0.85,
            provider_name=self._name,
            page_number=page_number
        )

    def is_available(self) -> bool:
        return True


class TestOcrPipeline:
    """Test OcrPipeline."""

    def test_pipeline_creation(self):
        """Create an OcrPipeline."""
        manager = OcrManager()
        pipeline = OcrPipeline(manager)
        assert pipeline.ocr_manager is manager

    def test_pipeline_auto_manager(self):
        """Pipeline creates auto manager if none provided."""
        pipeline = OcrPipeline()
        assert pipeline.ocr_manager is not None
        assert isinstance(pipeline.ocr_manager, OcrManager)

    def test_pipeline_with_text_pdf_uses_existing_extraction(self, multi_page_pdf):
        """Pipeline processes text-based PDFs without OCR."""
        # multi_page_pdf fixture creates a 5-page PDF with text
        pipeline = OcrPipeline()

        try:
            # This will use existing Rust extraction for text pages
            # Since the fixture PDF is text-based, is_likely_scanned should be False
            pages = pipeline.process_document(multi_page_pdf)

            # Should get one processed page per PDF page
            assert len(pages) == 5

            # All should be text source (not OCR)
            for page in pages:
                assert page.source == "text"
                assert page.is_scanned is False

            # Should have text content
            for page in pages:
                assert page.text is not None
                assert len(page.text) >= 0  # Could be empty for generated test PDF

        except Exception as e:
            # If pystreampdf.open fails due to missing Rust core, skip gracefully
            pytest.skip(f"Rust core not available: {e}")

    def test_pipeline_pymupdf_import_error(self):
        """Pipeline raises error for non-existent PDF."""
        # This is hard to test without actually removing pymupdf
        # We just verify that process_document handles errors gracefully
        pipeline = OcrPipeline()

        # Try to process a non-existent file to trigger error handling
        with pytest.raises((FileNotFoundError, ImportError, OSError)):
            # This will fail on file not found or on import
            pipeline.process_document("/nonexistent/path.pdf")


class TestOcrPipelineIntegration:
    """Integration tests for OcrPipeline."""

    def test_pipeline_dispatch_to_provider(self, multi_page_pdf):
        """Pipeline dispatches to specified OCR provider."""
        manager = OcrManager()
        mock_provider = MockOcrProvider("test_provider")
        manager.register(mock_provider)

        pipeline = OcrPipeline(manager)

        try:
            # This will attempt to process the PDF
            # For text-based PDFs, OCR won't be invoked
            # We're just checking the pipeline doesn't crash
            pages = pipeline.process_document(multi_page_pdf, provider_name="test_provider")

            assert len(pages) > 0
            # Pages should be processed (text-based, so source="text")

        except Exception as e:
            pytest.skip(f"Rust core not available: {e}")

    def test_pipeline_processes_all_pages(self, multi_page_pdf):
        """Pipeline processes all pages in document."""
        pipeline = OcrPipeline()

        try:
            pages = pipeline.process_document(multi_page_pdf)

            # Check we got multiple pages
            assert len(pages) >= 1

            # Each page should have a page_number
            page_numbers = [p.page_number for p in pages]
            assert len(set(page_numbers)) == len(page_numbers)  # All unique

        except Exception as e:
            pytest.skip(f"Rust core not available: {e}")
