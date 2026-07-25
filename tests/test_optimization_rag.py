"""Tests for Phase 5e: Intelligent RAG Optimization."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
from pystreampdf.optimization import (
    SelectiveIntelligence,
    ContentSelector,
    ContentDetail,
    AdaptiveCompressor,
    CompressionStrategy,
    RetrievalMetadata,
    MetadataInjector,
    ChunkDensity,
    ChunkingEngine,
    ChunkingStrategy,
    RAGChunk,
)
from pystreampdf.structure.builder import NodeType


class TestSelectiveIntelligence(unittest.TestCase):
    """Tests for selective intelligence decision making."""

    def setUp(self):
        self.intelligence = SelectiveIntelligence()

    def test_code_gets_full_detail(self):
        detail = self.intelligence.select_detail_level(NodeType.CODE, 0.9)
        self.assertEqual(detail, ContentDetail.FULL)

    def test_config_gets_full_detail(self):
        detail = self.intelligence.select_detail_level(NodeType.CONFIG, 0.8)
        self.assertEqual(detail, ContentDetail.FULL)

    def test_narrative_gets_summary(self):
        detail = self.intelligence.select_detail_level(NodeType.NARRATIVE, 0.7)
        self.assertEqual(detail, ContentDetail.SUMMARY)

    def test_low_confidence_skips(self):
        detail = self.intelligence.select_detail_level(NodeType.SECTION, 0.2)
        self.assertEqual(detail, ContentDetail.SKIP)

    def test_customize_policy(self):
        self.intelligence.customize_policy(NodeType.CODE, ContentDetail.SUMMARY, 0.8)
        detail = self.intelligence.select_detail_level(NodeType.CODE, 0.9)
        self.assertEqual(detail, ContentDetail.SUMMARY)


class TestContentSelector(unittest.TestCase):
    """Tests for content selection and prioritization."""

    def setUp(self):
        self.selector = ContentSelector()

    def test_select_high_confidence_code(self):
        selection = self.selector.select_for_rag(NodeType.CODE, 0.95, 500)
        self.assertTrue(selection["include"])
        self.assertEqual(selection["compression_ratio"], 1.0)
        self.assertGreater(selection["priority"], 0.8)

    def test_select_low_confidence_narrative(self):
        selection = self.selector.select_for_rag(NodeType.NARRATIVE, 0.3, 500)
        # Low confidence narrative still included, but with heavy compression
        self.assertTrue(selection["include"])
        self.assertLess(selection["compression_ratio"], 0.5)

    def test_tokens_estimated(self):
        selection = self.selector.select_for_rag(NodeType.CODE, 0.9, 400)
        # 400 chars / 4 = 100 tokens (roughly)
        self.assertAlmostEqual(selection["estimated_tokens"], 100, delta=10)

    def test_batch_selection(self):
        nodes = [
            {"node_type": NodeType.CODE, "confidence": 0.9, "content": "def foo(): pass"},
            {"node_type": NodeType.NARRATIVE, "confidence": 0.5, "content": "Some narrative"},
        ]
        selections = self.selector.select_batch(nodes)
        # Should be sorted by priority
        self.assertGreater(selections[0]["priority"], selections[1]["priority"])


class TestAdaptiveCompressor(unittest.TestCase):
    """Tests for adaptive compression."""

    def setUp(self):
        self.compressor = AdaptiveCompressor()

    def test_lossless_preserves_structure(self):
        code = "def hello():\n    # Comment\n    return 42"
        compressed = self.compressor.compress(code, CompressionStrategy.LOSSLESS, 0.7)
        # Structure should be preserved
        self.assertIn("def hello", compressed)
        self.assertIn("return 42", compressed)

    def test_lossy_removes_content(self):
        narrative = "This is a long sentence. This is another sentence. Key result: important finding."
        compressed = self.compressor.compress(narrative, CompressionStrategy.LOSSY, 0.3)
        self.assertLess(len(compressed), len(narrative))
        self.assertGreater(len(compressed), 0)

    def test_no_compression(self):
        text = "Keep this"
        result = self.compressor.compress(text, CompressionStrategy.NONE, 0.5)
        self.assertEqual(result, text)

    def test_suggest_strategy_code(self):
        strategy = self.compressor.suggest_strategy("code", 0.8)
        self.assertEqual(strategy, CompressionStrategy.LOSSLESS)

    def test_suggest_strategy_low_confidence(self):
        strategy = self.compressor.suggest_strategy("narrative", 0.3)
        self.assertEqual(strategy, CompressionStrategy.LOSSY)

    def test_suggest_ratio_high_importance(self):
        ratio = self.compressor.suggest_ratio(0.9, importance=0.9)
        self.assertEqual(ratio, 1.0)  # No compression

    def test_suggest_ratio_low_importance(self):
        ratio = self.compressor.suggest_ratio(0.2, importance=0.1)
        self.assertEqual(ratio, 0.1)  # Heavy compression


class TestRetrievalMetadata(unittest.TestCase):
    """Tests for retrieval metadata and scoring."""

    def test_metadata_creation(self):
        meta = RetrievalMetadata(
            chunk_id="chunk_1",
            node_type="code",
            content_type="python",
            confidence=0.9,
            density=ChunkDensity.HIGH,
            length=500,
            estimated_tokens=125,
            relevance_score=0.85,
            priority=0.76,
            update_frequency="stable",
        )
        self.assertEqual(meta.chunk_id, "chunk_1")
        self.assertEqual(meta.confidence, 0.9)

    def test_density_estimation_long_lines(self):
        content = "This is a very long line with lots of information packed into it for testing purposes"
        density = MetadataInjector.estimate_density(content)
        self.assertEqual(density, ChunkDensity.HIGH)

    def test_density_estimation_short_lines(self):
        content = "a\nb\nc"
        density = MetadataInjector.estimate_density(content)
        self.assertEqual(density, ChunkDensity.LOW)

    def test_density_estimation_structured(self):
        content = "{key: value, nested: {sub: 1}}"
        density = MetadataInjector.estimate_density(content)
        # Should be boosted for special characters
        self.assertIn(density, [ChunkDensity.HIGH, ChunkDensity.MEDIUM])

    def test_relevance_calculation(self):
        # High confidence + high density + good length
        score = MetadataInjector.calculate_relevance(0.95, ChunkDensity.HIGH, 1000)
        self.assertGreater(score, 0.4)  # Should be reasonably high

    def test_relevance_low_confidence(self):
        score = MetadataInjector.calculate_relevance(0.3, ChunkDensity.LOW, 1000)
        self.assertLess(score, 0.5)

    def test_inject_metadata(self):
        meta = MetadataInjector.inject_metadata(
            chunk_id="test",
            node_type="code",
            content="def foo(): pass",
            confidence=0.9,
            source_analyzer="code",
        )
        self.assertEqual(meta.chunk_id, "test")
        self.assertEqual(meta.source_analyzer, "code")
        self.assertGreater(meta.relevance_score, 0.0)
        self.assertLess(meta.relevance_score, 1.0)


class TestChunkingEngine(unittest.TestCase):
    """Tests for RAG chunking."""

    def setUp(self):
        self.engine = ChunkingEngine(strategy=ChunkingStrategy.ADAPTIVE, token_budget=10000)

    def test_engine_creation(self):
        self.assertIsNotNone(self.engine)

    def test_rag_chunk_creation(self):
        meta = RetrievalMetadata(
            chunk_id="c1",
            node_type="code",
            content_type="python",
            confidence=0.9,
            density=ChunkDensity.HIGH,
            length=100,
            estimated_tokens=25,
            relevance_score=0.85,
            priority=0.76,
            update_frequency="stable",
        )
        chunk = RAGChunk(
            id="c1",
            content="def test(): pass",
            metadata=meta,
            compression_ratio=1.0,
            original_content_length=100,
        )
        self.assertEqual(chunk.token_count(), 25)

    def test_chunk_to_retrieval_format(self):
        meta = RetrievalMetadata(
            chunk_id="c1",
            node_type="code",
            content_type="python",
            confidence=0.9,
            density=ChunkDensity.HIGH,
            length=100,
            estimated_tokens=25,
            relevance_score=0.85,
            priority=0.76,
            update_frequency="stable",
        )
        chunk = RAGChunk(
            id="c1",
            content="test",
            metadata=meta,
            compression_ratio=1.0,
            original_content_length=100,
        )
        fmt = chunk.to_retrieval_format()
        self.assertIn("id", fmt)
        self.assertIn("content", fmt)
        self.assertIn("metadata", fmt)

    def test_chunk_graph_simple(self):
        graph_data = {
            "nodes": {
                "node1": {
                    "type": "code",
                    "content": "def foo(): pass",
                    "confidence": 0.9,
                    "source_analyzer": "code",
                },
                "node2": {
                    "type": "narrative",
                    "content": "Some text",
                    "confidence": 0.7,
                    "source_analyzer": None,
                },
            },
            "edges": [],
        }
        chunks = self.engine.chunk_graph(graph_data)
        self.assertGreater(len(chunks), 0)

    def test_token_budget_enforcement(self):
        # Create a graph that would exceed token budget
        graph_data = {
            "nodes": {
                f"node{i}": {
                    "type": "narrative",
                    "content": "x" * 10000,  # Large content
                    "confidence": 0.9,
                    "source_analyzer": None,
                }
                for i in range(10)
            },
            "edges": [],
        }
        chunks = self.engine.chunk_graph(graph_data)
        total_tokens = sum(c.token_count() for c in chunks)
        self.assertLessEqual(total_tokens, self.engine.token_budget)

    def test_chunking_sorting_by_priority(self):
        graph_data = {
            "nodes": {
                "high": {
                    "type": "code",
                    "content": "high priority",
                    "confidence": 0.95,
                },
                "low": {
                    "type": "narrative",
                    "content": "low priority",
                    "confidence": 0.3,
                },
            },
            "edges": [],
        }
        chunks = self.engine.chunk_graph(graph_data, confidence_floor=0.0)
        # High priority should come first
        if len(chunks) > 1:
            self.assertGreater(chunks[0].metadata.priority, chunks[-1].metadata.priority)

    def test_explain_chunking(self):
        meta = RetrievalMetadata(
            chunk_id="c1",
            node_type="code",
            content_type="python",
            confidence=0.9,
            density=ChunkDensity.HIGH,
            length=100,
            estimated_tokens=25,
            relevance_score=0.85,
            priority=0.76,
            update_frequency="stable",
            validation_issues=2,
            corrections_applied=1,
        )
        chunk = RAGChunk(
            id="c1",
            content="test",
            metadata=meta,
            compression_ratio=1.0,
            original_content_length=100,
        )
        explanation = self.engine.explain_chunking(chunk)
        self.assertIn("Chunk:", explanation)
        self.assertIn("Priority:", explanation)
        self.assertIn("Issues:", explanation)


if __name__ == "__main__":
    unittest.main()
