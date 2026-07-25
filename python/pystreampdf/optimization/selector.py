"""Selective Intelligence: Identify what needs full detail vs summaries."""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..structure.builder import NodeType


class ContentDetail(Enum):
    """How much detail should this content have in RAG output."""
    FULL = "full"  # Keep everything (e.g., code, config, critical sections)
    SUMMARY = "summary"  # Compress to key points
    REFERENCE = "reference"  # Just pointer/title
    SKIP = "skip"  # Omit entirely (redundant, noise)


@dataclass
class SelectionPolicy:
    """Rules for selective intelligence by content type."""
    node_type: NodeType
    detail_level: ContentDetail
    min_confidence: float = 0.6
    max_summary_ratio: float = 0.3  # Compress to 30% of original

    def should_include(self, confidence: float) -> bool:
        """Should this content be included?"""
        return confidence >= self.min_confidence and self.detail_level != ContentDetail.SKIP


class SelectiveIntelligence:
    """
    Decide what content needs full detail vs summaries.

    Strategy: Technical content keeps structure; narrative gets summarized.
    """

    def __init__(self):
        # Default policies: what detail for each content type
        self.policies: Dict[NodeType, SelectionPolicy] = {
            # Technical (keep full detail - lossless)
            NodeType.CODE: SelectionPolicy(NodeType.CODE, ContentDetail.FULL, min_confidence=0.5),
            NodeType.CONFIG: SelectionPolicy(NodeType.CONFIG, ContentDetail.FULL, min_confidence=0.5),
            NodeType.LOG: SelectionPolicy(NodeType.LOG, ContentDetail.FULL, min_confidence=0.5),
            NodeType.TABLE: SelectionPolicy(NodeType.TABLE, ContentDetail.FULL, min_confidence=0.6),
            # Structured (keep significant detail)
            NodeType.SECTION: SelectionPolicy(NodeType.SECTION, ContentDetail.FULL, min_confidence=0.6),
            NodeType.FIGURE: SelectionPolicy(NodeType.FIGURE, ContentDetail.SUMMARY, min_confidence=0.6),
            NodeType.CAPTION: SelectionPolicy(NodeType.CAPTION, ContentDetail.SUMMARY, min_confidence=0.6),
            # Narrative (compress heavily)
            NodeType.NARRATIVE: SelectionPolicy(NodeType.NARRATIVE, ContentDetail.SUMMARY, min_confidence=0.6),
            NodeType.FOOTNOTE: SelectionPolicy(NodeType.FOOTNOTE, ContentDetail.REFERENCE, min_confidence=0.7),
            NodeType.REFERENCE: SelectionPolicy(NodeType.REFERENCE, ContentDetail.REFERENCE, min_confidence=0.7),
        }

    def select_detail_level(self, node_type: NodeType, confidence: float) -> ContentDetail:
        """
        Determine detail level for content.

        Args:
            node_type: Type of node
            confidence: Confidence score (0.0-1.0)

        Returns:
            ContentDetail level (FULL, SUMMARY, REFERENCE, SKIP)
        """
        if node_type not in self.policies:
            return ContentDetail.SUMMARY

        policy = self.policies[node_type]

        # If confidence too low, skip or reference only
        if not policy.should_include(confidence):
            return ContentDetail.SKIP if confidence < 0.3 else ContentDetail.REFERENCE

        return policy.detail_level

    def customize_policy(self, node_type: NodeType, detail: ContentDetail, min_confidence: float = 0.6) -> None:
        """Allow customization of policies per use case."""
        self.policies[node_type] = SelectionPolicy(node_type, detail, min_confidence)


class ContentSelector:
    """
    Select content based on selective intelligence policies.

    Output: For each chunk, what compression strategy to apply.
    """

    def __init__(self, intelligence: Optional[SelectiveIntelligence] = None):
        self.intelligence = intelligence or SelectiveIntelligence()

    def select_for_rag(
        self, node_type: NodeType, confidence: float, content_length: int
    ) -> Dict[str, any]:
        """
        Select content for RAG with recommendations.

        Returns:
            {
                "include": bool,
                "detail_level": ContentDetail,
                "compression_ratio": float,
                "estimated_tokens": int,
                "priority": float (0-1, higher = include first)
            }
        """
        detail = self.intelligence.select_detail_level(node_type, confidence)

        # Determine compression based on detail level
        compression_ratios = {
            ContentDetail.FULL: 1.0,  # 100% (no compression)
            ContentDetail.SUMMARY: 0.3,  # 30% (aggressive)
            ContentDetail.REFERENCE: 0.1,  # 10% (title only)
            ContentDetail.SKIP: 0.0,
        }

        compression_ratio = compression_ratios[detail]

        # Rough token estimate (1 token ≈ 4 chars)
        estimated_tokens = int(content_length / 4 * compression_ratio)

        # Priority: high confidence + high detail + important type
        type_priorities = {
            NodeType.CODE: 0.95,
            NodeType.CONFIG: 0.9,
            NodeType.LOG: 0.85,
            NodeType.SECTION: 0.8,
            NodeType.TABLE: 0.8,
            NodeType.FIGURE: 0.5,
            NodeType.NARRATIVE: 0.6,
            NodeType.CAPTION: 0.4,
            NodeType.FOOTNOTE: 0.2,
            NodeType.REFERENCE: 0.1,
        }

        type_priority = type_priorities.get(node_type, 0.5)
        overall_priority = confidence * type_priority * (compression_ratio if compression_ratio > 0 else 0)

        return {
            "include": detail != ContentDetail.SKIP,
            "detail_level": detail.value,
            "compression_ratio": compression_ratio,
            "estimated_tokens": estimated_tokens,
            "priority": min(1.0, overall_priority),
        }

    def select_batch(
        self, nodes: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Select multiple nodes, returning selection decisions.

        Args:
            nodes: List of {node_type, confidence, content_length, ...}

        Returns:
            List of {**node, **selection_decision}
        """
        selections = []

        for node in nodes:
            selection = self.select_for_rag(
                node["node_type"],
                node.get("confidence", 0.5),
                len(node.get("content", "")),
            )
            selections.append({**node, **selection})

        # Sort by priority for retrieval order
        selections.sort(key=lambda x: x["priority"], reverse=True)

        return selections
