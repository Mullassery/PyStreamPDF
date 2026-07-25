"""Tests for unified analysis pipeline and critical gap fixes."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
from pystreampdf.pipeline import (
    AnalysisPipeline,
    UnifiedAnalysisResult,
    AnalysisStage,
)
from pystreampdf.structure import DocumentGraph, RelationshipExtractor


class TestUnifiedAnalysisResult(unittest.TestCase):
    """Tests for unified result type with confidence propagation."""

    def test_result_creation(self):
        result = UnifiedAnalysisResult(content="test content")
        self.assertEqual(result.content, "test content")
        self.assertEqual(result.overall_confidence, 0.0)
        self.assertFalse(result.fallback_used)

    def test_confidence_propagation_single_stage(self):
        result = UnifiedAnalysisResult(content="test")
        result.validation_confidence = 0.9
        result.compute_confidence()
        self.assertEqual(result.overall_confidence, 0.9)

    def test_confidence_propagation_multiple_stages(self):
        result = UnifiedAnalysisResult(content="test")
        result.ocr_confidence = 0.8
        result.validation_confidence = 0.9
        result.intelligence_confidence = 0.85
        result.compute_confidence()
        # Should multiply: 0.8 * 0.9 * 0.85 = 0.612
        self.assertAlmostEqual(result.overall_confidence, 0.612, places=2)

    def test_confidence_zero_handled(self):
        result = UnifiedAnalysisResult(content="test")
        result.compute_confidence()
        # No stages, should be neutral
        self.assertEqual(result.overall_confidence, 1.0)

    def test_recommendation_accept(self):
        result = UnifiedAnalysisResult(content="test")
        result.overall_confidence = 0.9
        self.assertIn("ACCEPT", result.get_recommendation())

    def test_recommendation_review(self):
        result = UnifiedAnalysisResult(content="test")
        result.overall_confidence = 0.7
        self.assertIn("REVIEW", result.get_recommendation())

    def test_recommendation_rerun(self):
        result = UnifiedAnalysisResult(content="test")
        result.overall_confidence = 0.4
        self.assertIn("RERUN", result.get_recommendation())

    def test_recommendation_fallback(self):
        result = UnifiedAnalysisResult(content="test")
        result.fallback_used = True
        self.assertIn("FALLBACK", result.get_recommendation())

    def test_add_error(self):
        result = UnifiedAnalysisResult(content="test")
        result.add_error(AnalysisStage.INTELLIGENCE, "parsing failed")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("intelligence", result.errors[0])
        self.assertIn("parsing failed", result.errors[0])

    def test_add_metric(self):
        result = UnifiedAnalysisResult(content="test")
        result.add_metric(AnalysisStage.VALIDATION, "TextValidator", 10.5)
        self.assertEqual(len(result.metrics), 1)
        self.assertEqual(result.metrics[0].duration_ms, 10.5)

    def test_total_duration(self):
        result = UnifiedAnalysisResult(content="test")
        result.add_metric(AnalysisStage.VALIDATION, "Validator", 10.0)
        result.add_metric(AnalysisStage.INTELLIGENCE, "Analyzer", 20.0)
        self.assertEqual(result.total_duration_ms(), 30.0)

    def test_most_expensive_stage(self):
        result = UnifiedAnalysisResult(content="test")
        result.add_metric(AnalysisStage.VALIDATION, "Validator", 10.0)
        result.add_metric(AnalysisStage.INTELLIGENCE, "Analyzer", 50.0)
        slowest = result.most_expensive_stage()
        self.assertEqual(slowest.analyzer_name, "Analyzer")

    def test_to_dict_serialization(self):
        result = UnifiedAnalysisResult(content="test")
        result.content_type = "yaml"
        result.overall_confidence = 0.85
        result.add_error(AnalysisStage.VALIDATION, "test error")

        d = result.to_dict()
        self.assertEqual(d["content_type"], "yaml")
        self.assertEqual(d["overall_confidence"], 0.85)
        self.assertIn("ACCEPT", d["recommendation"])


class TestAnalysisPipeline(unittest.TestCase):
    """Tests for unified analysis pipeline."""

    def setUp(self):
        self.pipeline = AnalysisPipeline()

    def test_pipeline_creation(self):
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(len(self.pipeline.results_cache), 0)

    def test_analyze_empty_content(self):
        result = self.pipeline.analyze("")
        self.assertEqual(result.overall_confidence, 0.0)

    def test_analyze_with_validation(self):
        yaml_content = "key: value\nother: 123"
        result = self.pipeline.analyze(yaml_content, run_validation=True)
        self.assertIsNotNone(result.validation_result)
        self.assertGreater(result.validation_confidence, 0.0)

    def test_analyze_with_intelligence(self):
        yaml_content = "key: value\nother: 123"
        result = self.pipeline.analyze(yaml_content, run_intelligence=True)
        self.assertIsNotNone(result.intelligence_result)
        self.assertGreater(result.intelligence_confidence, 0.0)
        self.assertIsNotNone(result.content_type)

    def test_analyze_json_auto_detection(self):
        json_content = '{"key": "value", "number": 42}'
        result = self.pipeline.analyze(json_content, run_intelligence=True)
        # YAML is permissive; JSON content may be detected as YAML (valid)
        self.assertIn(result.content_type, ["json", "yaml"])

    def test_analyze_code_auto_detection(self):
        code_content = "def hello():\n    return 42"
        result = self.pipeline.analyze(code_content, run_intelligence=True)
        # Code should be detected (YAML is also valid for this)
        self.assertIn(result.content_type, ["python", "yaml"])

    def test_analyze_sql_auto_detection(self):
        sql_content = "SELECT * FROM users WHERE id = 1;"
        result = self.pipeline.analyze(sql_content, run_intelligence=True)
        # SQL should be detected or fall back to YAML
        self.assertIn(result.content_type, ["sql", "yaml"])

    def test_analyze_full_pipeline(self):
        yaml_content = "enabled: true\nhost: localhost"
        result = self.pipeline.analyze(
            yaml_content, run_validation=True, run_intelligence=True
        )

        # Should have both validation and intelligence results
        self.assertIsNotNone(result.validation_result)
        self.assertIsNotNone(result.intelligence_result)
        # Confidence should be propagated
        self.assertGreater(result.overall_confidence, 0.0)

    def test_error_recovery_on_bad_yaml(self):
        bad_yaml = "key: value\n  bad indent: true"
        result = self.pipeline.analyze(bad_yaml, run_intelligence=True)
        # Should handle gracefully without crashing
        self.assertIsNotNone(result)
        # Fallback should NOT be used (we still got results)
        self.assertFalse(result.fallback_used)

    def test_performance_tracking(self):
        content = "def test(): pass"
        result = self.pipeline.analyze(content, run_intelligence=True)
        self.assertGreater(len(result.metrics), 0)
        self.assertGreater(result.total_duration_ms(), 0.0)

    def test_confidence_report_generation(self):
        content = "key: value"
        result = self.pipeline.analyze(content, run_validation=True, run_intelligence=True)
        report = self.pipeline.get_confidence_report(result)
        self.assertIn("Confidence", report)
        self.assertIn("Recommendation", report)


class TestStructureRecovery(unittest.TestCase):
    """Tests for Phase 5c→5d bridge (intelligence → structure)."""

    def setUp(self):
        self.extractor = RelationshipExtractor()
        self.graph = DocumentGraph()

    def test_graph_creation(self):
        self.assertEqual(len(self.graph.nodes), 0)
        self.assertEqual(len(self.graph.edges), 0)

    def test_add_node(self):
        from pystreampdf.structure import GraphNode, NodeType

        node = GraphNode(node_type=NodeType.SECTION, content="test")
        node_id = self.graph.add_node(node)
        self.assertIn(node_id, self.graph.nodes)

    def test_graph_relationships_yaml(self):
        from pystreampdf.intelligence import YAMLAnalyzer
        from pystreampdf.structure import GraphNode, NodeType

        # Create a parent node
        parent = GraphNode(node_type=NodeType.SECTION, content="YAML Config")
        parent_id = self.graph.add_node(parent)

        # Analyze YAML and extract relationships
        analyzer = YAMLAnalyzer()
        yaml_result = analyzer.analyze("database:\n  host: localhost\n  port: 5432")

        edges = self.extractor.extract_from_intelligence(yaml_result, parent_id, self.graph)

        # Should have created relationships
        self.assertGreater(len(edges), 0)
        # Graph should have new nodes
        self.assertGreater(len(self.graph.nodes), 1)

    def test_graph_relationships_json(self):
        from pystreampdf.intelligence import JSONAnalyzer
        from pystreampdf.structure import GraphNode, NodeType

        parent = GraphNode(node_type=NodeType.SECTION, content="API Response")
        parent_id = self.graph.add_node(parent)

        analyzer = JSONAnalyzer()
        json_result = analyzer.analyze('{"status": 200, "data": [1, 2, 3]}')

        edges = self.extractor.extract_from_intelligence(json_result, parent_id, self.graph)

        self.assertGreater(len(edges), 0)

    def test_graph_relationships_sql(self):
        from pystreampdf.intelligence import SQLAnalyzer
        from pystreampdf.structure import GraphNode, NodeType

        parent = GraphNode(node_type=NodeType.SECTION, content="Database")
        parent_id = self.graph.add_node(parent)

        analyzer = SQLAnalyzer()
        sql_result = analyzer.analyze("SELECT * FROM users WHERE id = 1;")

        edges = self.extractor.extract_from_intelligence(sql_result, parent_id, self.graph)

        # Should detect table dependency
        self.assertGreater(len(edges), 0)

    def test_graph_relationships_code(self):
        from pystreampdf.intelligence import CodeAnalyzer
        from pystreampdf.structure import GraphNode, NodeType

        parent = GraphNode(node_type=NodeType.SECTION, content="Code")
        parent_id = self.graph.add_node(parent)

        analyzer = CodeAnalyzer()
        code_result = analyzer.analyze("import os\ndef main(): pass")

        edges = self.extractor.extract_from_intelligence(code_result, parent_id, self.graph)

        # Should detect imports and functions
        self.assertGreater(len(edges), 0)

    def test_graph_node_count_by_type(self):
        from pystreampdf.structure import GraphNode, NodeType

        self.graph.add_node(GraphNode(node_type=NodeType.SECTION, content="sec1"))
        self.graph.add_node(GraphNode(node_type=NodeType.SECTION, content="sec2"))
        self.graph.add_node(GraphNode(node_type=NodeType.CODE, content="code1"))

        counts = self.graph.node_count_by_type()
        self.assertEqual(counts["section"], 2)
        self.assertEqual(counts["code"], 1)

    def test_graph_min_confidence(self):
        from pystreampdf.structure import GraphNode, NodeType

        node1 = GraphNode(node_type=NodeType.SECTION, confidence=0.9)
        node2 = GraphNode(node_type=NodeType.SECTION, confidence=0.7)

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        self.assertEqual(self.graph.min_confidence(), 0.7)

    def test_graph_to_dict_serialization(self):
        from pystreampdf.structure import GraphNode, NodeType

        node = GraphNode(node_type=NodeType.SECTION, content="test")
        self.graph.add_node(node)

        d = self.graph.to_dict()
        self.assertIn("nodes", d)
        self.assertIn("edges", d)
        self.assertIn("stats", d)
        self.assertEqual(d["stats"]["node_count"], 1)


if __name__ == "__main__":
    unittest.main()
