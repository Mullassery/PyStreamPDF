"""Entity extraction and classification for PDF content.

Extract named entities (people, organizations, concepts) from PDF text
and classify them by type with confidence scores.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class EntityType(str, Enum):
    """Type of extracted entity."""
    PERSON = "person"  # Author names, researchers
    ORGANIZATION = "organization"  # Universities, companies
    LOCATION = "location"  # Geographic locations
    CONCEPT = "concept"  # Technical concepts, methods
    METHOD = "method"  # Algorithms, techniques
    METRIC = "metric"  # Performance measures, datasets
    MEASUREMENT = "measurement"  # Numerical measurements
    DATE = "date"  # Dates and time references
    REFERENCE = "reference"  # Citations, bibliographic references
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class Entity:
    """Extracted entity from PDF text."""
    name: str
    type: EntityType
    confidence: float  # 0-1, confidence in extraction
    context: Optional[str] = None  # Surrounding text for context
    page: Optional[int] = None
    frequency: int = 1  # How many times appears in document
    aliases: List[str] = field(default_factory=list)  # Alternative names


class ConceptExtractor:
    """Extract named entities and concepts from PDF text.

    Uses pattern matching and keyword detection to identify:
    - People (capitalized names with common patterns)
    - Organizations (capitalized acronyms, "Inc", "University")
    - Concepts (technical terms, domain-specific vocabulary)
    - Methods (algorithms, techniques)
    - Metrics (datasets, benchmarks)
    """

    def __init__(self, min_confidence: float = 0.6):
        """Initialize concept extractor.

        Args:
            min_confidence: Minimum confidence threshold (0-1)
        """
        self.min_confidence = min_confidence
        self.entities: Dict[str, Entity] = {}

        # Pattern definitions
        self.patterns = {
            "person": r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
            "organization": r"\b([A-Z][A-Z]+(?:\s+Inc\.?|Corporation|LLC|Ltd\.?|University)?)\b",
            "acronym": r"\b([A-Z]{2,}(?:Net|ML|AI|DB)?)\b",
            "date": r"\b((?:19|20)\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2})\b",
        }

        # Domain-specific keywords
        self.concept_keywords = {
            "neural network": ("method", 0.9),
            "deep learning": ("method", 0.9),
            "transformer": ("method", 0.85),
            "attention mechanism": ("method", 0.85),
            "recurrent": ("concept", 0.8),
            "convolution": ("concept", 0.8),
            "embedding": ("concept", 0.75),
            "gradient descent": ("method", 0.85),
            "backpropagation": ("method", 0.85),
            "dataset": ("metric", 0.7),
            "benchmark": ("metric", 0.7),
            "accuracy": ("metric", 0.8),
            "precision": ("metric", 0.8),
            "recall": ("metric", 0.8),
            "F1 score": ("metric", 0.85),
        }

        self.metric_keywords = [
            "accuracy", "precision", "recall", "f1", "loss", "auc", "roc",
            "bleu", "rouge", "perplexity", "latency", "throughput"
        ]

    def extract(self, text: str, page: Optional[int] = None) -> List[Entity]:
        """Extract entities from text.

        Args:
            text: Text to analyze
            page: Page number (for reference)

        Returns:
            List of extracted entities
        """
        extracted = []

        # Extract domain-specific concepts
        for keyword, (etype, confidence) in self.concept_keywords.items():
            if keyword.lower() in text.lower():
                entity = Entity(
                    name=keyword,
                    type=EntityType(etype),
                    confidence=confidence,
                    context=self._get_context(text, keyword),
                    page=page,
                )
                extracted.append(entity)

        # Extract dates
        dates = self._extract_dates(text, page)
        extracted.extend(dates)

        # Extract metrics
        metrics = self._extract_metrics(text, page)
        extracted.extend(metrics)

        # Extract people (simple pattern)
        people = self._extract_people(text, page)
        extracted.extend(people)

        # Extract organizations
        orgs = self._extract_organizations(text, page)
        extracted.extend(orgs)

        # Filter by confidence and deduplicate
        extracted = [e for e in extracted if e.confidence >= self.min_confidence]
        extracted = self._deduplicate(extracted)

        return extracted

    def _extract_dates(self, text: str, page: Optional[int] = None) -> List[Entity]:
        """Extract date references."""
        dates = []
        matches = re.finditer(self.patterns["date"], text)
        for match in matches:
            date_str = match.group(0)
            entity = Entity(
                name=date_str,
                type=EntityType.DATE,
                confidence=0.9,
                context=self._get_context(text, date_str),
                page=page,
            )
            dates.append(entity)
        return dates

    def _extract_metrics(self, text: str, page: Optional[int] = None) -> List[Entity]:
        """Extract performance metrics and measurements."""
        metrics = []
        for keyword in self.metric_keywords:
            if keyword.lower() in text.lower():
                # Look for numbers near the metric
                pattern = rf"{keyword}\s*(?:of|=|is)?\s*([\d.]+)%?"
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    full_text = match.group(0)
                    entity = Entity(
                        name=full_text,
                        type=EntityType.METRIC,
                        confidence=0.85,
                        context=self._get_context(text, full_text),
                        page=page,
                    )
                    metrics.append(entity)
        return metrics

    def _extract_people(self, text: str, page: Optional[int] = None) -> List[Entity]:
        """Extract person names using pattern matching."""
        people = []
        matches = re.finditer(self.patterns["person"], text)
        for match in matches:
            name = match.group(0)
            # Simple heuristic: if both parts capitalized, likely a name
            if len(name.split()) >= 2:
                entity = Entity(
                    name=name,
                    type=EntityType.PERSON,
                    confidence=0.7,
                    context=self._get_context(text, name),
                    page=page,
                )
                people.append(entity)
        return people

    def _extract_organizations(self, text: str, page: Optional[int] = None) -> List[Entity]:
        """Extract organization names."""
        orgs = []

        # Look for common organization patterns
        org_patterns = [
            r"\b([A-Z][a-z]+\s+(?:University|College|Institute|Labs?))\b",
            r"\b([A-Z]{2,}\s+(?:Inc|Corp|Ltd|LLC))\b",
            r"\b(?:Google|Apple|Microsoft|Facebook|Amazon|OpenAI|DeepMind|Meta)\b",
        ]

        for pattern in org_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(0)
                entity = Entity(
                    name=name,
                    type=EntityType.ORGANIZATION,
                    confidence=0.8,
                    context=self._get_context(text, name),
                    page=page,
                )
                orgs.append(entity)

        return orgs

    def _get_context(self, text: str, entity_name: str, window: int = 50) -> str:
        """Get surrounding text context for entity."""
        idx = text.lower().find(entity_name.lower())
        if idx == -1:
            return ""

        start = max(0, idx - window)
        end = min(len(text), idx + len(entity_name) + window)
        return text[start:end].strip()

    def _deduplicate(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities, keeping highest confidence."""
        seen: Dict[str, Entity] = {}
        for entity in sorted(entities, key=lambda e: -e.confidence):
            key = entity.name.lower()
            if key not in seen:
                seen[key] = entity
            else:
                # Merge frequency counts
                seen[key].frequency += entity.frequency
                if entity.confidence > seen[key].confidence:
                    seen[key].confidence = entity.confidence

        return list(seen.values())

    def batch_extract(self, texts: List[Tuple[str, Optional[int]]]) -> List[Entity]:
        """Extract entities from multiple texts.

        Args:
            texts: List of (text, page_number) tuples

        Returns:
            Combined list of entities from all texts
        """
        all_entities = []
        for text, page in texts:
            entities = self.extract(text, page)
            all_entities.extend(entities)

        # Final deduplication across all texts
        return self._deduplicate(all_entities)

    def get_entities_by_type(self, entities: List[Entity], entity_type: EntityType) -> List[Entity]:
        """Filter entities by type.

        Args:
            entities: List of entities
            entity_type: Type to filter for

        Returns:
            Filtered entities
        """
        return [e for e in entities if e.type == entity_type]

    def get_top_entities(self, entities: List[Entity], limit: int = 10) -> List[Entity]:
        """Get top entities by frequency.

        Args:
            entities: List of entities
            limit: Number to return

        Returns:
            Top entities by frequency
        """
        return sorted(entities, key=lambda e: -e.frequency)[:limit]
