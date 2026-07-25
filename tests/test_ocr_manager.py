"""
Tests for OcrManager registry and selection.
"""

import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

import pytest
from pystreampdf.ocr import (
    OcrManager,
    OcrProvider,
    OcrResult,
    OcrCapabilities,
)


class SimpleTestProvider(OcrProvider):
    """Simple test OCR provider."""

    def __init__(self, name: str = "test", available: bool = True):
        self._name = name
        self._available = available

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
            text=f"extracted by {self._name}",
            confidence=0.95,
            provider_name=self._name,
            page_number=page_number
        )

    def is_available(self) -> bool:
        return self._available


class TestOcrManager:
    """Test OcrManager."""

    def test_manager_creation(self):
        """Create empty OcrManager."""
        manager = OcrManager()
        assert manager.available_providers() == []
        assert manager.default() is None

    def test_manager_register_provider(self):
        """Register a provider."""
        manager = OcrManager()
        provider = SimpleTestProvider("test1")
        manager.register(provider)

        assert "test1" in manager.available_providers()
        assert manager.default() is provider

    def test_manager_register_multiple(self):
        """Register multiple providers."""
        manager = OcrManager()
        p1 = SimpleTestProvider("test1")
        p2 = SimpleTestProvider("test2")
        p3 = SimpleTestProvider("test3")

        manager.register(p1)
        manager.register(p2)
        manager.register(p3)

        providers = manager.available_providers()
        assert len(providers) == 3
        assert "test1" in providers
        assert "test2" in providers
        assert "test3" in providers

    def test_manager_default_is_first(self):
        """Default is the first registered provider."""
        manager = OcrManager()
        p1 = SimpleTestProvider("first")
        p2 = SimpleTestProvider("second")

        manager.register(p1)
        manager.register(p2)

        assert manager.default() is p1
        assert manager.default().name == "first"

    def test_manager_register_wrong_type(self):
        """register() rejects non-OcrProvider objects."""
        manager = OcrManager()

        with pytest.raises(TypeError):
            manager.register("not a provider")  # type: ignore

        with pytest.raises(TypeError):
            manager.register({"name": "fake"})  # type: ignore

    def test_manager_select_provider(self):
        """Select provider by name."""
        manager = OcrManager()
        p1 = SimpleTestProvider("provider1")
        p2 = SimpleTestProvider("provider2")

        manager.register(p1)
        manager.register(p2)

        selected = manager.select("provider1")
        assert selected is p1

        selected = manager.select("provider2")
        assert selected is p2

    def test_manager_select_missing_raises_keyerror(self):
        """select() raises KeyError for missing provider."""
        manager = OcrManager()
        manager.register(SimpleTestProvider("exists"))

        with pytest.raises(KeyError) as exc_info:
            manager.select("does_not_exist")

        assert "does_not_exist" in str(exc_info.value)
        assert "Available" in str(exc_info.value)

    def test_manager_extract_with_provider_name(self):
        """extract() uses specified provider."""
        manager = OcrManager()
        p1 = SimpleTestProvider("provider1")
        p2 = SimpleTestProvider("provider2")

        manager.register(p1)
        manager.register(p2)

        result = manager.extract(b"image data", provider_name="provider2")
        assert result.provider_name == "provider2"
        assert "provider2" in result.text

    def test_manager_extract_default_provider(self):
        """extract() uses default if no provider specified."""
        manager = OcrManager()
        provider = SimpleTestProvider("default")
        manager.register(provider)

        result = manager.extract(b"image data")
        assert result.provider_name == "default"

    def test_manager_extract_no_providers_raises(self):
        """extract() raises RuntimeError if no providers registered."""
        manager = OcrManager()

        with pytest.raises(RuntimeError) as exc_info:
            manager.extract(b"image data")

        assert "No OCR providers" in str(exc_info.value)

    def test_manager_extract_invalid_provider_raises(self):
        """extract() raises KeyError for invalid provider name."""
        manager = OcrManager()
        manager.register(SimpleTestProvider("exists"))

        with pytest.raises(KeyError):
            manager.extract(b"image data", provider_name="does_not_exist")

    def test_manager_available_installed(self):
        """available_installed() filters by is_available()."""
        manager = OcrManager()
        manager.register(SimpleTestProvider("available", available=True))
        manager.register(SimpleTestProvider("unavailable", available=False))
        manager.register(SimpleTestProvider("also_available", available=True))

        installed = manager.available_installed()
        assert len(installed) == 2
        assert "available" in installed
        assert "also_available" in installed
        assert "unavailable" not in installed

    def test_manager_auto_creates_manager(self):
        """auto() creates manager with available providers."""
        # This just checks that auto() doesn't crash
        # It may or may not find installed providers depending on environment
        manager = OcrManager.auto()

        assert isinstance(manager, OcrManager)
        # Manager should be created even if empty
        assert isinstance(manager.available_providers(), list)

    def test_manager_auto_tolerates_missing_deps(self):
        """auto() doesn't crash if providers can't be imported."""
        # This would only fail if there's a bug in auto()
        # The try/except should handle any import errors gracefully
        manager = OcrManager.auto()
        assert manager is not None


class TestOcrManagerIntegration:
    """Integration tests for OcrManager."""

    def test_manager_dispatch_to_correct_provider(self):
        """Manager correctly dispatches extract() to specified provider."""
        manager = OcrManager()

        # Create providers that return different results
        class CountingProvider(OcrProvider):
            def __init__(self, name: str):
                self._name = name
                self.extract_count = 0

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
                self.extract_count += 1
                return OcrResult(
                    text=f"result from {self._name}",
                    confidence=0.9,
                    provider_name=self._name,
                    page_number=page_number
                )

        p1 = CountingProvider("provider1")
        p2 = CountingProvider("provider2")

        manager.register(p1)
        manager.register(p2)

        # Extract with p2
        result = manager.extract(b"data", provider_name="provider2")

        assert result.provider_name == "provider2"
        assert p2.extract_count == 1
        assert p1.extract_count == 0

    def test_manager_extract_batch_via_provider(self):
        """Manager can trigger extract_batch on provider."""
        manager = OcrManager()
        provider = SimpleTestProvider("batch_test")
        manager.register(provider)

        images = [
            (b"img1", 1),
            (b"img2", 2),
        ]

        results = provider.extract_batch(images)
        assert len(results) == 2
