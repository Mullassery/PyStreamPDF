"""Knowledge graph for semantic understanding.

Construct and query knowledge graphs from extracted entities and relationships.
Supports in-memory storage with BFS/DFS traversal and graph analytics.
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict


@dataclass
class GraphNode:
    """Node in knowledge graph."""
    id: str
    label: str
    node_type: str  # person, organization, method, concept, etc.
    properties: Dict = field(default_factory=dict)
    frequency: int = 1  # How many times referenced
    in_degree: int = 0  # Number of incoming edges
    out_degree: int = 0  # Number of outgoing edges


@dataclass
class GraphEdge:
    """Edge in knowledge graph."""
    source: str
    target: str
    relation_type: str
    confidence: float = 1.0
    weight: float = 1.0  # For ranking (confidence-based)
    properties: Dict = field(default_factory=dict)


class KnowledgeGraph:
    """Graph structure for knowledge representation.

    Features:
    - Add nodes (entities) and edges (relationships)
    - Query neighbors at varying depths
    - Find shortest paths between nodes
    - Calculate node influence/importance
    - Export graph structure
    - Find strongly related concepts
    """

    def __init__(self):
        """Initialize knowledge graph."""
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[Tuple[str, str], GraphEdge] = {}  # (source, target) -> edge
        self.adjacency: Dict[str, List[Tuple[str, GraphEdge]]] = defaultdict(list)  # source -> [(target, edge)]
        self.reverse_adjacency: Dict[str, List[Tuple[str, GraphEdge]]] = defaultdict(list)  # target -> [(source, edge)]

    def add_node(self, node_id: str, label: str, node_type: str, **properties) -> GraphNode:
        """Add node to graph.

        Args:
            node_id: Unique node identifier
            label: Human-readable label
            node_type: Type of node (method, concept, person, etc.)
            **properties: Additional properties

        Returns:
            Created node
        """
        node_id = node_id.lower()  # Normalize

        if node_id in self.nodes:
            self.nodes[node_id].frequency += 1
            return self.nodes[node_id]

        node = GraphNode(
            id=node_id,
            label=label,
            node_type=node_type,
            properties=properties,
        )
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        confidence: float = 1.0,
        **properties,
    ) -> GraphEdge:
        """Add edge to graph.

        Args:
            source: Source node ID
            target: Target node ID
            relation: Relationship type
            confidence: Confidence score (0-1)
            **properties: Additional properties

        Returns:
            Created edge
        """
        source = source.lower()
        target = target.lower()

        # Ensure nodes exist
        if source not in self.nodes:
            self.add_node(source, source, "unknown")
        if target not in self.nodes:
            self.add_node(target, target, "unknown")

        # Check if edge already exists
        edge_key = (source, target)
        if edge_key in self.edges:
            # Update existing edge
            self.edges[edge_key].confidence = max(self.edges[edge_key].confidence, confidence)
            return self.edges[edge_key]

        # Create new edge
        edge = GraphEdge(
            source=source,
            target=target,
            relation_type=relation,
            confidence=confidence,
            weight=confidence,  # Use confidence as weight
            properties=properties,
        )

        self.edges[edge_key] = edge
        self.adjacency[source].append((target, edge))
        self.reverse_adjacency[target].append((source, edge))

        # Update degree counts
        self.nodes[source].out_degree += 1
        self.nodes[target].in_degree += 1

        return edge

    def query(self, node_id: str, depth: int = 1) -> Dict[str, List[Tuple[str, float]]]:
        """Query neighbors of a node up to specified depth.

        Args:
            node_id: Node to query
            depth: Search depth (1 = immediate neighbors)

        Returns:
            Dict mapping relation types to list of (node_id, confidence) tuples
        """
        node_id = node_id.lower()

        if node_id not in self.nodes:
            return {}

        results = defaultdict(list)
        visited = {node_id}
        queue = deque([(node_id, 0)])  # (node, current_depth)

        while queue:
            current, current_depth = queue.popleft()

            if current_depth >= depth:
                continue

            # Get neighbors
            for neighbor, edge in self.adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    results[edge.relation_type].append((neighbor, edge.confidence))
                    queue.append((neighbor, current_depth + 1))

        return dict(results)

    def find_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two nodes using BFS.

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            List of node IDs forming shortest path, or None if no path exists
        """
        source = source.lower()
        target = target.lower()

        if source not in self.nodes or target not in self.nodes:
            return None

        if source == target:
            return [source]

        visited = {source}
        queue = deque([(source, [source])])

        while queue:
            current, path = queue.popleft()

            for neighbor, _ in self.adjacency[current]:
                if neighbor == target:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def find_similar(self, node_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Find most similar/related nodes using shared neighbors.

        Args:
            node_id: Reference node
            top_k: Number of results to return

        Returns:
            List of (node_id, similarity_score) sorted by similarity
        """
        node_id = node_id.lower()

        if node_id not in self.nodes:
            return []

        # Get neighbors of reference node
        ref_neighbors = set(neighbor for neighbor, _ in self.adjacency[node_id])

        # Calculate similarity to other nodes
        similarities = []
        for other_id in self.nodes:
            if other_id == node_id:
                continue

            other_neighbors = set(neighbor for neighbor, _ in self.adjacency[other_id])

            # Jaccard similarity: intersection / union
            if len(ref_neighbors | other_neighbors) == 0:
                similarity = 0.0
            else:
                intersection = len(ref_neighbors & other_neighbors)
                union = len(ref_neighbors | other_neighbors)
                similarity = intersection / union

            if similarity > 0:
                similarities.append((other_id, similarity))

        # Return top K sorted by similarity
        return sorted(similarities, key=lambda x: -x[1])[:top_k]

    def calculate_influence(self) -> Dict[str, float]:
        """Calculate influence score for each node (PageRank-like).

        Returns:
            Dict mapping node IDs to influence scores (0-1)
        """
        # Simple influence based on in-degree and edge weights
        scores = {}

        for node_id in self.nodes:
            in_edges = self.reverse_adjacency[node_id]
            if not in_edges:
                scores[node_id] = 0.0
            else:
                # Sum of incoming edge weights
                total_weight = sum(edge.weight for _, edge in in_edges)
                # Normalize
                scores[node_id] = min(1.0, total_weight / len(self.nodes))

        # Normalize scores to 0-1 range
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {k: v / max_score for k, v in scores.items()}

        return scores

    def get_node_stats(self, node_id: str) -> Dict:
        """Get detailed statistics for a node.

        Args:
            node_id: Node ID

        Returns:
            Dict with node statistics
        """
        node_id = node_id.lower()

        if node_id not in self.nodes:
            return {}

        node = self.nodes[node_id]
        influence = self.calculate_influence()

        return {
            "id": node.id,
            "label": node.label,
            "type": node.node_type,
            "frequency": node.frequency,
            "in_degree": node.in_degree,
            "out_degree": node.out_degree,
            "influence_score": influence.get(node_id, 0.0),
            "neighbors": len(self.adjacency[node_id]),
        }

    def to_dict(self) -> Dict:
        """Export graph as dictionary.

        Returns:
            Dict with nodes and edges
        """
        return {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "type": node.node_type,
                    "frequency": node.frequency,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation_type,
                    "confidence": edge.confidence,
                }
                for edge in self.edges.values()
            ],
        }

    def get_subgraph(self, nodes: List[str]) -> "KnowledgeGraph":
        """Extract subgraph containing specified nodes and their relationships.

        Args:
            nodes: List of node IDs to include

        Returns:
            New KnowledgeGraph containing the subgraph
        """
        subgraph = KnowledgeGraph()

        # Normalize node IDs
        nodes = [n.lower() for n in nodes]

        # Add nodes
        for node_id in nodes:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                subgraph.add_node(node.id, node.label, node.node_type, **node.properties)

        # Add edges between nodes
        for (source, target), edge in self.edges.items():
            if source in nodes and target in nodes:
                subgraph.add_edge(
                    source,
                    target,
                    edge.relation_type,
                    edge.confidence,
                    **edge.properties,
                )

        return subgraph

    def merge(self, other: "KnowledgeGraph") -> None:
        """Merge another graph into this one.

        Args:
            other: KnowledgeGraph to merge
        """
        # Add all nodes
        for node in other.nodes.values():
            if node.id in self.nodes:
                self.nodes[node.id].frequency += node.frequency
            else:
                self.add_node(node.id, node.label, node.node_type, **node.properties)

        # Add all edges
        for edge in other.edges.values():
            self.add_edge(
                edge.source,
                edge.target,
                edge.relation_type,
                edge.confidence,
                **edge.properties,
            )
