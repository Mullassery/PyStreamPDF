"""Intelligent context assembly for queries.

Assemble optimal context for AI queries using multiple strategies:
- Scholarly: Cite important papers/concepts first
- Technical: Focus on implementation details
- Survey: Broad coverage of topic
- Tutorial: Progressive complexity
"""

from typing import List, Optional, Dict, Tuple, Set, Any
from enum import Enum
from dataclasses import dataclass, field


class AssemblyStrategy(str, Enum):
    """Strategy for assembling context."""
    SCHOLARLY = "scholarly"  # Citation importance first
    TECHNICAL = "technical"  # Implementation details
    SURVEY = "survey"  # Broad coverage
    TUTORIAL = "tutorial"  # Progressive complexity


@dataclass
class AssembledContext:
    """Assembled context from multiple sources."""
    query: str
    content: str  # Full assembled content
    token_count: int
    sources: List[int] = field(default_factory=list)  # Source IDs
    sections: List[str] = field(default_factory=list)  # Logical sections
    coverage: float = 0.0  # Coverage score (0-1)
    coherence: float = 0.0  # Coherence score (0-1)
    strategy: str = "scholarly"


class ContextAssembler:
    """Intelligently assemble context for queries.

    Combines extraction, relationships, graphs, and citations to build
    optimal context for AI agent queries using multiple strategies.
    """

    def __init__(self, knowledge_graph=None, citation_network=None, chunks: Optional[List[Tuple[str, int]]] = None, token_budget_config=None):
        """Initialize assembler.

        Args:
            knowledge_graph: KnowledgeGraph instance
            citation_network: CitationNetwork instance
            chunks: List of (text, source_id) tuples
            token_budget_config: Optional TokenBudgetConfig for dynamic budget evaluation
        """
        self.graph = knowledge_graph
        self.citations = citation_network
        self.chunks = chunks or []
        self.token_budget_config = token_budget_config

        # Token estimation
        self.avg_tokens_per_char = 1 / 4.0  # Approximate: 4 chars per token

    def assemble(
        self,
        query: str,
        max_tokens: int = 2000,
        strategy: AssemblyStrategy = AssemblyStrategy.SCHOLARLY,
        document_context: Optional[Dict[str, Any]] = None,
    ) -> AssembledContext:
        """Assemble optimal context for query.

        Args:
            query: Query/question to build context for
            max_tokens: Maximum tokens to include (can be overridden by token_budget_config)
            strategy: Assembly strategy to use
            document_context: Optional dict with 'filename', 'title', 'content_preview' for budget evaluation

        Returns:
            AssembledContext with assembled content
        """
        evaluated_max_tokens = max_tokens
        if self.token_budget_config and document_context:
            evaluated_max_tokens = self.token_budget_config.evaluate(
                filename=document_context.get("filename", ""),
                title=document_context.get("title"),
                content_preview=document_context.get("content_preview"),
            )

        if strategy == AssemblyStrategy.SCHOLARLY:
            return self._assemble_scholarly(query, evaluated_max_tokens)
        elif strategy == AssemblyStrategy.TECHNICAL:
            return self._assemble_technical(query, evaluated_max_tokens)
        elif strategy == AssemblyStrategy.SURVEY:
            return self._assemble_survey(query, evaluated_max_tokens)
        elif strategy == AssemblyStrategy.TUTORIAL:
            return self._assemble_tutorial(query, evaluated_max_tokens)
        else:
            return self._assemble_scholarly(query, evaluated_max_tokens)

    def _assemble_scholarly(self, query: str, max_tokens: int) -> AssembledContext:
        """Assemble using scholarly strategy (citation importance).

        Args:
            query: Query string
            max_tokens: Max tokens

        Returns:
            AssembledContext
        """
        sections = []
        sources = set()
        total_tokens = 0

        # 1. Get related concepts from graph
        if self.graph:
            related = self.graph.query(query.lower(), depth=2)
            # Sort by importance (in-degree)
            concepts = []
            for rel_type, neighbors in related.items():
                for neighbor, confidence in neighbors:
                    if neighbor in self.graph.nodes:
                        node = self.graph.nodes[neighbor]
                        concepts.append((neighbor, node.in_degree, confidence))

            concepts = sorted(concepts, key=lambda x: -x[1])[:10]

            # Add concept introductions
            for concept, _, confidence in concepts:
                for source_text, source_id in self.chunks:
                    if concept.lower() in source_text.lower():
                        tokens = int(len(source_text) * self.avg_tokens_per_char)
                        if total_tokens + tokens <= max_tokens:
                            sections.append(f"**{concept}**: {source_text[:200]}...")
                            total_tokens += tokens
                            sources.add(source_id)
                            break

        # 2. Add citations if available
        if self.citations:
            # Get influential papers
            try:
                influential = self.citations.top_cited(limit=3)
                for paper in influential:
                    sections.append(f"Citation: {paper}")
            except:
                pass

        # 3. Fill remaining space with relevant chunks
        remaining_tokens = max_tokens - total_tokens
        for source_text, source_id in self.chunks:
            if source_id not in sources:
                tokens = int(len(source_text) * self.avg_tokens_per_char)
                if tokens <= remaining_tokens:
                    sections.append(source_text)
                    total_tokens += tokens
                    sources.add(source_id)
                    remaining_tokens -= tokens

        content = "\n\n".join(sections)
        coverage = min(1.0, len(sources) / len(self.chunks)) if self.chunks else 0.0

        return AssembledContext(
            query=query,
            content=content,
            token_count=total_tokens,
            sources=sorted(sources),
            sections=sections,
            coverage=coverage,
            coherence=self._calculate_coherence(sections),
            strategy=AssemblyStrategy.SCHOLARLY.value,
        )

    def _assemble_technical(self, query: str, max_tokens: int) -> AssembledContext:
        """Assemble using technical strategy (implementation details).

        Args:
            query: Query string
            max_tokens: Max tokens

        Returns:
            AssembledContext
        """
        sections = []
        sources = set()
        total_tokens = 0

        # Look for technical keywords
        tech_keywords = ["algorithm", "implementation", "method", "approach", "technique", "code", "function"]

        for source_text, source_id in self.chunks:
            # Prioritize sources with technical content
            has_tech = any(keyword in source_text.lower() for keyword in tech_keywords)

            if has_tech and source_id not in sources:
                tokens = int(len(source_text) * self.avg_tokens_per_char)
                if total_tokens + tokens <= max_tokens:
                    sections.append(source_text)
                    total_tokens += tokens
                    sources.add(source_id)

        # Fill remaining space
        remaining_tokens = max_tokens - total_tokens
        for source_text, source_id in self.chunks:
            if source_id not in sources:
                tokens = int(len(source_text) * self.avg_tokens_per_char)
                if tokens <= remaining_tokens:
                    sections.append(source_text)
                    total_tokens += tokens
                    sources.add(source_id)
                    remaining_tokens -= tokens

        content = "\n\n".join(sections)

        return AssembledContext(
            query=query,
            content=content,
            token_count=total_tokens,
            sources=sorted(sources),
            sections=sections,
            coverage=min(1.0, len(sources) / len(self.chunks)) if self.chunks else 0.0,
            coherence=self._calculate_coherence(sections),
            strategy=AssemblyStrategy.TECHNICAL.value,
        )

    def _assemble_survey(self, query: str, max_tokens: int) -> AssembledContext:
        """Assemble using survey strategy (broad coverage).

        Args:
            query: Query string
            max_tokens: Max tokens

        Returns:
            AssembledContext
        """
        sections = []
        sources = set()
        total_tokens = 0
        chunk_size = max_tokens // min(5, len(self.chunks))  # Max 5 chunks

        # Evenly distribute across all chunks
        for i, (source_text, source_id) in enumerate(self.chunks):
            # Take first chunk_size characters from each
            text_slice = source_text[:int(chunk_size / self.avg_tokens_per_char)]
            tokens = int(len(text_slice) * self.avg_tokens_per_char)

            if total_tokens + tokens <= max_tokens:
                sections.append(text_slice)
                total_tokens += tokens
                sources.add(source_id)

        content = "\n\n".join(sections)

        return AssembledContext(
            query=query,
            content=content,
            token_count=total_tokens,
            sources=sorted(sources),
            sections=sections,
            coverage=len(sources) / len(self.chunks) if self.chunks else 0.0,
            coherence=self._calculate_coherence(sections),
            strategy=AssemblyStrategy.SURVEY.value,
        )

    def _assemble_tutorial(self, query: str, max_tokens: int) -> AssembledContext:
        """Assemble using tutorial strategy (progressive complexity).

        Args:
            query: Query string
            max_tokens: Max tokens

        Returns:
            AssembledContext
        """
        sections = []
        sources = set()
        total_tokens = 0

        # Sort by perceived complexity (shorter = simpler)
        sorted_chunks = sorted(self.chunks, key=lambda x: len(x[0]))

        # Add from simple to complex
        for source_text, source_id in sorted_chunks:
            tokens = int(len(source_text) * self.avg_tokens_per_char)
            if total_tokens + tokens <= max_tokens:
                sections.append(source_text)
                total_tokens += tokens
                sources.add(source_id)

        content = "\n\n".join(sections)

        return AssembledContext(
            query=query,
            content=content,
            token_count=total_tokens,
            sources=sorted(sources),
            sections=sections,
            coverage=len(sources) / len(self.chunks) if self.chunks else 0.0,
            coherence=self._calculate_coherence(sections),
            strategy=AssemblyStrategy.TUTORIAL.value,
        )

    def _calculate_coherence(self, sections: List[str]) -> float:
        """Calculate coherence score of assembled sections.

        Args:
            sections: List of section texts

        Returns:
            Coherence score (0-1)
        """
        if not sections:
            return 0.0

        # Simple coherence: based on section continuity
        # More related sections = higher coherence
        coherence = 0.5  # Base score

        # Bonus for section count (good coverage)
        coherence += min(0.3, len(sections) * 0.05)

        # Bonus for section length consistency
        if sections:
            lengths = [len(s) for s in sections]
            avg_length = sum(lengths) / len(lengths)
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            # Lower variance = higher coherence
            coherence -= min(0.2, variance / 1000000)

        return min(1.0, max(0.0, coherence))

    def estimate_query_cost(self, query: str) -> Dict:
        """Estimate cost/tokens for different strategies.

        Args:
            query: Query string

        Returns:
            Dict with estimated costs for each strategy
        """
        results = {}

        for strategy in AssemblyStrategy:
            assembled = self.assemble(query, max_tokens=2000, strategy=strategy)
            results[strategy.value] = {
                "tokens": assembled.token_count,
                "sources": len(assembled.sources),
                "coverage": assembled.coverage,
                "coherence": assembled.coherence,
            }

        return results

    def optimize_for_budget(self, query: str, max_tokens: int, prefer_coverage: bool = True) -> AssembledContext:
        """Optimize context for token budget.

        Args:
            query: Query string
            max_tokens: Maximum tokens available
            prefer_coverage: Prefer coverage or coherence?

        Returns:
            Best AssembledContext for budget
        """
        best_context = None
        best_score = -1

        for strategy in AssemblyStrategy:
            context = self.assemble(query, max_tokens, strategy)

            # Score based on preference
            if prefer_coverage:
                score = context.coverage * 0.7 + context.coherence * 0.3
            else:
                score = context.coherence * 0.7 + context.coverage * 0.3

            if score > best_score:
                best_score = score
                best_context = context

        return best_context or self.assemble(query, max_tokens, AssemblyStrategy.SCHOLARLY)
