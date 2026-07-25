"""
Tests for OCR provider base classes and data structures.
"""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest
from pystreampdf.ocr import (
    TextRegion,
    OcrResult,
    OcrCapabilities,
    OcrProvider,
)


class TestTextRegion:
    """Test TextRegion dataclass."""

    def test_text_region_creation(self):
        """Create a TextRegion."""
        region = TextRegion(
            text="hello",
            confidence=0.95,
            bbox=(10, 20, 100, 30),
            language="en"
        )
        assert region.text == "hello"
        assert region.confidence == 0.95
        assert region.bbox == (10, 20, 100, 30)
        assert region.language == "en"

    def test_text_region_default_language(self):
        """TextRegion language defaults to None."""
        region = TextRegion(text="test", confidence=0.8, bbox=(0, 0, 10, 10))
        assert region.language is None

    def test_text_region_confidence_range(self):
        """Confidence must be 0.0-1.0."""
        TextRegion(text="test", confidence=0.0, bbox=(0, 0, 1, 1))
        TextRegion(text="test", confidence=1.0, bbox=(0, 0, 1, 1))

        with pytest.raises(ValueError):
            TextRegion(text="test", confidence=-0.1, bbox=(0, 0, 1, 1))

        with pytest.raises(ValueError):
            TextRegion(text="test", confidence=1.1, bbox=(0, 0, 1, 1))


class TestOcrResult:
    """Test OcrResult dataclass."""

    def test_ocr_result_creation(self):
        """Create an OcrResult."""
        result = OcrResult(
            text="extracted text",
            confidence=0.92,
            provider_name="tesseract",
            page_number=1
        )
        assert result.text == "extracted text"
        assert result.confidence == 0.92
        assert result.provider_name == "tesseract"
        assert result.page_number == 1
        assert result.regions == []
        assert result.metadata == {}

    def test_ocr_result_with_regions(self):
        """OcrResult with text regions."""
        regions = [
            TextRegion(text="hello", confidence=0.95, bbox=(0, 0, 50, 20)),
            TextRegion(text="world", confidence=0.93, bbox=(60, 0, 50, 20)),
        ]
        result = OcrResult(
            text="hello world",
            confidence=0.94,
            regions=regions,
            provider_name="paddle"
        )
        assert len(result.regions) == 2
        assert result.regions[0].text == "hello"

    def test_ocr_result_with_metadata(self):
        """OcrResult with provider metadata."""
        metadata = {"language": "en", "region_count": 5}
        result = OcrResult(
            text="test",
            confidence=0.9,
            provider_name="test",
            metadata=metadata
        )
        assert result.metadata["language"] == "en"

    def test_ocr_result_processing_time(self):
        """OcrResult tracks processing time."""
        result = OcrResult(
            text="test",
            confidence=0.9,
            provider_name="test",
            processing_time_ms=150.5
        )
        assert result.processing_time_ms == 150.5

    def test_ocr_result_confidence_range(self):
        """OcrResult confidence must be 0.0-1.0."""
        OcrResult(text="test", confidence=0.0, provider_name="test")
        OcrResult(text="test", confidence=1.0, provider_name="test")

        with pytest.raises(ValueError):
            OcrResult(text="test", confidence=-0.1, provider_name="test")

        with pytest.raises(ValueError):
            OcrResult(text="test", confidence=1.1, provider_name="test")


class TestOcrCapabilities:
    """Test OcrCapabilities dataclass."""

    def test_capabilities_defaults(self):
        """OcrCapabilities defaults are False/empty."""
        caps = OcrCapabilities()
        assert caps.supports_handwriting is False
        assert caps.supports_tables is False
        assert caps.supports_formulas is False
        assert caps.supported_languages == []
        assert caps.max_image_size is None

    def test_capabilities_with_values(self):
        """OcrCapabilities with custom values."""
        caps = OcrCapabilities(
            supports_handwriting=True,
            supports_tables=True,
            supported_languages=["en", "fr", "de"],
            max_image_size=(4000, 3000)
        )
        assert caps.supports_handwriting is True
        assert caps.supports_tables is True
        assert len(caps.supported_languages) == 3
        assert caps.max_image_size == (4000, 3000)


class TestOcrProviderAbstract:
    """Test OcrProvider abstract base class."""

    def test_ocr_provider_is_abstract(self):
        """OcrProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            OcrProvider()  # type: ignore

    def test_ocr_provider_requires_name(self):
        """Subclass must implement name property."""
        class BadProvider(OcrProvider):
            @property
            def version(self) -> str:
                return "1.0"

            @property
            def capabilities(self) -> OcrCapabilities:
                return OcrCapabilities()

            def extract(self, image_data: bytes, page_number=None):
                return OcrResult(text="", confidence=0.0, provider_name="bad")

        with pytest.raises(TypeError):
            BadProvider()  # type: ignore

    def test_ocr_provider_concrete_implementation(self):
        """Valid concrete OcrProvider implementation."""
        class TestProvider(OcrProvider):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

            @property
            def capabilities(self) -> OcrCapabilities:
                return OcrCapabilities(supported_languages=["en"])

            def extract(self, image_data: bytes, page_number=None) -> OcrResult:
                return OcrResult(
                    text="test result",
                    confidence=0.9,
                    provider_name="test"
                )

        provider = TestProvider()
        assert provider.name == "test"
        assert provider.version == "1.0"
        assert provider.capabilities.supported_languages == ["en"]

        result = provider.extract(b"fake image data")
        assert result.text == "test result"
        assert result.provider_name == "test"

    def test_ocr_provider_is_available_default(self):
        """is_available() defaults to True."""
        class SimpleProvider(OcrProvider):
            @property
            def name(self) -> str:
                return "simple"

            @property
            def version(self) -> str:
                return "1.0"

            @property
            def capabilities(self) -> OcrCapabilities:
                return OcrCapabilities()

            def extract(self, image_data: bytes, page_number=None) -> OcrResult:
                return OcrResult(text="", confidence=0.0, provider_name="simple")

        provider = SimpleProvider()
        assert provider.is_available() is True

    def test_ocr_provider_extract_batch_default(self):
        """extract_batch() defaults to calling extract() per image."""
        class SimpleProvider(OcrProvider):
            @property
            def name(self) -> str:
                return "simple"

            @property
            def version(self) -> str:
                return "1.0"

            @property
            def capabilities(self) -> OcrCapabilities:
                return OcrCapabilities()

            def extract(self, image_data: bytes, page_number=None) -> OcrResult:
                return OcrResult(
                    text=f"page {page_number}",
                    confidence=0.9,
                    provider_name="simple",
                    page_number=page_number
                )

        provider = SimpleProvider()
        images = [
            (b"image1", 1),
            (b"image2", 2),
            (b"image3", 3),
        ]
        results = provider.extract_batch(images)

        assert len(results) == 3
        assert results[0].page_number == 1
        assert results[1].page_number == 2
        assert results[2].page_number == 3
