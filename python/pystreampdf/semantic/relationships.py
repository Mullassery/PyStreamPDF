"""Relationship extraction from PDF content.

Detect relationships between entities (cites, extends, refutes, etc.)
using pattern matching and syntactic analysis.
"""

from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re


class RelationType(str, Enum):
    """Type of relationship between entities."""
    CITES = "cites"  # Entity A cites entity B
    CITED_BY = "cited_by"  # Entity A is cited by entity B
    EXTENDS = "extends"  # Entity A extends entity B's work
    EXTENDS_BY = "extends_by"  # Entity A is extended by entity B
    REFUTES = "refutes"  # Entity A contradicts entity B
    REFUTED_BY = "refuted_by"  # Entity A is refuted by entity B
    REFINES = "refines"  # Entity A improves on entity B
    REFINED_BY = "refined_by"  # Entity A is refined by entity B
    USES = "uses"  # Entity A uses entity B
    USED_BY = "used_by"  # Entity A is used by entity B
    ENABLES = "enables"  # Entity A makes entity B possible
    ENABLED_BY = "enabled_by"  # Entity A is enabled by entity B
    RELATED_TO = "related_to"  # General relationship
    AUTHOR_OF = "author_of"  # Entity A is author of entity B
    AUTHORED_BY = "authored_by"  # Entity A is authored by entity B


@dataclass
class Relationship:
    """Relationship between two entities."""
    entity_a: str
    entity_b: str
    relation_type: RelationType
    confidence: float  # 0-1
    evidence: Optional[str] = None  # Supporting text
    distance: int = 1  # Token distance between entities


class RelationshipExtractor:
    """Extract relationships between entities.

    Uses pattern matching and syntactic analysis to detect relationships.
    Supports multiple relationship types with confidence scoring.
    """

    def __init__(self, min_confidence: float = 0.6):
        """Initialize relationship extractor.

        Args:
            min_confidence: Minimum confidence threshold for relationships
        """
        self.min_confidence = min_confidence
        self.relationships: Dict[Tuple[str, str], Relationship] = {}

        # Relationship pattern templates
        self.patterns = {
            RelationType.CITES: [
                r"\b(\w+(?:\s+\w+)?)\s+(?:cites?|cited?|refers?|reference[sd]?)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\b",
                r"(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:is|was)\s+cited\s+by\s+(\w+(?:\s+\w+)?)",
            ],
            RelationType.EXTENDS: [
                r"(?:building\s+on|extends?|builds?|improves?\s+on|based\s+on)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:with|through)\s+(\w+(?:\s+\w+)?)",
                r"(\w+(?:\s+\w+)?)\s+(?:extends?|generalizes?|improves?)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
            ],
            RelationType.REFUTES: [
                r"(\w+(?:\s+\w+)?)\s+(?:contradicts?|refutes?|disputes?|challenges?)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
                r"(?:contrary to|in contrast with|unlike)\s+(?:the\s+)?(\w+(?:\s+\w+)?),\s+(\w+(?:\s+\w+)?)",
            ],
            RelationType.USES: [
                r"(\w+(?:\s+\w+)?)\s+(?:uses?|utilizes?|employs?|leverages?)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
                r"(?:using|via|through)\s+(\w+(?:\s+\w+)?)\s+(?:to\s+)?(?:perform|achieve|compute)\s+(\w+(?:\s+\w+)?)",
            ],
            RelationType.ENABLES: [
                r"(\w+(?:\s+\w+)?)\s+(?:enables?|allows?|facilitates?|makes\s+possible)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
            ],
        }

        # Context window for extracting evidence
        self.context_window = 100  # Characters before/after

    def extract(self, text: str, entities: Optional[List[str]] = None) -> List[Relationship]:
        """Extract relationships from text.

        Args:
            text: Text to analyze
            entities: Optional list of entity names to focus on

        Returns:
            List of detected relationships
        """
        relationships = []

        # Extract using patterns
        for rel_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 2:
                        entity_a = match.group(1)
                        entity_b = match.group(2)

                        # Filter by provided entities if given
                        if entities:
                            if entity_a.lower() not in [e.lower() for e in entities]:
                                continue
                            if entity_b.lower() not in [e.lower() for e in entities]:
                                continue

                        # Extract evidence context
                        start = max(0, match.start() - self.context_window)
                        end = min(len(text), match.end() + self.context_window)
                        evidence = text[start:end].strip()

                        # Determine confidence
                        confidence = self._calculate_confidence(rel_type, entity_a, entity_b, text)

                        if confidence >= self.min_confidence:
                            rel = Relationship(
                                entity_a=entity_a,
                                entity_b=entity_b,
                                relation_type=rel_type,
                                confidence=confidence,
                                evidence=evidence,
                                distance=match.end() - match.start(),
                            )
                            relationships.append(rel)

        # Deduplicate relationships
        return self._deduplicate(relationships)

    def _calculate_confidence(self, rel_type: RelationType, entity_a: str, entity_b: str, text: str) -> float:
        """Calculate confidence score for relationship.

        Args:
            rel_type: Type of relationship
            entity_a: First entity
            entity_b: Second entity
            text: Full text context

        Returns:
            Confidence score (0-1)
        """
        base_confidence = {
            RelationType.CITES: 0.85,
            RelationType.EXTENDS: 0.80,
            RelationType.REFUTES: 0.75,
            RelationType.USES: 0.75,
            RelationType.ENABLES: 0.70,
            RelationType.RELATED_TO: 0.60,
        }

        confidence = base_confidence.get(rel_type, 0.60)

        # Boost if entities are capitalized (proper nouns)
        if entity_a[0].isupper() and entity_b[0].isupper():
            confidence += 0.05

        # Boost if exact case match in text
        if entity_a in text and entity_b in text:
            confidence += 0.05

        return min(1.0, confidence)

    def find_relations(self, entity1: str, entity2: str, text: str) -> List[Relationship]:
        """Find specific relationships between two entities.

        Args:
            entity1: First entity name
            entity2: Second entity name
            text: Text context

        Returns:
            List of relationships between the entities
        """
        rels = self.extract(text, [entity1, entity2])
        return [
            r for r in rels
            if (r.entity_a.lower() == entity1.lower() and r.entity_b.lower() == entity2.lower())
            or (r.entity_a.lower() == entity2.lower() and r.entity_b.lower() == entity1.lower())
        ]

    def batch_extract(self, texts: List[Tuple[str, Optional[int]]]) -> List[Relationship]:
        """Extract relationships from multiple texts.

        Args:
            texts: List of (text, source_id) tuples

        Returns:
            Combined relationships from all texts
        """
        all_rels = []
        for text, source_id in texts:
            rels = self.extract(text)
            # Tag with source
            for rel in rels:
                rel.evidence = f"[Source {source_id}] {rel.evidence}"
            all_rels.extend(rels)

        return self._deduplicate(all_rels)

    def _deduplicate(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships, keeping highest confidence.

        Args:
            relationships: List of relationships

        Returns:
            Deduplicated relationships
        """
        seen: Dict[Tuple[str, str, str], Relationship] = {}

        for rel in sorted(relationships, key=lambda r: -r.confidence):
            key = (rel.entity_a.lower(), rel.entity_b.lower(), rel.relation_type.value)
            if key not in seen:
                seen[key] = rel

        return list(seen.values())

    def get_related_entities(self, entity: str, relationships: List[Relationship]) -> Dict[RelationType, Set[str]]:
        """Get all entities related to a given entity.

        Args:
            entity: Entity name to find relations for
            relationships: List of relationships to search

        Returns:
            Dict mapping relationship types to related entity names
        """
        related = {}

        for rel in relationships:
            if rel.entity_a.lower() == entity.lower():
                rel_type = rel.relation_type
                if rel_type not in related:
                    related[rel_type] = set()
                related[rel_type].add(rel.entity_b)

            elif rel.entity_b.lower() == entity.lower():
                # Reverse the relationship type
                rel_type = self._reverse_relation_type(rel.relation_type)
                if rel_type not in related:
                    related[rel_type] = set()
                related[rel_type].add(rel.entity_a)

        return related

    @staticmethod
    def _reverse_relation_type(rel_type: RelationType) -> RelationType:
        """Get reverse of a relationship type.

        Args:
            rel_type: Original relationship type

        Returns:
            Reversed relationship type
        """
        reverse_map = {
            RelationType.CITES: RelationType.CITED_BY,
            RelationType.CITED_BY: RelationType.CITES,
            RelationType.EXTENDS: RelationType.EXTENDS_BY,
            RelationType.EXTENDS_BY: RelationType.EXTENDS,
            RelationType.REFUTES: RelationType.REFUTED_BY,
            RelationType.REFUTED_BY: RelationType.REFUTES,
            RelationType.USES: RelationType.USED_BY,
            RelationType.USED_BY: RelationType.USES,
            RelationType.ENABLES: RelationType.ENABLED_BY,
            RelationType.ENABLED_BY: RelationType.ENABLES,
            RelationType.AUTHOR_OF: RelationType.AUTHORED_BY,
            RelationType.AUTHORED_BY: RelationType.AUTHOR_OF,
            RelationType.REFINES: RelationType.REFINED_BY,
            RelationType.REFINED_BY: RelationType.REFINES,
            RelationType.RELATED_TO: RelationType.RELATED_TO,
        }
        return reverse_map.get(rel_type, rel_type)
