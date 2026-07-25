"""
RAG Optimization Layer (Phase 5e).

Transforms structured documents into retrieval-ready chunks with:
- Selective intelligence (what needs full detail vs summaries)
- Adaptive compression (technical vs narrative, lossless vs lossy)
- Retrieval metadata (scoring, density, update frequency)
- Token budgeting (adaptive allocation per chunk type)
"""

from .selector import (
    SelectiveIntelligence,
    ContentSelector,
    ContentDetail,
    SelectionPolicy,
)
from .compressor import AdaptiveCompressor, CompressionStrategy
from .chunking import ChunkingStrategy, RAGChunk, ChunkingEngine
from .metadata import RetrievalMetadata, MetadataInjector, ChunkDensity

__all__ = [
    # Selective Intelligence
    "SelectiveIntelligence",
    "ContentSelector",
    "ContentDetail",
    "SelectionPolicy",
    # Compression
    "AdaptiveCompressor",
    "CompressionStrategy",
    # Chunking
    "ChunkingStrategy",
    "RAGChunk",
    "ChunkingEngine",
    # Metadata
    "RetrievalMetadata",
    "MetadataInjector",
    "ChunkDensity",
]
