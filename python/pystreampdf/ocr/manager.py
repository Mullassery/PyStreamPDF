"""
OCR Manager for provider registration and selection.

Provides a registry for OCR providers and handles dispatch to the appropriate provider.
"""

from typing import Dict, List, Optional
from .provider import OcrProvider, OcrResult


class OcrManager:
    """
    Registry and dispatcher for OCR providers.

    Allows registration of providers, selection by name, and extraction via a specific provider.
    """

    def __init__(self):
        """Initialize an empty manager."""
        self._providers: Dict[str, OcrProvider] = {}
        self._default_provider: Optional[str] = None

    def register(self, provider: OcrProvider) -> None:
        """
        Register an OCR provider.

        Args:
            provider: OcrProvider instance

        Raises:
            TypeError: If provider is not an OcrProvider
        """
        if not isinstance(provider, OcrProvider):
            raise TypeError(f"provider must be OcrProvider, got {type(provider)}")

        self._providers[provider.name] = provider

        # Set as default if first provider
        if self._default_provider is None:
            self._default_provider = provider.name

    def select(self, name: str) -> OcrProvider:
        """
        Select a provider by name.

        Args:
            name: Provider name

        Returns:
            OcrProvider instance

        Raises:
            KeyError: If provider not registered
        """
        if name not in self._providers:
            available = list(self._providers.keys())
            raise KeyError(
                f"OCR provider '{name}' not registered. Available: {available}"
            )
        return self._providers[name]

    def default(self) -> Optional[OcrProvider]:
        """
        Get the default provider (first registered).

        Returns:
            OcrProvider or None if no providers registered
        """
        if self._default_provider is None:
            return None
        return self._providers.get(self._default_provider)

    def available_providers(self) -> List[str]:
        """Get list of all registered provider names."""
        return list(self._providers.keys())

    def available_installed(self) -> List[str]:
        """Get list of registered providers that are available (dependencies installed)."""
        return [name for name, p in self._providers.items() if p.is_available()]

    def extract(
        self, image_data: bytes, provider_name: Optional[str] = None, page_number: Optional[int] = None
    ) -> OcrResult:
        """
        Extract text using a specific provider (or default).

        Args:
            image_data: Image bytes
            provider_name: Provider to use (defaults to first registered)
            page_number: Optional page number for tracking

        Returns:
            OcrResult

        Raises:
            KeyError: If provider_name not registered
            RuntimeError: If no providers registered
        """
        if provider_name is None:
            provider = self.default()
            if provider is None:
                raise RuntimeError("No OCR providers registered")
        else:
            provider = self.select(provider_name)

        return provider.extract(image_data, page_number)

    @classmethod
    def auto(cls) -> "OcrManager":
        """
        Auto-create a manager and register all available installed providers.

        Tries to import and instantiate each known provider.
        Safe to call even if no providers are installed.

        Returns:
            OcrManager with any available providers registered
        """
        manager = cls()

        # Try to register Tesseract
        try:
            from .providers.tesseract import TesseractProvider
            provider = TesseractProvider()
            if provider.is_available():
                manager.register(provider)
        except (ImportError, Exception):
            pass

        # Try to register PaddleOCR
        try:
            from .providers.paddle import PaddleProvider
            provider = PaddleProvider()
            if provider.is_available():
                manager.register(provider)
        except (ImportError, Exception):
            pass

        return manager
