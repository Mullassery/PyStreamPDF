"""Tests for Phase 5d: Document structure recovery and multi-format export."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
import json
from pystreampdf.structure import (
    DocumentGraph,
    StructureRecoveryEngine,
    MarkdownExporter,
    JSONLDExporter,
    RAGOptimizedExporter,
    SimpleJSONExporter,
)


class TestStructureRecoveryEngine(unittest.TestCase):
    """Tests for document structure recovery."""

    def setUp(self):
        self.engine = StructureRecoveryEngine()
        self.graph = DocumentGraph()

    def test_engine_creation(self):
        self.assertIsNotNone(self.engine)

    def test_section_extraction_single(self):
        content = "# Main Section\nSome content here"
        sections = self.engine._extract_sections(content)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["title"], "Main Section")
        self.assertEqual(sections[0]["level"], 1)

    def test_section_extraction_hierarchy(self):
        content = """# Introduction
Section 1 content

## Background
Subsection content

## Related Work
More content

# Methods
Methods content"""
        sections = self.engine._extract_sections(content)
        self.assertEqual(len(sections), 4)
        self.assertEqual(sections[0]["level"], 1)
        self.assertEqual(sections[1]["level"], 2)
        self.assertEqual(sections[2]["level"], 2)
        self.assertEqual(sections[3]["level"], 1)

    def test_section_hierarchy_building(self):
        content = """# Main
Main content

## Sub1
Sub1 content

## Sub2
Sub2 content"""
        sections = self.engine._extract_sections(content)
        hierarchy = self.engine._build_section_hierarchy(sections, self.graph, 0.9)

        # Should have 3 sections
        self.assertEqual(len(hierarchy), 3)
        # Root should be set
        self.assertIsNotNone(self.graph.root_id)

    def test_figure_detection(self):
        content = "Figure 1: Sample visualization showing data trends"
        figures = self.engine._detect_figures(content)
        self.assertGreater(len(figures), 0)

    def test_table_detection(self):
        content = "Table 2.1: Comparative results and analysis"
        tables = self.engine._detect_tables(content)
        self.assertGreater(len(tables), 0)

    def test_appendix_detection(self):
        content = "Appendix A: Supplementary data\nAppendix B: Additional methods"
        appendices = self.engine._detect_appendices(content)
        self.assertEqual(len(appendices), 2)

    def test_full_structure_recovery(self):
        content = """# Document Title
Introduction text

## Background
Background content

Figure 1: Sample illustration

# Methods
Methods section

Table 1: Results summary

# Appendix
Appendix A: Raw data"""

        recovered_graph = self.engine.recover_structure(content, self.graph, confidence=0.9)

        # Should have created nodes
        self.assertGreater(len(recovered_graph.nodes), 0)
        # Should have created relationships
        self.assertGreater(len(recovered_graph.edges), 0)

    def test_metadata_extraction(self):
        content = """# The Great Analysis
Some introduction

Keywords: machine learning, data science, analysis"""

        metadata = self.engine.extract_metadata(content)
        self.assertEqual(metadata.title, "The Great Analysis")
        self.assertIsNotNone(metadata.language)

    def test_empty_content_handling(self):
        recovered_graph = self.engine.recover_structure("", self.graph, confidence=0.9)
        self.assertIsNotNone(recovered_graph)
        # Should not crash, but graph may be empty
        self.assertEqual(len(recovered_graph.edges), 0)


class TestMarkdownExporter(unittest.TestCase):
    """Tests for Markdown export format."""

    def setUp(self):
        self.exporter = MarkdownExporter()
        self.graph = DocumentGraph()
        self.engine = StructureRecoveryEngine()

    def test_export_empty_graph(self):
        md = self.exporter.export(self.graph)
        self.assertIn("Empty", md)

    def test_export_simple_structure(self):
        content = """# Main
Content

## Sub
Subcontent"""

        self.engine.recover_structure(content, self.graph, 0.9)
        md = self.exporter.export(self.graph)

        self.assertIn("# Main", md)
        self.assertIn("## Sub", md)

    def test_export_with_figures(self):
        content = """# Analysis
Figure 1: Key visualization"""

        self.engine.recover_structure(content, self.graph, 0.9)
        md = self.exporter.export(self.graph)

        self.assertIsNotNone(md)
        self.assertGreater(len(md), 0)


class TestJSONLDExporter(unittest.TestCase):
    """Tests for JSON-LD export format."""

    def setUp(self):
        self.exporter = JSONLDExporter()
        self.graph = DocumentGraph()
        self.engine = StructureRecoveryEngine()

    def test_export_structure(self):
        content = "# Main\nContent"
        self.engine.recover_structure(content, self.graph, 0.9)

        jsonld = self.exporter.export(self.graph)
        data = json.loads(jsonld)

        self.assertEqual(data["@type"], "Document")
        self.assertIn("hasPart", data)

    def test_export_includes_relationships(self):
        content = """# Main
## Sub
Content"""
        self.engine.recover_structure(content, self.graph, 0.9)

        jsonld = self.exporter.export(self.graph)
        data = json.loads(jsonld)

        # Should have relationships if there are edges
        if self.graph.edges:
            self.assertIn("relationships", data)


class TestRAGOptimizedExporter(unittest.TestCase):
    """Tests for RAG-optimized export format."""

    def setUp(self):
        self.exporter = RAGOptimizedExporter()
        self.graph = DocumentGraph()
        self.engine = StructureRecoveryEngine()

    def test_export_structure(self):
        content = "# Main\nThis is important content"
        self.engine.recover_structure(content, self.graph, 0.9)

        rag_json = self.exporter.export(self.graph)
        data = json.loads(rag_json)

        self.assertEqual(data["format"], "rag_optimized")
        self.assertIn("chunks", data)
        self.assertGreater(len(data["chunks"]), 0)

    def test_chunks_sorted_by_relevance(self):
        content = """# Important Section
Very detailed content with lots of important information here

## Minor Section
Brief"""

        self.engine.recover_structure(content, self.graph, 0.9)
        rag_json = self.exporter.export(self.graph)
        data = json.loads(rag_json)

        chunks = data["chunks"]
        # First chunk should be higher score than last
        if len(chunks) > 1:
            self.assertGreater(chunks[0]["score"], chunks[-1]["score"])

    def test_chunk_has_relationships(self):
        content = """# Main
## Sub
Content"""

        self.engine.recover_structure(content, self.graph, 0.9)
        rag_json = self.exporter.export(self.graph)
        data = json.loads(rag_json)

        for chunk in data["chunks"]:
            self.assertIn("relationships", chunk)


class TestSimpleJSONExporter(unittest.TestCase):
    """Tests for simple JSON export format."""

    def setUp(self):
        self.exporter = SimpleJSONExporter()
        self.graph = DocumentGraph()
        self.engine = StructureRecoveryEngine()

    def test_export_structure(self):
        content = "# Title\nContent"
        self.engine.recover_structure(content, self.graph, 0.9)

        simple_json = self.exporter.export(self.graph)
        data = json.loads(simple_json)

        self.assertIn("sections", data)
        self.assertIn("metadata", data)

    def test_export_metadata(self):
        content = "# Title\nContent"
        self.engine.recover_structure(content, self.graph, 0.9)

        simple_json = self.exporter.export(self.graph)
        data = json.loads(simple_json)

        meta = data["metadata"]
        self.assertIn("total_nodes", meta)
        self.assertIn("total_edges", meta)
        self.assertIn("min_confidence", meta)

    def test_export_nodes_grouped_by_type(self):
        content = """# Main
Figure 1: Sample

Table 1: Data"""

        self.engine.recover_structure(content, self.graph, 0.9)
        simple_json = self.exporter.export(self.graph)
        data = json.loads(simple_json)

        # Should have sections grouped by type
        self.assertGreater(len(data["sections"]), 0)


class TestStructureRecoveryIntegration(unittest.TestCase):
    """Integration tests for full structure recovery workflow."""

    def setUp(self):
        self.engine = StructureRecoveryEngine()
        self.graph = DocumentGraph()
        self.exporters = {
            "markdown": MarkdownExporter(),
            "jsonld": JSONLDExporter(),
            "rag": RAGOptimizedExporter(),
            "json": SimpleJSONExporter(),
        }

    def test_end_to_end_workflow(self):
        """Full workflow: content → recovery → multiple exports."""
        content = """# Research Paper
This is an important paper

## Introduction
Background and motivation

## Methods
Our approach

Figure 1: System architecture

## Results
Key findings

Table 1: Benchmark results

## Conclusion
Implications and future work

Appendix A: Implementation details"""

        # Recover structure
        recovered_graph = self.engine.recover_structure(content, self.graph, 0.95)

        # Verify recovery
        self.assertGreater(len(recovered_graph.nodes), 0)
        self.assertGreater(len(recovered_graph.edges), 0)

        # Export to all formats
        for fmt_name, exporter in self.exporters.items():
            export_result = exporter.export(recovered_graph)
            self.assertIsNotNone(export_result)
            self.assertGreater(len(export_result), 0)

            # Validate JSON exports can be parsed
            if fmt_name in ["jsonld", "rag", "json"]:
                data = json.loads(export_result)
                self.assertIsNotNone(data)

    def test_confidence_preservation(self):
        """Verify confidence scores are preserved through recovery and export."""
        content = "# Section\nContent"
        recovered_graph = self.engine.recover_structure(content, self.graph, 0.85)

        # All nodes should have confidence
        for node in recovered_graph.nodes.values():
            self.assertLessEqual(node.confidence, 1.0)
            self.assertGreaterEqual(node.confidence, 0.0)

    def test_large_document_handling(self):
        """Test recovery on larger documents."""
        content = "\n".join([
            f"# Section {i}\n"
            f"Content for section {i}\n"
            f"## Subsection {i}.1\n"
            f"More content\n"
            f"Figure {i}: Illustration\n"
            f"Table {i}: Data\n"
            for i in range(1, 11)
        ])

        recovered_graph = self.engine.recover_structure(content, self.graph, 0.9)

        # Should handle large documents
        self.assertGreater(len(recovered_graph.nodes), 10)


if __name__ == "__main__":
    unittest.main()
