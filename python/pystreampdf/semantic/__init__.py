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

from .assembler import AssemblyStrategy, ContextAssembler
from .citations import CitationNetwork, CitationRelation
from .entities import ConceptExtractor, Entity, EntityType
from .graph import GraphEdge, GraphNode, KnowledgeGraph
from .relationships import Relationship, RelationshipExtractor, RelationType
from .topics import Topic, TopicModel
from .verifier import FactVerifier, VerificationResult

__all__ = [
    "AssemblyStrategy",
    # Citations
    "CitationNetwork",
    "CitationRelation",
    # Entity extraction
    "ConceptExtractor",
    # Context assembly
    "ContextAssembler",
    "Entity",
    "EntityType",
    # Verification
    "FactVerifier",
    "GraphEdge",
    "GraphNode",
    # Knowledge graph
    "KnowledgeGraph",
    "RelationType",
    "Relationship",
    # Relationships
    "RelationshipExtractor",
    "Topic",
    # Topics
    "TopicModel",
    "VerificationResult",
]
