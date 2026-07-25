"""Document graph builder - converts analysis results into structure graphs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


class NodeType(Enum):
    """Types of nodes in document graph."""
    SECTION = "section"
    FIGURE = "figure"
    TABLE = "table"
    CODE = "code"
    CONFIG = "config"
    LOG = "log"
    NARRATIVE = "narrative"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    REFERENCE = "reference"


class EdgeType(Enum):
    """Types of relationships in document graph."""
    CONTAINS = "contains"  # Parent contains child
    REFERENCES = "references"  # A references B
    ILLUSTRATED_BY = "illustrated_by"  # Section illustrated by figure
    DESCRIBED_BY = "described_by"  # Figure described by caption
    RELATED_TO = "related_to"  # General semantic relationship
    DEPENDS_ON = "depends_on"  # Code depends on library
    QUERIES = "queries"  # SQL query from section


@dataclass
class GraphNode:
    """Node in document structure graph."""

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    node_type: NodeType = NodeType.NARRATIVE
    content: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Source tracking
    source_analyzer: Optional[str] = None  # "yaml", "json", "code", etc.
    page_number: Optional[int] = None
    line_range: Optional[tuple] = None  # (start, end)

    # Intelligence metadata
    language: Optional[str] = None  # e.g., "python", "sql"
    validation_issues: List[str] = field(default_factory=list)
    corrections_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.node_type.value,
            "content": self.content[:200],  # Truncate for display
            "confidence": self.confidence,
            "source_analyzer": self.source_analyzer,
            "language": self.language,
            "validation_issues": len(self.validation_issues),
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    """Edge representing relationship between nodes."""

    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.RELATED_TO
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "confidence": self.confidence,
        }


class DocumentGraph:
    """
    Directed acyclic graph representing document structure.

    Nodes: sections, figures, tables, code blocks, configs, logs
    Edges: containment, reference, illustration, dependency
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.root_id: Optional[str] = None

    def add_node(self, node: GraphNode) -> str:
        """Add node to graph, return node ID."""
        self.nodes[node.id] = node
        return node.id

    def add_edge(self, edge: GraphEdge) -> None:
        """Add edge to graph."""
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node {edge.source_id} not in graph")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node {edge.target_id} not in graph")
        self.edges.append(edge)

    def set_root(self, node_id: str) -> None:
        """Set root node (document start)."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not in graph")
        self.root_id = node_id

    def get_children(self, node_id: str) -> List[GraphNode]:
        """Get all direct children of a node."""
        children = []
        for edge in self.edges:
            if edge.source_id == node_id and edge.edge_type == EdgeType.CONTAINS:
                children.append(self.nodes[edge.target_id])
        return children

    def get_parents(self, node_id: str) -> List[GraphNode]:
        """Get all direct parents of a node."""
        parents = []
        for edge in self.edges:
            if edge.target_id == node_id and edge.edge_type == EdgeType.CONTAINS:
                parents.append(self.nodes[edge.source_id])
        return parents

    def get_related(self, node_id: str) -> List[GraphNode]:
        """Get all related nodes (any edge type)."""
        related = set()
        for edge in self.edges:
            if edge.source_id == node_id:
                related.add(edge.target_id)
            elif edge.target_id == node_id:
                related.add(edge.source_id)
        return [self.nodes[nid] for nid in related]

    def min_confidence(self) -> float:
        """Weakest link in the graph."""
        if not self.nodes:
            return 1.0
        return min(node.confidence for node in self.nodes.values())

    def path_confidence(self, start_id: str, end_id: str) -> float:
        """
        Confidence score for path from start to end.

        Multiplies confidences along the path (weakest link matters).
        """
        # Simple implementation: breadth-first search
        from collections import deque

        visited = {start_id}
        queue = deque([(start_id, 1.0)])

        while queue:
            current_id, confidence = queue.popleft()

            if current_id == end_id:
                return confidence

            for edge in self.edges:
                if edge.source_id == current_id and edge.target_id not in visited:
                    visited.add(edge.target_id)
                    new_confidence = confidence * edge.confidence
                    queue.append((edge.target_id, new_confidence))

        return 0.0  # No path found

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "root_id": self.root_id,
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "min_confidence": self.min_confidence(),
            },
        }

    def node_count_by_type(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node in self.nodes.values():
            counts[node.node_type.value] = counts.get(node.node_type.value, 0) + 1
        return counts

    def edge_count_by_type(self) -> Dict[str, int]:
        """Count edges by type."""
        counts = {}
        for edge in self.edges:
            counts[edge.edge_type.value] = counts.get(edge.edge_type.value, 0) + 1
        return counts
