"""
RAG Optimization Layer (Phase 5e).

Transforms structured documents into retrieval-ready chunks with:
- Selective intelligence (what needs full detail vs summaries)
- Adaptive compression (technical vs narrative, lossless vs lossy)
- Retrieval metadata (scoring, density, update frequency)
- Token budgeting (adaptive allocation per chunk type)
"""

from .chunking import ChunkingEngine, ChunkingStrategy, RAGChunk
from .compressor import AdaptiveCompressor, CompressionStrategy
from .metadata import ChunkDensity, MetadataInjector, RetrievalMetadata
from .selector import (
    ContentDetail,
    ContentSelector,
    SelectionPolicy,
    SelectiveIntelligence,
)

__all__ = [
    # Compression
    "AdaptiveCompressor",
    "ChunkDensity",
    "ChunkingEngine",
    # Chunking
    "ChunkingStrategy",
    "CompressionStrategy",
    "ContentDetail",
    "ContentSelector",
    "MetadataInjector",
    "RAGChunk",
    # Metadata
    "RetrievalMetadata",
    "SelectionPolicy",
    # Selective Intelligence
    "SelectiveIntelligence",
]
