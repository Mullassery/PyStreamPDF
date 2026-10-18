"""Citation network extraction and analysis."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
        self.citations: list[Citation] = []
        self.papers: dict[str, dict] = {}

    def add_paper(self, paper_id: str, title: str = "", year: Optional[int] = None):
        """Add paper to network."""
        self.papers[paper_id] = {"title": title, "year": year}

    def add_citation(self, source: str, target: str, relation: CitationRelation = CitationRelation.CITES):
        """Add citation."""
        citation = Citation(source_paper=source, target_paper=target, relation=relation)
        self.citations.append(citation)

    def top_cited(self, limit: int = 3) -> list[str]:
        """Return formatted labels for the most-cited papers in the network (PYSTREAMPDF-006)."""
        counts: dict[str, int] = {}
        for c in self.citations:
            if c.relation == CitationRelation.CITES:
                counts[c.target_paper] = counts.get(c.target_paper, 0) + 1
            elif c.relation == CitationRelation.CITED_BY:
                counts[c.source_paper] = counts.get(c.source_paper, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[: max(0, limit)]
        results: list[str] = []
        for pid, count in ranked:
            meta = self.papers.get(pid, {})
            title = meta.get("title") or pid
            year = meta.get("year")
            if year is not None:
                results.append(f"{title} ({year}, {count} citations)")
            else:
                results.append(f"{title} ({count} citations)")
        return results
