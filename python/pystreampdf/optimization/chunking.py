"""RAG-Ready Chunking: Combine selective intelligence + compression + metadata."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from .selector import SelectiveIntelligence, ContentSelector, ContentDetail
from .compressor import AdaptiveCompressor, CompressionStrategy
from .metadata import RetrievalMetadata, MetadataInjector


class ChunkingStrategy(Enum):
    """How to split document into chunks."""
    BY_SECTION = "by_section"  # One chunk per section
    BY_CONFIDENCE = "by_confidence"  # Group by confidence level
    FIXED_TOKENS = "fixed_tokens"  # Fixed token budget per chunk
    ADAPTIVE = "adaptive"  # Mix all strategies for optimal retrieval


@dataclass
class RAGChunk:
    """A chunk optimized for RAG retrieval."""

    id: str
    content: str
    metadata: RetrievalMetadata
    compression_ratio: float  # 0.1 to 1.0
    original_content_length: int

    def token_count(self) -> int:
        """Estimated tokens in this chunk."""
        return self.metadata.estimated_tokens

    def to_retrieval_format(self) -> Dict[str, Any]:
        """Format for RAG system."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }


class ChunkingEngine:
    """
    Create RAG-ready chunks using selective intelligence + compression + metadata.

    Pipeline:
    1. Input: DocumentGraph (from Phase 5d)
    2. SelectiveIntelligence: Decide detail level per node
    3. AdaptiveCompressor: Compress based on type
    4. MetadataInjector: Attach retrieval scoring
    5. Output: List[RAGChunk] sorted by relevance
    """

    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.ADAPTIVE,
        token_budget: int = 128000,  # ~100K tokens per document
    ):
        self.strategy = strategy
        self.token_budget = token_budget
        self.selector = ContentSelector(SelectiveIntelligence())
        self.compressor = AdaptiveCompressor()
        self.injector = MetadataInjector()

    def chunk_graph(
        self, graph_data: Dict[str, Any], confidence_floor: float = 0.5
    ) -> List[RAGChunk]:
        """
        Convert document graph into RAG chunks.

        Args:
            graph_data: Graph exported as dict (from DocumentGraph.to_dict())
            confidence_floor: Minimum confidence to include

        Returns:
            List of RAGChunk sorted by relevance for retrieval
        """
        chunks = []
        node_data = graph_data.get("nodes", {})

        # Convert nodes to chunks
        for node_id, node_info in node_data.items():
            if node_info.get("confidence", 1.0) < confidence_floor:
                continue

            chunk = self._node_to_chunk(
                node_id, node_info, graph_data
            )

            if chunk:
                chunks.append(chunk)

        # Sort by relevance for default retrieval order
        chunks.sort(key=lambda c: c.metadata.priority, reverse=True)

        # Enforce token budget
        chunks = self._apply_token_budget(chunks)

        return chunks

    def _node_to_chunk(
        self, node_id: str, node_info: Dict[str, Any], graph_data: Dict[str, Any]
    ) -> Optional[RAGChunk]:
        """Convert a graph node to a RAGChunk."""
        content = node_info.get("content", "")
        node_type = node_info.get("type", "narrative")
        confidence = node_info.get("confidence", 0.5)

        # Selective intelligence: decide detail level
        selection = self.selector.select_for_rag(
            node_type, confidence, len(content)
        )

        if not selection["include"]:
            return None

        # Determine compression strategy and ratio
        strategy = self.compressor.suggest_strategy(node_type, confidence)
        ratio = selection.get("compression_ratio", 1.0)

        # Compress content
        compressed = self.compressor.compress(content, strategy, ratio)

        # Inject metadata
        metadata = self.injector.inject_metadata(
            chunk_id=node_id,
            node_type=node_type,
            content=compressed,
            confidence=confidence,
            source_analyzer=node_info.get("source_analyzer"),
            content_type=node_type,
            language=node_info.get("language"),
            validation_issues=len(node_info.get("validation_issues", [])),
        )

        return RAGChunk(
            id=node_id,
            content=compressed,
            metadata=metadata,
            compression_ratio=ratio,
            original_content_length=len(content),
        )

    def _apply_token_budget(self, chunks: List[RAGChunk]) -> List[RAGChunk]:
        """Enforce token budget by truncating low-priority chunks."""
        total_tokens = sum(c.token_count() for c in chunks)

        if total_tokens <= self.token_budget:
            return chunks

        # Greedily keep high-priority chunks until budget exhausted
        selected = []
        current_tokens = 0

        for chunk in chunks:
            chunk_tokens = chunk.token_count()
            if current_tokens + chunk_tokens <= self.token_budget:
                selected.append(chunk)
                current_tokens += chunk_tokens
            else:
                # Truncate last chunk to fit
                remaining = self.token_budget - current_tokens
                if remaining > 100:  # Only keep if meaningful
                    truncated = chunk.content[: remaining * 4]  # Rough conversion
                    chunk.content = truncated
                    chunk.metadata.length = len(truncated)
                    chunk.metadata.estimated_tokens = remaining
                    selected.append(chunk)
                break

        return selected

    def explain_chunking(self, chunk: RAGChunk) -> str:
        """Generate human-readable explanation of chunking decision."""
        meta = chunk.metadata
        lines = [
            f"Chunk: {chunk.id}",
            f"Type: {meta.node_type}",
            f"Confidence: {meta.confidence:.1%}",
            f"Density: {meta.density.value}",
            f"Relevance: {meta.relevance_score:.2f}",
            f"Priority: {meta.priority:.2f}",
            f"Compression: {chunk.compression_ratio:.0%}",
            f"Tokens: {chunk.token_count()}",
        ]

        if meta.validation_issues > 0:
            lines.append(f"Issues: {meta.validation_issues}")

        if meta.corrections_applied > 0:
            lines.append(f"Corrections: {meta.corrections_applied}")

        return "\n".join(lines)
