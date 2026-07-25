"""Export document graphs in multiple formats for different downstream systems."""

import json
from typing import Dict, List, Any
from datetime import datetime

from .builder import DocumentGraph, NodeType, EdgeType


class GraphExporter:
    """Base class for graph exporters."""

    def export(self, graph: DocumentGraph) -> str:
        """Export graph to format-specific string."""
        raise NotImplementedError


class MarkdownExporter(GraphExporter):
    """Export document graph as Markdown with structure preserved."""

    def export(self, graph: DocumentGraph) -> str:
        """Convert graph to Markdown."""
        lines = []

        if not graph.nodes:
            return "# Empty Document"

        # Find root or start from H1 nodes
        if graph.root_id and graph.root_id in graph.nodes:
            root_node = graph.nodes[graph.root_id]
            lines.append(f"# {root_node.content}")
            self._export_subtree(graph.root_id, graph, lines, level=1)
        else:
            # No root, export all H1-level sections
            for node_id, node in graph.nodes.items():
                if (
                    node.node_type == NodeType.SECTION
                    and node.metadata.get("level") == 1
                ):
                    lines.append(f"# {node.content}")
                    self._export_subtree(node_id, graph, lines, level=1)

        return "\n".join(lines)

    def _export_subtree(
        self, node_id: str, graph: DocumentGraph, lines: List[str], level: int
    ) -> None:
        """Recursively export node and children."""
        node = graph.nodes[node_id]

        # Skip root
        if level > 1:
            prefix = "#" * min(level, 6)
            lines.append(f"{prefix} {node.content}")

        # Add children (CONTAINS edges)
        for edge in graph.edges:
            if (
                edge.source_id == node_id
                and edge.edge_type == EdgeType.CONTAINS
                and edge.target_id in graph.nodes
            ):
                child = graph.nodes[edge.target_id]
                if child.node_type == NodeType.SECTION:
                    self._export_subtree(edge.target_id, graph, lines, level + 1)
                else:
                    # Non-section child (figure, table, etc.)
                    lines.append(f"\n**{child.node_type.value.title()}:** {child.content}")


class JSONLDExporter(GraphExporter):
    """Export graph as JSON-LD for semantic web compatibility."""

    def export(self, graph: DocumentGraph) -> str:
        """Convert graph to JSON-LD."""
        ld = {
            "@context": "https://schema.org",
            "@type": "Document",
            "datePublished": datetime.now().isoformat(),
            "hasPart": [],
        }

        # Export nodes as hasPart
        for node in graph.nodes.values():
            part = {
                "@type": self._map_node_type_to_schema(node.node_type),
                "name": node.content,
                "confidence": node.confidence,
            }

            if node.metadata:
                part["metadata"] = node.metadata

            ld["hasPart"].append(part)

        # Export edges as relationships
        relationships = []
        for edge in graph.edges:
            rel = {
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.edge_type.value,
                "confidence": edge.confidence,
            }
            relationships.append(rel)

        if relationships:
            ld["relationships"] = relationships

        return json.dumps(ld, indent=2)

    @staticmethod
    def _map_node_type_to_schema(node_type: NodeType) -> str:
        """Map NodeType to JSON-LD schema type."""
        mapping = {
            NodeType.SECTION: "Article",
            NodeType.FIGURE: "ImageObject",
            NodeType.TABLE: "Table",
            NodeType.CODE: "Code",
            NodeType.CONFIG: "StructuredValue",
            NodeType.LOG: "Event",
            NodeType.CAPTION: "Description",
            NodeType.FOOTNOTE: "Note",
            NodeType.REFERENCE: "Link",
            NodeType.NARRATIVE: "Text",
        }
        return mapping.get(node_type, "Thing")


class RAGOptimizedExporter(GraphExporter):
    """Export graph in RAG-optimized format for retrieval systems."""

    def export(self, graph: DocumentGraph) -> str:
        """Convert graph to RAG-optimized JSON."""
        chunks = []

        for node_id, node in graph.nodes.items():
            # Score: size × confidence (prioritize large, high-confidence content)
            content_score = len(node.content) * node.confidence

            chunk = {
                "id": node_id,
                "type": node.node_type.value,
                "content": node.content,
                "confidence": node.confidence,
                "score": content_score,
                "metadata": {
                    "source_analyzer": node.source_analyzer,
                    "language": node.language,
                    "validation_issues": len(node.validation_issues),
                },
                "relationships": self._find_related(node_id, graph),
            }

            chunks.append(chunk)

        # Sort by relevance score (for default retrieval order)
        chunks.sort(key=lambda x: x["score"], reverse=True)

        return json.dumps(
            {
                "format": "rag_optimized",
                "version": "1.0",
                "chunk_count": len(chunks),
                "chunks": chunks,
            },
            indent=2,
        )

    @staticmethod
    def _find_related(node_id: str, graph: DocumentGraph) -> List[Dict[str, Any]]:
        """Find all relationships for a node."""
        relationships = []

        for edge in graph.edges:
            if edge.source_id == node_id:
                rel = {
                    "target_id": edge.target_id,
                    "type": edge.edge_type.value,
                    "confidence": edge.confidence,
                }
                relationships.append(rel)
            elif edge.target_id == node_id:
                rel = {
                    "source_id": edge.source_id,
                    "type": edge.edge_type.value,
                    "confidence": edge.confidence,
                    "direction": "incoming",
                }
                relationships.append(rel)

        return relationships


class SimpleJSONExporter(GraphExporter):
    """Export graph as simple nested JSON."""

    def export(self, graph: DocumentGraph) -> str:
        """Convert graph to nested JSON structure."""
        result = {
            "title": "Document Structure",
            "sections": [],
            "metadata": {
                "total_nodes": len(graph.nodes),
                "total_edges": len(graph.edges),
                "min_confidence": graph.min_confidence(),
            },
        }

        # Export nodes grouped by type
        nodes_by_type = {}
        for node in graph.nodes.values():
            node_type = node.node_type.value
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(
                {
                    "id": node.id,
                    "content": node.content,
                    "confidence": node.confidence,
                    "metadata": node.metadata,
                }
            )

        result["sections"] = [
            {"type": node_type, "count": len(nodes), "items": nodes}
            for node_type, nodes in nodes_by_type.items()
        ]

        return json.dumps(result, indent=2)
