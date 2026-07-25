"""Document structure recovery - reconstruct hierarchy and relationships from analyzed content."""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .builder import DocumentGraph, GraphNode, GraphEdge, NodeType, EdgeType


@dataclass
class DocumentMetadata:
    """Extracted document-level metadata."""
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    date: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    keywords: List[str] = field(default_factory=list)


@dataclass
class SectionHierarchy:
    """Section with hierarchy level and relationships."""
    title: str
    level: int  # 1=H1, 2=H2, etc.
    content: str
    page_number: int
    node_id: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    related_ids: List[str] = field(default_factory=list)  # Cross-references


class StructureRecoveryEngine:
    """
    Reconstruct document structure from analyzed content.

    Handles:
    - Document hierarchy (H1→H6, proper nesting)
    - Relationship recovery (figures↔captions, citations, appendices)
    - Section detection and boundary identification
    - Cross-reference tracking
    """

    def __init__(self):
        self.section_patterns = {
            "h1": re.compile(r"^#\s+(.+)$", re.MULTILINE),
            "h2": re.compile(r"^##\s+(.+)$", re.MULTILINE),
            "h3": re.compile(r"^###\s+(.+)$", re.MULTILINE),
            "h4": re.compile(r"^####\s+(.+)$", re.MULTILINE),
            "h5": re.compile(r"^#####\s+(.+)$", re.MULTILINE),
            "h6": re.compile(r"^######\s+(.+)$", re.MULTILINE),
        }

        self.figure_pattern = re.compile(
            r"(?:Figure|Fig\.?|Exhibit|Image)\s*[\d\.]+(?::|\.)\s*(.+?)(?:\n|$)", re.IGNORECASE
        )
        self.caption_pattern = re.compile(
            r"(?:Caption|Description):\s*(.+?)(?:\n\n|\Z)", re.IGNORECASE
        )
        self.table_pattern = re.compile(
            r"(?:Table|Tab\.?)\s*[\d\.]+(?::|\.)\s*(.+?)(?:\n|$)", re.IGNORECASE
        )
        self.appendix_pattern = re.compile(
            r"(?:Appendix|Annex)\s*([A-Z]|\d+)(?::|\.)\s*(.+?)(?:\n|$)", re.IGNORECASE
        )
        self.reference_pattern = re.compile(
            r"\[(\d+|[a-z]+)\]|→|→|See (section|figure|table|appendix)\s+(.+?)(?:\.|,|\n)", re.IGNORECASE
        )

    def recover_structure(
        self, content: str, graph: DocumentGraph, confidence: float = 1.0
    ) -> DocumentGraph:
        """
        Recover document structure from content.

        Args:
            content: Full document text (ideally markdown-formatted)
            graph: DocumentGraph to populate
            confidence: Confidence in the analysis

        Returns:
            Enhanced DocumentGraph with recovered structure
        """
        # Step 1: Extract sections and build hierarchy
        sections = self._extract_sections(content)
        section_nodes = self._build_section_hierarchy(sections, graph, confidence)

        # Step 2: Detect figures and captions
        figures = self._detect_figures(content)
        self._link_figures_to_sections(figures, section_nodes, graph, confidence)

        # Step 3: Detect tables and metadata
        tables = self._detect_tables(content)
        self._link_tables_to_sections(tables, section_nodes, graph, confidence)

        # Step 4: Detect appendices
        appendices = self._detect_appendices(content)
        self._link_appendices(appendices, section_nodes, graph, confidence)

        # Step 5: Extract cross-references
        self._extract_cross_references(content, section_nodes, graph, confidence)

        return graph

    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract all section headers and their content."""
        sections = []
        lines = content.split("\n")
        current_section = None
        section_content = []

        for i, line in enumerate(lines):
            # Check for markdown headers
            for level, pattern in enumerate(self.section_patterns.values(), 1):
                match = pattern.match(line)
                if match:
                    # Save previous section
                    if current_section:
                        current_section["content"] = "\n".join(section_content)
                        sections.append(current_section)

                    # Start new section
                    current_section = {
                        "title": match.group(1).strip(),
                        "level": level,
                        "line_start": i,
                        "content": "",
                    }
                    section_content = []
                    break
            else:
                # Accumulate content for current section
                if current_section is not None:
                    section_content.append(line)

        # Save final section
        if current_section:
            current_section["content"] = "\n".join(section_content)
            sections.append(current_section)

        return sections

    def _build_section_hierarchy(
        self, sections: List[Dict[str, Any]], graph: DocumentGraph, confidence: float
    ) -> Dict[int, SectionHierarchy]:
        """Build proper hierarchy from flat section list."""
        hierarchy = {}
        stack = []  # Stack of (level, section_hierarchy)

        for section_dict in sections:
            level = section_dict["level"]
            title = section_dict["title"]

            # Create node
            node = GraphNode(
                node_type=NodeType.SECTION,
                content=title,
                confidence=confidence,
                metadata={
                    "level": level,
                    "content_length": len(section_dict["content"]),
                },
            )
            node_id = graph.add_node(node)

            # Find parent (last section with level < current)
            parent_id = None
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                parent_id = stack[-1][1].node_id
                # Add containment edge
                edge = GraphEdge(
                    source_id=parent_id,
                    target_id=node_id,
                    edge_type=EdgeType.CONTAINS,
                    confidence=confidence,
                )
                graph.add_edge(edge)

            section_hier = SectionHierarchy(
                title=title,
                level=level,
                content=section_dict["content"],
                page_number=section_dict.get("page", 1),
                node_id=node_id,
                parent_id=parent_id,
            )

            hierarchy[len(hierarchy)] = section_hier
            stack.append((level, section_hier))

            # Set root if this is H1
            if level == 1 and graph.root_id is None:
                graph.set_root(node_id)

        return hierarchy

    def _detect_figures(self, content: str) -> List[Dict[str, str]]:
        """Detect figure references and captions."""
        figures = []

        for match in self.figure_pattern.finditer(content):
            figure_text = match.group(0)
            caption_match = self.caption_pattern.search(content, match.end())

            figures.append(
                {
                    "reference": match.group(1),
                    "caption": caption_match.group(1) if caption_match else "",
                    "position": match.start(),
                }
            )

        return figures

    def _link_figures_to_sections(
        self,
        figures: List[Dict[str, str]],
        sections: Dict[int, SectionHierarchy],
        graph: DocumentGraph,
        confidence: float,
    ) -> None:
        """Link figures to sections they appear in."""
        for figure in figures:
            # Create figure node
            fig_node = GraphNode(
                node_type=NodeType.FIGURE,
                content=figure["reference"],
                confidence=confidence,
                metadata={"caption": figure["caption"][:100]},
            )
            fig_id = graph.add_node(fig_node)

            # Create caption node
            if figure["caption"]:
                cap_node = GraphNode(
                    node_type=NodeType.CAPTION,
                    content=figure["caption"][:100],
                    confidence=confidence,
                )
                cap_id = graph.add_node(cap_node)

                # Figure→Caption relationship
                edge = GraphEdge(
                    source_id=fig_id,
                    target_id=cap_id,
                    edge_type=EdgeType.DESCRIBED_BY,
                    confidence=confidence,
                )
                graph.add_edge(edge)

            # Link to nearest section
            for section in sections.values():
                if section.node_id in graph.nodes:
                    # Find containing section
                    edge = GraphEdge(
                        source_id=section.node_id,
                        target_id=fig_id,
                        edge_type=EdgeType.CONTAINS,
                        confidence=confidence * 0.9,  # Slightly lower confidence for inferred link
                    )
                    graph.add_edge(edge)
                    break

    def _detect_tables(self, content: str) -> List[Dict[str, str]]:
        """Detect table references."""
        tables = []

        for match in self.table_pattern.finditer(content):
            tables.append(
                {
                    "reference": match.group(1),
                    "position": match.start(),
                }
            )

        return tables

    def _link_tables_to_sections(
        self,
        tables: List[Dict[str, str]],
        sections: Dict[int, SectionHierarchy],
        graph: DocumentGraph,
        confidence: float,
    ) -> None:
        """Link tables to sections they appear in."""
        for table in tables:
            table_node = GraphNode(
                node_type=NodeType.TABLE,
                content=table["reference"],
                confidence=confidence,
            )
            table_id = graph.add_node(table_node)

            # Link to nearest section
            for section in sections.values():
                if section.node_id in graph.nodes:
                    edge = GraphEdge(
                        source_id=section.node_id,
                        target_id=table_id,
                        edge_type=EdgeType.CONTAINS,
                        confidence=confidence * 0.9,
                    )
                    graph.add_edge(edge)
                    break

    def _detect_appendices(self, content: str) -> List[Dict[str, str]]:
        """Detect appendix sections."""
        appendices = []

        for match in self.appendix_pattern.finditer(content):
            appendices.append(
                {
                    "letter": match.group(1),
                    "title": match.group(2),
                    "position": match.start(),
                }
            )

        return appendices

    def _link_appendices(
        self,
        appendices: List[Dict[str, str]],
        sections: Dict[int, SectionHierarchy],
        graph: DocumentGraph,
        confidence: float,
    ) -> None:
        """Link appendices to main document."""
        if not appendices:
            return

        # Create appendix container
        appendix_container = GraphNode(
            node_type=NodeType.SECTION,
            content="Appendices",
            confidence=confidence,
            metadata={"level": 1},
        )
        container_id = graph.add_node(appendix_container)

        for appendix in appendices:
            app_node = GraphNode(
                node_type=NodeType.SECTION,
                content=f"Appendix {appendix['letter']}: {appendix['title']}",
                confidence=confidence,
                metadata={"level": 2, "type": "appendix"},
            )
            app_id = graph.add_node(app_node)

            # Container→Appendix
            edge = GraphEdge(
                source_id=container_id,
                target_id=app_id,
                edge_type=EdgeType.CONTAINS,
                confidence=confidence,
            )
            graph.add_edge(edge)

    def _extract_cross_references(
        self,
        content: str,
        sections: Dict[int, SectionHierarchy],
        graph: DocumentGraph,
        confidence: float,
    ) -> None:
        """Extract and link cross-references between sections."""
        for match in self.reference_pattern.finditer(content):
            ref_id = match.group(1)
            ref_type = match.group(2) if match.group(2) else "unknown"
            ref_target = match.group(3) if match.group(3) else ""

            # Try to link to section
            for section in sections.values():
                if ref_target.lower() in section.title.lower():
                    # Find source section for this reference
                    for src_section in sections.values():
                        if src_section.node_id in graph.nodes:
                            edge = GraphEdge(
                                source_id=src_section.node_id,
                                target_id=section.node_id,
                                edge_type=EdgeType.REFERENCES,
                                confidence=confidence * 0.8,  # Lower confidence for inferred
                            )
                            graph.add_edge(edge)
                            break
                    break

    def extract_metadata(self, content: str) -> DocumentMetadata:
        """Extract document-level metadata."""
        metadata = DocumentMetadata()

        # Simple heuristics for metadata
        lines = content.split("\n")

        # Title (usually first H1)
        for line in lines[:10]:
            if line.startswith("# "):
                metadata.title = line[2:].strip()
                break

        # Keywords (look for keyword section)
        for i, line in enumerate(lines):
            if "keyword" in line.lower() and i + 1 < len(lines):
                keywords_str = lines[i + 1]
                metadata.keywords = [k.strip() for k in keywords_str.split(",")]
                break

        # Language (default English, could extend)
        metadata.language = "en"

        return metadata
