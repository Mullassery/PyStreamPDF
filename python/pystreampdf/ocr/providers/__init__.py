"""OCR provider implementations."""

from .paddle import PaddleProvider
from .tesseract import TesseractProvider

__all__ = ["PaddleProvider", "TesseractProvider"]
