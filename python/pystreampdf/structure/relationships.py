"""Relationship extractor - converts intelligence insights into graph relationships."""

from enum import Enum
from typing import Dict, List, Optional, Set

from ..intelligence.types import IntelligenceResult
from ..pipeline import UnifiedAnalysisResult
from .builder import DocumentGraph, GraphNode, GraphEdge, NodeType, EdgeType


class RelationType(Enum):
    """High-level relationship types for RAG optimization."""
    STRUCTURE = "structure"  # Document hierarchy
    DEFINITION = "definition"  # Defines a term/concept
    DEPENDENCY = "dependency"  # Code/config dependencies
    REFERENCE = "reference"  # Cites or references
    ILLUSTRATION = "illustration"  # Figure/caption relationship
    EVIDENCE = "evidence"  # Supports or evidences claim


class RelationshipExtractor:
    """
    Extract semantic relationships from intelligence analysis results.

    Maps intelligence insights → graph relationships:
    - YAML/JSON/SQL structure → containment edges
    - Code imports → dependency edges
    - Log errors → evidence edges
    - Cross-references → reference edges
    """

    def extract_from_intelligence(
        self, intelligence_result: IntelligenceResult, parent_node_id: str, graph: DocumentGraph
    ) -> List[GraphEdge]:
        """
        Extract relationships from intelligence analysis.

        Args:
            intelligence_result: IntelligenceResult from Phase 5c
            parent_node_id: ID of parent node in graph
            graph: DocumentGraph to add nodes/edges to

        Returns:
            List of extracted edges
        """
        edges = []

        if intelligence_result.content_type == "yaml":
            edges.extend(self._extract_yaml_relationships(intelligence_result, parent_node_id, graph))

        elif intelligence_result.content_type == "json":
            edges.extend(self._extract_json_relationships(intelligence_result, parent_node_id, graph))

        elif intelligence_result.content_type == "sql":
            edges.extend(self._extract_sql_relationships(intelligence_result, parent_node_id, graph))

        elif intelligence_result.content_type == "python":
            edges.extend(self._extract_code_relationships(intelligence_result, parent_node_id, graph))

        elif intelligence_result.content_type in ["syslog", "journalctl", "kernel", "docker", "k8s"]:
            edges.extend(self._extract_log_relationships(intelligence_result, parent_node_id, graph))

        return edges

    def _extract_yaml_relationships(
        self, result: IntelligenceResult, parent_id: str, graph: DocumentGraph
    ) -> List[GraphEdge]:
        """Extract structure from YAML metadata."""
        edges = []

        meta = result.metadata
        if not meta:
            return edges

        # Each top-level key becomes a child node
        for key in meta.get("root_keys", []):
            child = GraphNode(
                node_type=NodeType.CONFIG,
                content=key,
                confidence=result.confidence,
                source_analyzer="yaml",
                metadata={"key_name": key},
            )
            child_id = graph.add_node(child)

            # Parent contains child
            edge = GraphEdge(
                source_id=parent_id,
                target_id=child_id,
                edge_type=EdgeType.CONTAINS,
                confidence=result.confidence,
            )
            edges.append(edge)
            graph.add_edge(edge)

        return edges

    def _extract_json_relationships(
        self, result: IntelligenceResult, parent_id: str, graph: DocumentGraph
    ) -> List[GraphEdge]:
        """Extract structure from JSON metadata."""
        edges = []

        meta = result.metadata
        if not meta:
            return edges

        # Inferred purpose guides node type
        purpose = meta.get("inferred_purpose", "unknown")
        node_type = {
            "api_response": NodeType.TABLE,
            "config": NodeType.CONFIG,
            "error_response": NodeType.NARRATIVE,
            "data_array": NodeType.TABLE,
        }.get(purpose, NodeType.NARRATIVE)

        # Create node for the JSON structure
        child = GraphNode(
            node_type=node_type,
            content=result.content_type,
            confidence=result.confidence,
            source_analyzer="json",
            metadata={"purpose": purpose, "key_count": meta.get("key_count", 0)},
        )
        child_id = graph.add_node(child)

        # Parent describes child
        edge = GraphEdge(
            source_id=parent_id,
            target_id=child_id,
            edge_type=EdgeType.CONTAINS,
            confidence=result.confidence,
        )
        edges.append(edge)
        graph.add_edge(edge)

        return edges

    def _extract_sql_relationships(
        self, result: IntelligenceResult, parent_id: str, graph: DocumentGraph
    ) -> List[GraphEdge]:
        """Extract dependencies from SQL metadata."""
        edges = []

        meta = result.metadata
        if not meta:
            return edges

        # Create node for SQL structure
        child = GraphNode(
            node_type=NodeType.CODE,
            content=result.content_type,
            confidence=result.confidence,
            source_analyzer="sql",
            language="sql",
            metadata={
                "dialect": meta.get("dialect"),
                "query_types": meta.get("query_types", []),
                "table_count": len(meta.get("tables_referenced", [])),
            },
        )
        child_id = graph.add_node(child)

        # Parent contains SQL
        edge = GraphEdge(
            source_id=parent_id,
            target_id=child_id,
            edge_type=EdgeType.CONTAINS,
            confidence=result.confidence,
        )
        edges.append(edge)
        graph.add_edge(edge)

        # Create nodes for each table (dependency tracking)
        for table in meta.get("tables_referenced", []):
            table_node = GraphNode(
                node_type=NodeType.TABLE,
                content=table,
                confidence=result.confidence,
                source_analyzer="sql",
                metadata={"table_name": table},
            )
            table_id = graph.add_node(table_node)

            # SQL depends on tables
            dep_edge = GraphEdge(
                source_id=child_id,
                target_id=table_id,
                edge_type=EdgeType.DEPENDS_ON,
                confidence=result.confidence,
            )
            edges.append(dep_edge)
            graph.add_edge(dep_edge)

        return edges

    def _extract_code_relationships(
        self, result: IntelligenceResult, parent_id: str, graph: DocumentGraph
    ) -> List[GraphEdge]:
        """Extract structure from code metadata."""
        edges = []

        meta = result.metadata
        if not meta:
            return edges

        language = meta.get("language", "unknown")

        # Create node for code block
        child = GraphNode(
            node_type=NodeType.CODE,
            content=result.content_type,
            confidence=result.confidence,
            source_analyzer="code",
            language=language,
            metadata={
                "line_count": meta.get("line_count", 0),
                "function_count": len(meta.get("function_names", [])),
                "class_count": len(meta.get("class_names", [])),
            },
        )
        child_id = graph.add_node(child)

        # Parent contains code
        edge = GraphEdge(
            source_id=parent_id,
            target_id=child_id,
            edge_type=EdgeType.CONTAINS,
            confidence=result.confidence,
        )
        edges.append(edge)
        graph.add_edge(edge)

        # Create nodes for functions/classes (structure)
        for func_name in meta.get("function_names", []):
            func_node = GraphNode(
                node_type=NodeType.CODE,
                content=func_name,
                confidence=result.confidence,
                source_analyzer="code",
                metadata={"type": "function", "language": language},
            )
            func_id = graph.add_node(func_node)

            # Code contains functions
            func_edge = GraphEdge(
                source_id=child_id,
                target_id=func_id,
                edge_type=EdgeType.CONTAINS,
                confidence=result.confidence,
            )
            edges.append(func_edge)
            graph.add_edge(func_edge)

        # Create nodes for imports (dependencies)
        for import_name in meta.get("import_names", []):
            import_node = GraphNode(
                node_type=NodeType.NARRATIVE,
                content=import_name,
                confidence=result.confidence,
                source_analyzer="code",
                metadata={"type": "import", "language": language},
            )
            import_id = graph.add_node(import_node)

            # Code depends on imports
            import_edge = GraphEdge(
                source_id=child_id,
                target_id=import_id,
                edge_type=EdgeType.DEPENDS_ON,
                confidence=result.confidence,
            )
            edges.append(import_edge)
            graph.add_edge(import_edge)

        return edges

    def _extract_log_relationships(
        self, result: IntelligenceResult, parent_id: str, graph: DocumentGraph
    ) -> List[GraphEdge]:
        """Extract patterns from log metadata."""
        edges = []

        meta = result.metadata
        if not meta:
            return edges

        log_format = meta.get("log_format", "unknown")

        # Create node for logs
        child = GraphNode(
            node_type=NodeType.LOG,
            content=log_format,
            confidence=result.confidence,
            source_analyzer="log",
            metadata={
                "format": log_format,
                "entry_count": meta.get("entry_count", 0),
                "error_count": meta.get("error_count", 0),
            },
        )
        child_id = graph.add_node(child)

        # Parent contains logs
        edge = GraphEdge(
            source_id=parent_id,
            target_id=child_id,
            edge_type=EdgeType.CONTAINS,
            confidence=result.confidence,
        )
        edges.append(edge)
        graph.add_edge(edge)

        # Create nodes for error patterns (evidence)
        for crash_line in meta.get("crash_patterns", [])[:3]:  # Limit to top 3
            error_node = GraphNode(
                node_type=NodeType.NARRATIVE,
                content=crash_line[:100],
                confidence=result.confidence,
                source_analyzer="log",
                metadata={"type": "crash_pattern"},
            )
            error_id = graph.add_node(error_node)

            # Logs evidence errors
            error_edge = GraphEdge(
                source_id=child_id,
                target_id=error_id,
                edge_type=EdgeType.REFERENCES,
                confidence=result.confidence,
            )
            edges.append(error_edge)
            graph.add_edge(error_edge)

        return edges
