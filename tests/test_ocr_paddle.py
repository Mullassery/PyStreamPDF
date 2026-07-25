"""
Tests for PaddleProvider.
"""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest


class TestPaddleProvider:
    """Test PaddleProvider."""

    def test_paddle_import_available(self):
        """PaddleProvider can be imported."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider
            assert PaddleProvider is not None
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_creation(self):
        """Create PaddleProvider."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider()
            assert provider is not None
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_name(self):
        """PaddleProvider has correct name."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider()
            assert provider.name == "paddle"
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_version(self):
        """PaddleProvider returns version string."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider()
            version = provider.version
            assert isinstance(version, str)
            # Version can be "unavailable" or actual version
            assert len(version) > 0
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_capabilities(self):
        """PaddleProvider exposes capabilities."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider
            from pystreampdf.ocr import OcrCapabilities

            provider = PaddleProvider()
            caps = provider.capabilities

            assert isinstance(caps, OcrCapabilities)
            assert hasattr(caps, "supports_handwriting")
            assert hasattr(caps, "supported_languages")
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_is_available(self):
        """PaddleProvider.is_available() returns bool."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider()
            available = provider.is_available()
            assert isinstance(available, bool)
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_languages_config(self):
        """PaddleProvider accepts language configuration."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider(languages=["en"])
            assert provider.languages == ["en"]

            provider2 = PaddleProvider(use_gpu=False)
            assert provider2.use_gpu is False

            provider3 = PaddleProvider(languages=["ch"], use_gpu=True)
            assert provider3.languages == ["ch"]
            assert provider3.use_gpu is True
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_lazy_initialization(self):
        """PaddleProvider doesn't initialize OCR engine on creation."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider()
            # _ocr should be None until first extract()
            assert provider._ocr is None
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_extract_requires_deps(self):
        """PaddleProvider.extract() requires paddleocr and pillow."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider()

            if provider.is_available():
                # If paddleocr is installed, extract should work with valid image data
                # We skip the actual extraction as it requires model download
                assert callable(provider.extract)
            else:
                # If paddleocr isn't installed, extract should raise ImportError
                with pytest.raises(ImportError):
                    provider.extract(b"invalid image data")

        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_extract_batch_inherits_default(self):
        """PaddleProvider uses default extract_batch."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            provider = PaddleProvider()
            # extract_batch should exist (inherited default)
            assert hasattr(provider, "extract_batch")
            assert callable(provider.extract_batch)
        except ImportError:
            pytest.skip("PaddleProvider not available")

    def test_paddle_provider_multiple_languages(self):
        """PaddleProvider supports multiple language codes."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider

            # PaddleOCR supports: en, ch (Chinese), fr, de, etc.
            provider_en = PaddleProvider(languages=["en"])
            assert provider_en.languages == ["en"]

            provider_ch = PaddleProvider(languages=["ch"])
            assert provider_ch.languages == ["ch"]

            provider_fr = PaddleProvider(languages=["fr"])
            assert provider_fr.languages == ["fr"]
        except ImportError:
            pytest.skip("PaddleProvider not available")


class TestPaddleProviderIntegration:
    """Integration tests for PaddleProvider (skip if paddleocr not installed)."""

    @pytest.mark.skipif(
        True,  # Skip by default since paddleocr requires model download
        reason="PaddleOCR model download not always available in CI"
    )
    def test_paddle_extract_minimal_image(self):
        """PaddleProvider can extract from minimal test image."""
        try:
            from pystreampdf.ocr.providers.paddle import PaddleProvider
            import io
            from PIL import Image, ImageDraw

            provider = PaddleProvider()

            if not provider.is_available():
                pytest.skip("PaddleOCR not installed")

            # Create minimal test image with text
            img = Image.new("RGB", (200, 100), color="white")
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), "Hello World", fill="black")

            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            image_data = img_bytes.getvalue()

            # Extract
            result = provider.extract(image_data, page_number=1)

            assert result.text is not None
            assert result.confidence >= 0.0
            assert result.provider_name == "paddle"
            assert result.page_number == 1

        except ImportError:
            pytest.skip("PaddleProvider or dependencies not available")
