"""
Tesseract OCR provider implementation.

Uses pytesseract and Pillow for text extraction from images.
"""

import time
from typing import List, Optional

from ..provider import OcrCapabilities, OcrProvider, OcrResult, TextRegion


class TesseractProvider(OcrProvider):
    """OCR provider using Tesseract via pytesseract."""

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        config: str = "",
        tesseract_cmd: Optional[str] = None
    ):
        """
        Initialize Tesseract provider.

        Args:
            languages: List of language codes (e.g. ["eng", "fra"])
            config: Tesseract config string (e.g. "--psm 3")
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        self.languages = languages or ["eng"]
        self.config = config
        self.tesseract_cmd = tesseract_cmd

    @property
    def name(self) -> str:
        return "tesseract"

    @property
    def version(self) -> str:
        if not self.is_available():
            return "unavailable"

        try:
            import pytesseract
            version_str = pytesseract.get_tesseract_version()
            # Extract version number (usually "tesseract 4.1.1\n...")
            if version_str:
                return version_str.split()[1] if len(version_str.split()) > 1 else "unknown"
        except Exception:
            pass
        return "unknown"

    @property
    def capabilities(self) -> OcrCapabilities:
        return OcrCapabilities(
            supports_handwriting=False,
            supports_tables=False,
            supports_formulas=False,
            supported_languages=self.languages
        )

    def extract(self, image_data: bytes, page_number: Optional[int] = None) -> OcrResult:
        """
        Extract text from image using Tesseract.

        Args:
            image_data: Image bytes (PNG, JPEG, etc.)
            page_number: Optional page number for tracking

        Returns:
            OcrResult

        Raises:
            ImportError: If pytesseract or Pillow not installed
            ValueError: If image data is invalid
        """
        try:
            import pytesseract
            from PIL import Image
            import io
        except ImportError as e:
            raise ImportError(
                "pytesseract and pillow required for Tesseract OCR. "
                "Install with: pip install pytesseract pillow"
            ) from e

        if self.tesseract_cmd:
            pytesseract.pytesseract.pytesseract_cmd = self.tesseract_cmd

        start_time = time.time()

        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))

            # Extract full text
            lang = "+".join(self.languages) if self.languages else "eng"
            text = pytesseract.image_to_string(image, lang=lang, config=self.config)

            # Extract per-word data with bounding boxes and confidence
            data = pytesseract.image_to_data(image, lang=lang, config=self.config, output_type=pytesseract.Output.DICT)

            # Build text regions
            regions = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():  # Skip empty words
                    word_conf = int(data["conf"][i])
                    if word_conf >= 0:  # -1 means invalid/skipped
                        regions.append(
                            TextRegion(
                                text=data["text"][i],
                                confidence=word_conf / 100.0,  # Convert from 0-100 to 0-1
                                bbox=(
                                    int(data["left"][i]),
                                    int(data["top"][i]),
                                    int(data["width"][i]),
                                    int(data["height"][i])
                                ),
                                language=lang
                            )
                        )

            # Calculate overall confidence
            confidences = [r.confidence for r in regions] if regions else [0.5]
            overall_confidence = sum(confidences) / len(confidences)

            processing_time = (time.time() - start_time) * 1000  # ms

            return OcrResult(
                text=text,
                confidence=overall_confidence,
                regions=regions,
                provider_name=self.name,
                page_number=page_number,
                processing_time_ms=processing_time,
                metadata={
                    "language": lang,
                    "region_count": len(regions),
                    "config": self.config
                }
            )

        except Exception as e:
            if isinstance(e, ImportError):
                raise
            raise ValueError(f"Failed to extract text with Tesseract: {e}") from e

    def is_available(self) -> bool:
        """
        Check if Tesseract is installed and available.

        Returns:
            True if tesseract executable can be found and used
        """
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
