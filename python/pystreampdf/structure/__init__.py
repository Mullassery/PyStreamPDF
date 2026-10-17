"""
Document structure recovery and relationship graphs.

Converts analyzed content (from Phase 5c Intelligence) into structured
knowledge graphs for Phase 5e RAG optimization.

Phases:
- Phase 5c: Intelligence analysis (YAML, JSON, Code, Log, SQL)
- Phase 5d: Structure recovery (hierarchy, relationships, formats)
- Phase 5e: RAG optimization (token budgets, retrieval ranking)
"""

from .builder import DocumentGraph, EdgeType, GraphEdge, GraphNode, NodeType
from .exporters import (
    GraphExporter,
    JSONLDExporter,
    MarkdownExporter,
    RAGOptimizedExporter,
    SimpleJSONExporter,
)
from .recovery import DocumentMetadata, SectionHierarchy, StructureRecoveryEngine
from .relationships import RelationshipExtractor, RelationType

__all__ = [
    # Graph structure
    "DocumentGraph",
    "DocumentMetadata",
    "EdgeType",
    "GraphEdge",
    # Exporters
    "GraphExporter",
    "GraphNode",
    "JSONLDExporter",
    "MarkdownExporter",
    "NodeType",
    "RAGOptimizedExporter",
    "RelationType",
    # Relationship extraction
    "RelationshipExtractor",
    "SectionHierarchy",
    "SimpleJSONExporter",
    # Structure recovery
    "StructureRecoveryEngine",
]
