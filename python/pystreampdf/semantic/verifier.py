"""Fact verification and hallucination prevention.

Verify claims against source documents to prevent hallucinations
and provide grounding/evidence for AI-generated content.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VerificationStatus(str, Enum):
    """Status of claim verification."""
    GROUNDED = "grounded"  # Claim is supported by sources
    PARTIALLY_GROUNDED = "partially_grounded"  # Some evidence found
    NOT_GROUNDED = "not_grounded"  # No supporting evidence
    REFUTED = "refuted"  # Directly contradicted by sources
    UNCERTAIN = "uncertain"  # Insufficient evidence


@dataclass
class Evidence:
    """Evidence supporting or refuting a claim."""
    text: str  # Source text
    source_id: Optional[int] = None  # Which chunk/page
    support_level: float = 0.5  # 0=refutes, 0.5=neutral, 1=supports
    relevance: float = 0.5  # How directly relevant (0-1)


@dataclass
class VerificationResult:
    """Result of fact verification."""
    claim: str
    status: VerificationStatus
    confidence: float  # 0-1, overall confidence
    grounded: bool  # Is claim grounded in sources?
    evidence: list[Evidence] = field(default_factory=list)
    supporting_facts: list[str] = field(default_factory=list)  # Key pieces of evidence
    refuting_facts: list[str] = field(default_factory=list)  # Contradictions
    sources: list[int] = field(default_factory=list)  # Source IDs (chunk numbers)


class FactVerifier:
    """Verify claims against source documents.

    Checks whether claims are grounded in source material and
    prevents LLM hallucinations by verifying outputs.
    """

    def __init__(self, source_chunks: Optional[list[tuple[str, int]]] = None):
        """Initialize verifier.

        Args:
            source_chunks: List of (text, source_id) tuples
        """
        self.sources = source_chunks or []
        self.claim_cache: dict[str, VerificationResult] = {}

    def verify(self, claim: str) -> VerificationResult:
        """Verify a claim against source documents.

        Args:
            claim: Claim to verify

        Returns:
            VerificationResult with grounding evidence
        """
        # Check cache
        claim_key = claim.lower().strip()
        if claim_key in self.claim_cache:
            return self.claim_cache[claim_key]

        if not self.sources:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.UNCERTAIN,
                confidence=0.0,
                grounded=False,
            )

        # Extract key terms from claim
        key_terms = self._extract_key_terms(claim)

        # Search for evidence
        evidence_list = self._find_evidence(claim, key_terms)

        # Analyze evidence
        result = self._analyze_evidence(claim, evidence_list)

        # Cache result
        self.claim_cache[claim_key] = result

        return result

    def verify_batch(self, claims: list[str]) -> list[VerificationResult]:
        """Verify multiple claims.

        Args:
            claims: List of claims to verify

        Returns:
            List of verification results
        """
        return [self.verify(claim) for claim in claims]

    def get_evidence_for_term(self, term: str, top_k: int = 5) -> list[Evidence]:
        """Get evidence for a specific term.

        Args:
            term: Term to find evidence for
            top_k: Number of evidence items to return

        Returns:
            List of relevant evidence items
        """
        evidence_list = []

        for source_text, source_id in self.sources:
            if term.lower() in source_text.lower():
                # Find the specific context
                pattern = rf".{{0,100}}{re.escape(term)}.{{0,100}}"
                matches = re.finditer(pattern, source_text, re.IGNORECASE)

                for match in matches:
                    evidence = Evidence(
                        text=match.group(0),
                        source_id=source_id,
                        relevance=self._calculate_relevance(term, match.group(0)),
                    )
                    evidence_list.append(evidence)

        # Sort by relevance and return top K
        return sorted(evidence_list, key=lambda e: -e.relevance)[:top_k]

    def is_hallucination(self, claim: str, threshold: float = 0.3) -> bool:
        """Check if a claim is likely a hallucination.

        Args:
            claim: Claim to check
            threshold: Confidence threshold below which it's hallucination

        Returns:
            True if claim is likely hallucinated
        """
        result = self.verify(claim)
        return (
            result.status in [VerificationStatus.NOT_GROUNDED, VerificationStatus.REFUTED]
            or result.confidence < threshold
        )

    def _extract_key_terms(self, claim: str) -> list[str]:
        """Extract key terms from claim for searching.

        Args:
            claim: Claim text

        Returns:
            List of important terms
        """
        # Remove common words
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can", "and", "or",
            "but", "in", "on", "at", "to", "for", "of", "with", "by"
        }

        # Split into words and filter
        words = claim.lower().split()
        terms = [w.strip(".,!?;:") for w in words if w.lower() not in stopwords and len(w) > 2]

        # Return top terms (by frequency in claim)
        return sorted(set(terms), key=lambda t: -len(t))[:10]

    def _find_evidence(self, claim: str, key_terms: list[str]) -> list[Evidence]:
        """Find evidence for a claim in source documents.

        Args:
            claim: Claim to find evidence for
            key_terms: Key terms to search for

        Returns:
            List of evidence items
        """
        evidence_list = []
        claim_lower = claim.lower()

        for source_text, source_id in self.sources:
            source_lower = source_text.lower()

            # Direct match (strongest evidence)
            if claim_lower in source_lower or any(term in source_lower for term in key_terms):
                # Find exact context
                start = max(0, source_lower.find(claim_lower) if claim_lower in source_lower else 0)
                end = min(len(source_text), start + len(claim) + 100)

                evidence = Evidence(
                    text=source_text[start:end],
                    source_id=source_id,
                    support_level=self._calculate_support_level(claim, source_text),
                    relevance=0.9,  # Direct match is highly relevant
                )
                evidence_list.append(evidence)

        return evidence_list

    def _calculate_support_level(self, claim: str, source_text: str) -> float:
        """Calculate how much source supports or refutes claim.

        Args:
            claim: Claim being verified
            source_text: Source text

        Returns:
            Support level (0=refutes, 0.5=neutral, 1=supports)
        """
        claim_lower = claim.lower()
        source_lower = source_text.lower()

        # Check for refuting keywords
        refute_keywords = ["not", "no", "does not", "did not", "cannot", "impossible", "contradicts", "refutes"]
        for keyword in refute_keywords:
            if keyword in source_lower and claim_lower in source_lower:
                return 0.1  # Refutes

        # Check for supporting keywords
        support_keywords = ["confirms", "supports", "shows", "demonstrates", "proves", "validates", "enables", "allows"]
        for keyword in support_keywords:
            if keyword in source_lower:
                return 0.9  # Supports

        # Default: neutral/ambiguous
        return 0.5

    def _calculate_relevance(self, term: str, context: str) -> float:
        """Calculate how relevant a piece of context is to a term.

        Args:
            term: Search term
            context: Context text

        Returns:
            Relevance score (0-1)
        """
        if term.lower() not in context.lower():
            return 0.0

        # Longer context = more relevant
        relevance = min(1.0, len(context) / 200.0)

        # Exact case match = more relevant
        if term in context:
            relevance = min(1.0, relevance + 0.1)

        return relevance

    def _analyze_evidence(self, claim: str, evidence_list: list[Evidence]) -> VerificationResult:
        """Analyze evidence to determine claim status.

        Args:
            claim: Claim being verified
            evidence_list: List of evidence items

        Returns:
            VerificationResult with analysis
        """
        if not evidence_list:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.NOT_GROUNDED,
                confidence=0.0,
                grounded=False,
            )

        # Calculate average support level
        support_levels = [e.support_level for e in evidence_list]
        avg_support = sum(support_levels) / len(support_levels)

        # Determine status
        if avg_support > 0.7:
            status = VerificationStatus.GROUNDED
            confidence = min(1.0, len(evidence_list) * 0.3)
        elif avg_support > 0.4:
            status = VerificationStatus.PARTIALLY_GROUNDED
            confidence = 0.5
        elif avg_support > 0.2:
            status = VerificationStatus.REFUTED
            confidence = 0.8
        else:
            status = VerificationStatus.NOT_GROUNDED
            confidence = 0.1

        # Extract supporting facts
        supporting = [e.text for e in evidence_list if e.support_level > 0.6]
        refuting = [e.text for e in evidence_list if e.support_level < 0.4]

        # Source IDs
        source_ids = sorted({e.source_id for e in evidence_list if e.source_id is not None})

        return VerificationResult(
            claim=claim,
            status=status,
            confidence=confidence,
            grounded=status in [VerificationStatus.GROUNDED, VerificationStatus.PARTIALLY_GROUNDED],
            evidence=evidence_list,
            supporting_facts=supporting[:3],  # Top 3
            refuting_facts=refuting[:3],  # Top 3
            sources=source_ids,
        )

    def generate_verification_report(self, claims: list[str]) -> dict:
        """Generate comprehensive verification report for multiple claims.

        Args:
            claims: List of claims to verify

        Returns:
            Report with statistics and details
        """
        results = self.verify_batch(claims)

        grounded_count = sum(1 for r in results if r.grounded)
        refuted_count = sum(1 for r in results if r.status == VerificationStatus.REFUTED)
        uncertain_count = sum(1 for r in results if r.status == VerificationStatus.UNCERTAIN)

        return {
            "total_claims": len(claims),
            "grounded": grounded_count,
            "grounded_percent": (grounded_count / len(claims)) * 100 if claims else 0,
            "refuted": refuted_count,
            "uncertain": uncertain_count,
            "avg_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
            "results": results,
        }
