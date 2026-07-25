"""
Tests for TesseractProvider.
"""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest


class TestTesseractProvider:
    """Test TesseractProvider."""

    def test_tesseract_import_available(self):
        """TesseractProvider can be imported."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider
            assert TesseractProvider is not None
        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_creation(self):
        """Create TesseractProvider."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider

            provider = TesseractProvider()
            assert provider is not None
        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_name(self):
        """TesseractProvider has correct name."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider

            provider = TesseractProvider()
            assert provider.name == "tesseract"
        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_version(self):
        """TesseractProvider returns version string."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider

            provider = TesseractProvider()
            version = provider.version
            assert isinstance(version, str)
            # Version can be "unavailable" or actual version
            assert len(version) > 0
        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_capabilities(self):
        """TesseractProvider exposes capabilities."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider
            from pystreampdf.ocr import OcrCapabilities

            provider = TesseractProvider()
            caps = provider.capabilities

            assert isinstance(caps, OcrCapabilities)
            assert hasattr(caps, "supports_handwriting")
            assert hasattr(caps, "supported_languages")
        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_is_available(self):
        """TesseractProvider.is_available() returns bool."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider

            provider = TesseractProvider()
            available = provider.is_available()
            assert isinstance(available, bool)
        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_languages_config(self):
        """TesseractProvider accepts language configuration."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider

            provider = TesseractProvider(languages=["eng", "fra"])
            assert provider.languages == ["eng", "fra"]

            provider2 = TesseractProvider(config="--psm 3")
            assert provider2.config == "--psm 3"
        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_extract_requires_deps(self):
        """TesseractProvider.extract() requires pytesseract and Pillow."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider

            # Check if pytesseract is available
            try:
                import pytesseract  # noqa: F401
                pytesseract_available = True
            except ImportError:
                pytesseract_available = False

            provider = TesseractProvider()

            if pytesseract_available and provider.is_available():
                # If dependencies are installed, extract should work with valid image data
                # We skip the actual extraction as we don't have test images
                # but we verify the method exists
                assert callable(provider.extract)
            else:
                # If dependencies aren't installed, extract should raise ImportError
                with pytest.raises(ImportError):
                    provider.extract(b"invalid image data")

        except ImportError:
            pytest.skip("TesseractProvider not available")

    def test_tesseract_provider_extract_batch_inherits_default(self):
        """TesseractProvider uses default extract_batch."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider

            provider = TesseractProvider()
            # extract_batch should exist (inherited default)
            assert hasattr(provider, "extract_batch")
            assert callable(provider.extract_batch)
        except ImportError:
            pytest.skip("TesseractProvider not available")


class TestTesseractProviderIntegration:
    """Integration tests for TesseractProvider (skip if tesseract not installed)."""

    @pytest.mark.skipif(
        True,  # Skip by default since tesseract requires system binary
        reason="Tesseract system dependency not always available in CI"
    )
    def test_tesseract_extract_minimal_image(self):
        """TesseractProvider can extract from minimal test image."""
        try:
            from pystreampdf.ocr.providers.tesseract import TesseractProvider
            import io
            from PIL import Image, ImageDraw

            provider = TesseractProvider()

            if not provider.is_available():
                pytest.skip("Tesseract not installed")

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
            assert result.provider_name == "tesseract"
            assert result.page_number == 1

        except ImportError:
            pytest.skip("TesseractProvider or dependencies not available")
