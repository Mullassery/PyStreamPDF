"""
Document structure recovery and relationship graphs.

Converts analyzed content (from Phase 5c Intelligence) into structured
knowledge graphs for Phase 5e RAG optimization.

Phases:
- Phase 5c: Intelligence analysis (YAML, JSON, Code, Log, SQL)
- Phase 5d: Structure recovery (hierarchy, relationships, formats)
- Phase 5e: RAG optimization (token budgets, retrieval ranking)
"""

from .builder import DocumentGraph, GraphNode, GraphEdge, NodeType, EdgeType
from .relationships import RelationshipExtractor, RelationType
from .recovery import StructureRecoveryEngine, DocumentMetadata, SectionHierarchy
from .exporters import (
    GraphExporter,
    MarkdownExporter,
    JSONLDExporter,
    RAGOptimizedExporter,
    SimpleJSONExporter,
)

__all__ = [
    # Graph structure
    "DocumentGraph",
    "GraphNode",
    "GraphEdge",
    "NodeType",
    "EdgeType",
    # Relationship extraction
    "RelationshipExtractor",
    "RelationType",
    # Structure recovery
    "StructureRecoveryEngine",
    "DocumentMetadata",
    "SectionHierarchy",
    # Exporters
    "GraphExporter",
    "MarkdownExporter",
    "JSONLDExporter",
    "RAGOptimizedExporter",
    "SimpleJSONExporter",
]
