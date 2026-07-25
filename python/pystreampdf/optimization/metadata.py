"""Retrieval Metadata: Tags and scoring for RAG systems."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class ChunkDensity(Enum):
    """Information density of chunk."""
    VERY_HIGH = "very_high"  # Multiple concepts per sentence
    HIGH = "high"  # Clear, structured information
    MEDIUM = "medium"  # Some redundancy, filler
    LOW = "low"  # Lots of filler, sparse information


@dataclass
class RetrievalMetadata:
    """Metadata for retrieval ranking and filtering."""

    # Identification
    chunk_id: str
    node_type: str  # "code", "config", "narrative", "section", etc.
    content_type: str  # More specific: "python", "yaml", "markdown", etc.

    # Quality signals
    confidence: float  # 0.0-1.0 from Phase 5c analysis
    density: ChunkDensity  # Information density
    length: int  # Character count after compression
    estimated_tokens: int  # Approximate token count

    # Ranking signals
    relevance_score: float  # Combined score for ranking
    priority: float  # 0.0-1.0: should include in RAG early
    update_frequency: str  # "stable", "frequent", "dynamic" (hint for cache strategy)

    # Source tracking
    source_analyzer: Optional[str] = None  # "yaml", "code", "sql", etc.
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    language: Optional[str] = None  # For code: "python", "sql"; for docs: "en"

    # Relationships
    related_chunk_ids: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)  # Prerequisite chunks
    referenced_by: List[str] = field(default_factory=list)  # Chunks that cite this

    # Filtering metadata
    tags: List[str] = field(default_factory=list)  # For semantic filtering
    validation_issues: int = 0  # Number of issues detected
    corrections_applied: int = 0  # OCR/analysis corrections made

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "chunk_id": self.chunk_id,
            "node_type": self.node_type,
            "content_type": self.content_type,
            "confidence": self.confidence,
            "density": self.density.value,
            "length": self.length,
            "estimated_tokens": self.estimated_tokens,
            "relevance_score": self.relevance_score,
            "priority": self.priority,
            "update_frequency": self.update_frequency,
            "source_analyzer": self.source_analyzer,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "language": self.language,
            "related_chunk_ids": self.related_chunk_ids,
            "tags": self.tags,
            "validation_issues": self.validation_issues,
        }


class MetadataInjector:
    """Inject retrieval metadata into chunks for RAG optimization."""

    @staticmethod
    def estimate_density(content: str) -> ChunkDensity:
        """Estimate information density of content."""
        if not content:
            return ChunkDensity.LOW

        lines = content.strip().split("\n")
        non_empty_lines = [l for l in lines if l.strip()]

        if not non_empty_lines:
            return ChunkDensity.LOW

        avg_line_length = sum(len(l) for l in non_empty_lines) / len(non_empty_lines)

        # Heuristics:
        # - Long lines (code, structured): HIGH
        # - Short lines (sparse): LOW
        # - Code/config keywords: HIGH
        if avg_line_length > 60:
            density = ChunkDensity.HIGH
        elif avg_line_length > 40:
            density = ChunkDensity.MEDIUM
        else:
            density = ChunkDensity.LOW

        # Boost if structured (contains special chars like {}, [], :, =)
        special_char_count = sum(1 for c in content if c in "{}[]:=")
        if special_char_count > len(content) * 0.02:
            density = ChunkDensity.HIGH

        return density

    @staticmethod
    def calculate_relevance(
        confidence: float,
        density: ChunkDensity,
        content_length: int,
        importance: float = 0.5,
    ) -> float:
        """
        Calculate combined relevance score for ranking.

        Factors:
        - Confidence (0.0-1.0): how certain are we about the content?
        - Density: high-density chunks are more valuable
        - Length: but not too long (diminishing returns)
        - Importance: domain-specific importance weighting
        """
        # Base score from confidence
        score = confidence * 0.6

        # Boost for density
        density_weights = {
            ChunkDensity.VERY_HIGH: 1.2,
            ChunkDensity.HIGH: 1.0,
            ChunkDensity.MEDIUM: 0.8,
            ChunkDensity.LOW: 0.6,
        }
        score *= density_weights[density]

        # Slight boost for reasonable length (not too short, not too long)
        # Optimal: 500-2000 chars
        if 500 <= content_length <= 2000:
            score *= 1.1
        elif content_length < 100:
            score *= 0.7  # Too short
        elif content_length > 5000:
            score *= 0.8  # Too long

        # Apply importance weighting
        score *= (1.0 - importance * 0.3)  # Importance modulates the score

        return min(1.0, score)

    @staticmethod
    def inject_metadata(
        chunk_id: str,
        node_type: str,
        content: str,
        confidence: float,
        source_analyzer: Optional[str] = None,
        **kwargs,
    ) -> RetrievalMetadata:
        """
        Inject metadata into a chunk.

        Args:
            chunk_id: Unique chunk identifier
            node_type: Type of node (code, config, narrative, etc.)
            content: Chunk content
            confidence: Confidence score (0.0-1.0)
            source_analyzer: Which analyzer produced this (yaml, code, sql, etc.)
            **kwargs: Additional metadata fields

        Returns:
            RetrievalMetadata with calculated scores
        """
        density = MetadataInjector.estimate_density(content)
        length = len(content)
        estimated_tokens = int(length / 4)  # Rough estimate: 1 token ≈ 4 chars

        # Map node_type to content_type if not provided
        content_type = kwargs.get("content_type", source_analyzer or node_type)

        importance = kwargs.get("importance", 0.5)
        relevance = MetadataInjector.calculate_relevance(
            confidence, density, length, importance
        )

        # Determine priority for retrieval order
        priority = relevance * confidence

        # Determine update frequency based on content type
        update_freq_map = {
            "code": "stable",
            "config": "stable",
            "log": "dynamic",
            "data": "frequent",
            "narrative": "stable",
        }
        update_frequency = update_freq_map.get(source_analyzer, "stable")

        return RetrievalMetadata(
            chunk_id=chunk_id,
            node_type=node_type,
            content_type=content_type,
            confidence=confidence,
            density=density,
            length=length,
            estimated_tokens=estimated_tokens,
            relevance_score=relevance,
            priority=priority,
            update_frequency=update_frequency,
            source_analyzer=source_analyzer,
            page_number=kwargs.get("page_number"),
            section_title=kwargs.get("section_title"),
            language=kwargs.get("language"),
            tags=kwargs.get("tags", []),
            validation_issues=kwargs.get("validation_issues", 0),
            corrections_applied=kwargs.get("corrections_applied", 0),
        )
