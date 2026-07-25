"""
PaddleOCR provider implementation.

Uses PaddleOCR for multi-language text extraction.
"""

import time
from typing import List, Optional

from ..provider import OcrCapabilities, OcrProvider, OcrResult, TextRegion


class PaddleProvider(OcrProvider):
    """OCR provider using PaddleOCR."""

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        use_gpu: bool = False
    ):
        """
        Initialize PaddleOCR provider.

        Args:
            languages: List of language codes (e.g. ["en"])
                      Defaults to ["en"]. PaddleOCR supports: en, ch (Chinese), fr, de, etc.
            use_gpu: Whether to use GPU for inference
        """
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        self._ocr = None

    @property
    def name(self) -> str:
        return "paddle"

    @property
    def version(self) -> str:
        if not self.is_available():
            return "unavailable"

        try:
            import paddleocr
            return paddleocr.__version__ if hasattr(paddleocr, '__version__') else "unknown"
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

    def _init_ocr(self) -> None:
        """Lazy-initialize PaddleOCR engine on first use."""
        if self._ocr is not None:
            return

        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            raise ImportError(
                "paddleocr required for PaddleOCR extraction. "
                "Install with: pip install paddleocr"
            ) from e

        try:
            lang_str = self.languages[0] if self.languages else "en"
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang_str,
                use_gpu=self.use_gpu
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize PaddleOCR: {e}") from e

    def extract(self, image_data: bytes, page_number: Optional[int] = None) -> OcrResult:
        """
        Extract text from image using PaddleOCR.

        Args:
            image_data: Image bytes (PNG, JPEG, etc.)
            page_number: Optional page number for tracking

        Returns:
            OcrResult

        Raises:
            ImportError: If paddleocr not installed
            ValueError: If image data is invalid or extraction fails
        """
        try:
            import io
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "pillow required for image processing. "
                "Install with: pip install pillow"
            ) from e

        # Initialize OCR engine
        self._init_ocr()

        start_time = time.time()

        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed (RGBA, grayscale, etc.)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Convert PIL image to numpy array for PaddleOCR
            import numpy as np
            img_array = np.array(image)

            # Extract text with PaddleOCR
            result = self._ocr.ocr(img_array, cls=True)

            # PaddleOCR returns: list[list[(x1,y1,x2,y2,x3,y3,x4,y4), (text, confidence)]]
            # One inner list per detected text line

            full_text = []
            regions = []
            all_confidences = []

            for line in result:
                if not line:
                    continue

                for detection in line:
                    bbox_4points = detection[0]  # 4 corner points
                    text = detection[1]
                    confidence = float(detection[2])

                    full_text.append(text)
                    all_confidences.append(confidence)

                    # Convert 4-corner bbox to (x, y, w, h)
                    x_coords = [p[0] for p in bbox_4points]
                    y_coords = [p[1] for p in bbox_4points]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)

                    regions.append(
                        TextRegion(
                            text=text,
                            confidence=confidence,
                            bbox=(
                                int(x_min),
                                int(y_min),
                                int(x_max - x_min),
                                int(y_max - y_min)
                            ),
                            language=self.languages[0] if self.languages else None
                        )
                    )

            text = " ".join(full_text)
            overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5

            processing_time = (time.time() - start_time) * 1000  # ms

            return OcrResult(
                text=text,
                confidence=overall_confidence,
                regions=regions,
                provider_name=self.name,
                page_number=page_number,
                processing_time_ms=processing_time,
                metadata={
                    "language": self.languages[0] if self.languages else "en",
                    "region_count": len(regions),
                    "use_gpu": self.use_gpu
                }
            )

        except Exception as e:
            if isinstance(e, (ImportError, ValueError)):
                raise
            raise ValueError(f"Failed to extract text with PaddleOCR: {e}") from e

    def is_available(self) -> bool:
        """
        Check if PaddleOCR is installed and available.

        Returns:
            True if paddleocr can be imported and initialized
        """
        try:
            import paddleocr  # noqa: F401
            # Try to initialize to ensure models can be downloaded
            self._init_ocr()
            return True
        except Exception:
            return False
