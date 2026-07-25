"""Adaptive Compression: Technical (lossless) vs Narrative (lossy)."""

from enum import Enum
from typing import Optional
import re


class CompressionStrategy(Enum):
    """How to compress content."""
    LOSSLESS = "lossless"  # Preserve structure (code, config, tables)
    LOSSY = "lossy"  # Summarize, remove redundancy (narrative)
    NONE = "none"  # No compression


class AdaptiveCompressor:
    """
    Compress content based on type and target ratio.

    - Technical: Preserve syntax and structure
    - Narrative: Remove redundancy, summarize
    """

    def compress(
        self, content: str, strategy: CompressionStrategy, target_ratio: float = 0.5
    ) -> str:
        """
        Compress content to target ratio.

        Args:
            content: Text to compress
            strategy: LOSSLESS (preserve structure) or LOSSY (summarize)
            target_ratio: Target size (0.1 = 10% of original, 1.0 = no compression)

        Returns:
            Compressed content
        """
        if strategy == CompressionStrategy.NONE or target_ratio >= 1.0:
            return content

        if strategy == CompressionStrategy.LOSSLESS:
            return self._compress_lossless(content, target_ratio)
        else:  # LOSSY
            return self._compress_lossy(content, target_ratio)

    def _compress_lossless(self, content: str, target_ratio: float) -> str:
        """Preserve structure, remove only whitespace and comments."""
        lines = content.split("\n")
        compressed = []

        for line in lines:
            stripped = line.strip()

            # Keep non-empty, non-comment lines
            if stripped and not stripped.startswith("#"):
                # Remove trailing comments (but keep inline logic)
                if " #" in stripped and not "http" in stripped:
                    stripped = stripped.split(" #")[0].strip()

                compressed.append(stripped)

        # Join with minimal whitespace
        result = "\n".join(compressed)

        # If still too long, trim from end
        if len(result) > len(content) * target_ratio:
            max_len = int(len(content) * target_ratio)
            result = result[:max_len] + "..."

        return result

    def _compress_lossy(self, content: str, target_ratio: float) -> str:
        """Summarize narrative: extract key sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", content)

        if not sentences:
            return content

        # Score sentences by keyword presence
        keywords = {"important", "critical", "key", "significant", "result", "conclusion"}
        scored = []

        for sent in sentences:
            score = sum(1 for kw in keywords if kw in sent.lower())
            scored.append((score, sent))

        # Sort by score, keep top N to reach target ratio
        scored.sort(reverse=True)
        target_count = max(1, int(len(sentences) * target_ratio))
        kept = sorted(scored[:target_count], key=lambda x: sentences.index(x[1]))

        result = " ".join(s[1] for s in kept)

        # If still too long, truncate
        if len(result) > len(content) * target_ratio:
            max_len = int(len(content) * target_ratio)
            result = result[:max_len] + "..."

        return result

    def suggest_strategy(self, content_type: str, confidence: float) -> CompressionStrategy:
        """
        Suggest compression strategy based on content type.

        Args:
            content_type: "code", "config", "log", "narrative", "table", etc.
            confidence: Confidence score (0.0-1.0)

        Returns:
            Recommended CompressionStrategy
        """
        # Technical content: always lossless
        if content_type in ["code", "config", "log", "sql", "yaml", "json"]:
            return CompressionStrategy.LOSSLESS

        # High confidence: preserve; low confidence: compress
        if confidence >= 0.8:
            return CompressionStrategy.LOSSLESS
        elif confidence >= 0.5:
            return CompressionStrategy.LOSSY
        else:
            return CompressionStrategy.LOSSY

    def suggest_ratio(self, confidence: float, importance: float = 0.5) -> float:
        """
        Suggest compression ratio.

        Args:
            confidence: Confidence score (0.0-1.0)
            importance: Importance score (0.0-1.0)

        Returns:
            Compression ratio (0.1 to 1.0)
        """
        # High confidence + importance: minimal compression
        # Low confidence: aggressive compression

        combined_score = (confidence * 0.7) + (importance * 0.3)

        if combined_score >= 0.9:
            return 1.0  # No compression
        elif combined_score >= 0.7:
            return 0.7  # 70% retained
        elif combined_score >= 0.5:
            return 0.5  # 50% retained
        elif combined_score >= 0.3:
            return 0.3  # 30% retained
        else:
            return 0.1  # 10% retained (heavy compression)
