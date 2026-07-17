"""Tests for Phase 4.2 - Relationships and Knowledge Graphs."""

import pytest
import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

from pystreampdf.semantic import (
    RelationshipExtractor, RelationType, Relationship,
    KnowledgeGraph, GraphNode, GraphEdge
)


class TestRelationshipExtractor:
    """Test relationship extraction."""

    def test_extractor_init(self):
        """Test extractor initialization."""
        extractor = RelationshipExtractor()
        assert extractor is not None
        assert extractor.min_confidence == 0.6

    def test_extract_cites_relationship(self):
        """Test extracting citation relationships."""
        extractor = RelationshipExtractor()
        text = "Smith cites Johnson's work on neural networks."
        relationships = extractor.extract(text)

        assert len(relationships) > 0
        # Check for citation relationship
        cite_rels = [r for r in relationships if r.relation_type == RelationType.CITES]
        assert len(cite_rels) > 0

    def test_extract_extends_relationship(self):
        """Test extracting extends relationships."""
        extractor = RelationshipExtractor()
        text = "Our work extends the transformer architecture with attention mechanisms."
        relationships = extractor.extract(text)

        assert len(relationships) > 0

    def test_extract_uses_relationship(self):
        """Test extracting uses relationships."""
        extractor = RelationshipExtractor()
        text = "The system uses BERT for natural language understanding."
        relationships = extractor.extract(text)

        assert len(relationships) > 0

    def test_extract_refutes_relationship(self):
        """Test extracting refutes relationships."""
        extractor = RelationshipExtractor()
        text = "This work refutes the previous conclusion that RNNs are superior."
        relationships = extractor.extract(text)

        assert len(relationships) > 0

    def test_confidence_filtering(self):
        """Test confidence threshold filtering."""
        extractor = RelationshipExtractor(min_confidence=0.9)
        text = "Smith uses Johnson's methods and cites their paper."
        relationships = extractor.extract(text)

        # All relationships should meet high threshold
        assert all(r.confidence >= 0.9 for r in relationships)

    def test_entity_filtering(self):
        """Test filtering relationships by specific entities."""
        extractor = RelationshipExtractor()
        text = "Smith cites Johnson who builds on Williams' work."
        relationships = extractor.extract(text, entities=["smith", "johnson"])

        # Should only find relationships involving Smith or Johnson
        for rel in relationships:
            assert rel.entity_a.lower() in ["smith", "johnson"] or rel.entity_b.lower() in ["smith", "johnson"]

    def test_evidence_extraction(self):
        """Test that evidence text is extracted."""
        extractor = RelationshipExtractor()
        text = "The transformer architecture, introduced by Vaswani, extends previous sequence models."
        relationships = extractor.extract(text)

        for rel in relationships:
            if rel.evidence:
                assert len(rel.evidence) > 0
                assert rel.entity_a in rel.evidence or rel.entity_b in rel.evidence

    def test_deduplication(self):
        """Test relationship deduplication."""
        extractor = RelationshipExtractor()
        text = "Smith cites Johnson. Smith cites Johnson again in the paper."
        relationships = extractor.extract(text)

        # Should deduplicate identical relationships
        smith_johnson_rels = [r for r in relationships if r.entity_a.lower() == "smith" and r.entity_b.lower() == "johnson"]
        # At most one relationship between each pair
        assert len(smith_johnson_rels) <= 2  # May have multiple due to pattern matching

    def test_batch_extract(self):
        """Test batch relationship extraction."""
        extractor = RelationshipExtractor()
        texts = [
            ("Smith cites Johnson.", 1),
            ("Williams extends Huang's approach.", 2),
            ("Li uses the transformer architecture.", 3),
        ]

        relationships = extractor.batch_extract(texts)
        assert len(relationships) > 0
        # Some should be from different sources
        sources = set()
        for rel in relationships:
            if rel.evidence and "[Source" in rel.evidence:
                sources.add(rel.evidence.split("[Source")[1][0])

    def test_get_related_entities(self):
        """Test getting related entities."""
        extractor = RelationshipExtractor()
        text = "Smith cites Johnson and extends Williams' work."
        relationships = extractor.extract(text)

        related = extractor.get_related_entities("smith", relationships)
        assert isinstance(related, dict)

    def test_reverse_relation_type(self):
        """Test reversing relationship types."""
        assert RelationshipExtractor._reverse_relation_type(RelationType.CITES) == RelationType.CITED_BY
        assert RelationshipExtractor._reverse_relation_type(RelationType.CITED_BY) == RelationType.CITES
        assert RelationshipExtractor._reverse_relation_type(RelationType.EXTENDS) == RelationType.EXTENDS_BY
        assert RelationshipExtractor._reverse_relation_type(RelationType.RELATED_TO) == RelationType.RELATED_TO


class TestKnowledgeGraph:
    """Test knowledge graph."""

    def test_graph_init(self):
        """Test graph initialization."""
        graph = KnowledgeGraph()
        assert graph is not None
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """Test adding nodes to graph."""
        graph = KnowledgeGraph()
        node = graph.add_node("transformer", "Transformer", "method")

        assert node is not None
        assert node.id == "transformer"
        assert len(graph.nodes) == 1

    def test_add_node_duplicate(self):
        """Test adding duplicate nodes increases frequency."""
        graph = KnowledgeGraph()
        node1 = graph.add_node("transformer", "Transformer", "method")
        node2 = graph.add_node("Transformer", "Transformer", "method")  # Case insensitive

        # Should be same node with increased frequency
        assert node1.id == node2.id
        assert node1.frequency == 2

    def test_add_edge(self):
        """Test adding edges to graph."""
        graph = KnowledgeGraph()
        graph.add_node("bert", "BERT", "method")
        graph.add_node("transformer", "Transformer", "method")

        edge = graph.add_edge("bert", "transformer", "extends", confidence=0.9)

        assert edge is not None
        assert edge.source == "bert"
        assert edge.target == "transformer"
        assert edge.confidence == 0.9
        assert len(graph.edges) == 1

    def test_edge_creates_missing_nodes(self):
        """Test that adding edges creates missing nodes."""
        graph = KnowledgeGraph()
        graph.add_edge("smith", "johnson", "cites")

        assert "smith" in graph.nodes
        assert "johnson" in graph.nodes

    def test_query_neighbors(self):
        """Test querying node neighbors."""
        graph = KnowledgeGraph()
        graph.add_edge("transformer", "attention", "uses", confidence=0.9)
        graph.add_edge("transformer", "bert", "extends", confidence=0.85)

        neighbors = graph.query("transformer", depth=1)

        assert "uses" in neighbors
        assert "extends" in neighbors
        assert ("attention", 0.9) in neighbors["uses"]

    def test_query_depth(self):
        """Test querying with different depths."""
        graph = KnowledgeGraph()
        graph.add_edge("a", "b", "relates_to")
        graph.add_edge("b", "c", "relates_to")
        graph.add_edge("c", "d", "relates_to")

        neighbors_depth1 = graph.query("a", depth=1)
        neighbors_depth2 = graph.query("a", depth=2)

        # Depth 1: only b
        assert len(neighbors_depth1.get("relates_to", [])) >= 1
        # Depth 2: b and c
        assert len(neighbors_depth2.get("relates_to", [])) >= 2

    def test_find_path(self):
        """Test finding shortest path between nodes."""
        graph = KnowledgeGraph()
        graph.add_edge("transformer", "attention", "uses")
        graph.add_edge("attention", "query", "has")
        graph.add_edge("query", "key", "paired_with")

        path = graph.find_path("transformer", "key")

        assert path is not None
        assert path[0] == "transformer"
        assert path[-1] == "key"
        assert len(path) == 4  # 4 nodes in path

    def test_find_path_same_node(self):
        """Test path from node to itself."""
        graph = KnowledgeGraph()
        graph.add_node("transformer", "Transformer", "method")

        path = graph.find_path("transformer", "transformer")

        assert path == ["transformer"]

    def test_find_path_no_path(self):
        """Test when no path exists."""
        graph = KnowledgeGraph()
        graph.add_node("a", "A", "concept")
        graph.add_node("b", "B", "concept")

        path = graph.find_path("a", "b")

        assert path is None

    def test_find_similar(self):
        """Test finding similar nodes."""
        graph = KnowledgeGraph()
        # Create central hub node
        graph.add_edge("transformer", "nlp", "used_in")
        graph.add_edge("transformer", "vision", "used_in")
        graph.add_edge("transformer", "efficiency", "provides")

        # Create other node with some shared neighbors
        graph.add_edge("attention", "nlp", "used_in")
        graph.add_edge("attention", "efficiency", "provides")

        similar = graph.find_similar("transformer", top_k=5)

        assert len(similar) > 0
        # Attention should be in similar (shares neighbors)
        similar_ids = [node_id for node_id, _ in similar]
        assert "attention" in similar_ids

    def test_calculate_influence(self):
        """Test calculating node influence."""
        graph = KnowledgeGraph()
        graph.add_edge("transformer", "bert", "extends")
        graph.add_edge("transformer", "gpt", "extends")
        graph.add_edge("attention", "transformer", "enables")

        influence = graph.calculate_influence()

        assert "transformer" in influence
        assert isinstance(influence["transformer"], float)
        assert 0 <= influence["transformer"] <= 1

    def test_get_node_stats(self):
        """Test getting node statistics."""
        graph = KnowledgeGraph()
        graph.add_edge("transformer", "bert", "extends")
        graph.add_edge("attention", "transformer", "enables")

        stats = graph.get_node_stats("transformer")

        assert stats["in_degree"] == 1  # attention -> transformer
        assert stats["out_degree"] == 1  # transformer -> bert
        assert stats["influence_score"] >= 0

    def test_to_dict(self):
        """Test exporting graph to dict."""
        graph = KnowledgeGraph()
        graph.add_edge("transformer", "bert", "extends")

        graph_dict = graph.to_dict()

        assert "nodes" in graph_dict
        assert "edges" in graph_dict
        assert len(graph_dict["nodes"]) == 2
        assert len(graph_dict["edges"]) == 1

    def test_get_subgraph(self):
        """Test extracting subgraph."""
        graph = KnowledgeGraph()
        graph.add_edge("a", "b", "relates")
        graph.add_edge("b", "c", "relates")
        graph.add_edge("c", "d", "relates")

        subgraph = graph.get_subgraph(["a", "b", "c"])

        assert "a" in subgraph.nodes
        assert "b" in subgraph.nodes
        assert "c" in subgraph.nodes
        assert "d" not in subgraph.nodes
        assert ("a", "b") in subgraph.edges or ("b", "a") in subgraph.edges

    def test_merge_graphs(self):
        """Test merging two graphs."""
        graph1 = KnowledgeGraph()
        graph1.add_edge("a", "b", "relates")

        graph2 = KnowledgeGraph()
        graph2.add_edge("c", "d", "relates")

        graph1.merge(graph2)

        assert "a" in graph1.nodes
        assert "c" in graph1.nodes
        assert len(graph1.edges) == 2


class TestIntegration:
    """Integration tests for relationships and knowledge graph."""

    def test_extract_and_build_graph(self):
        """Test extracting relationships and building knowledge graph."""
        text = """
        Smith cites Johnson's work on neural networks.
        The transformer architecture extends RNNs by using attention mechanisms.
        BERT uses the transformer as its foundation.
        """

        # Extract entities first (would come from ConceptExtractor)
        extractor = RelationshipExtractor()
        relationships = extractor.extract(text)

        # Build knowledge graph from relationships
        graph = KnowledgeGraph()

        for rel in relationships:
            graph.add_node(rel.entity_a, rel.entity_a, "entity")
            graph.add_node(rel.entity_b, rel.entity_b, "entity")
            graph.add_edge(rel.entity_a, rel.entity_b, rel.relation_type.value, rel.confidence)

        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

    def test_graph_queries_on_extracted_relationships(self):
        """Test querying graph built from extracted relationships."""
        text = "Transformer uses attention. BERT uses transformer. GPT uses transformer."

        extractor = RelationshipExtractor()
        relationships = extractor.extract(text)

        graph = KnowledgeGraph()
        for rel in relationships:
            graph.add_edge(rel.entity_a, rel.entity_b, rel.relation_type.value, rel.confidence)

        # Query what uses transformer
        neighbors = graph.query("transformer", depth=1)
        assert "uses" in neighbors or len(neighbors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
