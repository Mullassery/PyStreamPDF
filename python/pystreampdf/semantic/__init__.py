"""Semantic understanding module for PyStreamPDF.

Transform PDF content into semantic knowledge:
- Entity extraction and classification
- Relationship detection
- Knowledge graph construction
- Citation networks
- Topic modeling and hierarchies
- Fact verification and grounding
- Intelligent context assembly
"""

from .entities import ConceptExtractor, Entity, EntityType
from .relationships import RelationshipExtractor, Relationship, RelationType
from .graph import KnowledgeGraph, GraphNode, GraphEdge
from .citations import CitationNetwork, CitationRelation
from .topics import TopicModel, Topic
from .verifier import FactVerifier, VerificationResult
from .assembler import ContextAssembler, AssemblyStrategy

__all__ = [
    # Entity extraction
    "ConceptExtractor",
    "Entity",
    "EntityType",
    # Relationships
    "RelationshipExtractor",
    "Relationship",
    "RelationType",
    # Knowledge graph
    "KnowledgeGraph",
    "GraphNode",
    "GraphEdge",
    # Citations
    "CitationNetwork",
    "CitationRelation",
    # Topics
    "TopicModel",
    "Topic",
    # Verification
    "FactVerifier",
    "VerificationResult",
    # Context assembly
    "ContextAssembler",
    "AssemblyStrategy",
]
