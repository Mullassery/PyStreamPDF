"""Citation network extraction and analysis."""

from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class CitationRelation(str, Enum):
    """Type of citation relationship."""
    CITES = "cites"
    CITED_BY = "cited_by"
    RELATED_TO = "related_to"


@dataclass
class Citation:
    """Citation relationship between papers."""
    source_paper: str
    target_paper: str
    relation: CitationRelation


class CitationNetwork:
    """Citation network for papers and documents."""

    def __init__(self):
        """Initialize citation network."""
        self.citations: List[Citation] = []
        self.papers: Dict[str, Dict] = {}

    def add_paper(self, paper_id: str, title: str = "", year: Optional[int] = None):
        """Add paper to network."""
        self.papers[paper_id] = {"title": title, "year": year}

    def add_citation(self, source: str, target: str, relation: CitationRelation = CitationRelation.CITES):
        """Add citation."""
        citation = Citation(source_paper=source, target_paper=target, relation=relation)
        self.citations.append(citation)
