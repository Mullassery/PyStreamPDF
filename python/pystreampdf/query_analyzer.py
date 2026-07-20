"""
Query Analyzer - Auto-detect optimal token budget based on query complexity

Analyzes query keywords and patterns to automatically suggest appropriate
token budget. Supports programmatic override for explicit control.
"""

from typing import Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass


class TokenBudgetLevel(Enum):
    """Token budget levels"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    RICH = "rich"
    COMPREHENSIVE = "comprehensive"


@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    detected_level: TokenBudgetLevel
    confidence: float           # 0.0-1.0 confidence in detection
    matched_keywords: List[str] # Keywords that matched
    query_complexity: str       # "simple", "moderate", "complex", "deep"
    rationale: str             # Human-readable explanation


class QueryAnalyzer:
    """Analyze queries to auto-detect optimal token budget"""

    # Keyword patterns for each token budget level
    KEYWORD_PATTERNS = {
        "minimal": {
            "keywords": [
                "what is", "define", "explain briefly", "quick answer",
                "short", "simple", "one word", "list", "bullet point",
                "lookup", "find", "location", "who", "when", "where"
            ],
            "patterns": [
                r"^what\s+is\s+",  # What is X?
                r"\?\s*$",          # Single question mark
            ],
            "complexity": "simple",
        },
        "standard": {
            "keywords": [
                "explain", "how", "describe", "tell me", "discuss",
                "overview", "summary", "basics", "introduction",
                "why", "what does", "understand", "compare briefly",
                "pros and cons", "advantages disadvantages"
            ],
            "patterns": [
                r"^how\s+",         # How to...
                r"^why\s+",         # Why...
            ],
            "complexity": "moderate",
        },
        "rich": {
            "keywords": [
                "analyze", "detail", "comprehensive", "complex",
                "relationship", "connection", "integration",
                "compare", "contrast", "difference", "similarity",
                "impact", "effect", "consequence", "implications",
                "implementation", "example", "case study"
            ],
            "patterns": [
                r"compare\s+.*\s+and\s+",  # Compare X and Y
                r"analyze\s+",
                r"implement",
            ],
            "complexity": "complex",
        },
        "comprehensive": {
            "keywords": [
                "deep dive", "thorough", "exhaustive", "detailed analysis",
                "research", "investigate", "comprehensive review",
                "all aspects", "full context", "background",
                "complete understanding", "in depth", "full explanation",
                "advanced", "architecture", "design", "system design",
                "best practices", "patterns", "principles"
            ],
            "patterns": [
                r"deep\s+dive",
                r"comprehensive\s+review",
                r"detailed\s+analysis",
            ],
            "complexity": "deep",
        },
    }

    @staticmethod
    def analyze(query: str) -> QueryAnalysis:
        """Analyze query to determine optimal token budget

        Args:
            query: User's search query

        Returns:
            QueryAnalysis with detected level and confidence
        """
        import re

        query_lower = query.lower()
        scores = {}

        # Score each budget level
        for level, patterns in QueryAnalyzer.KEYWORD_PATTERNS.items():
            score = 0.0
            matched = []

            # Check keywords (0.3 weight each)
            for keyword in patterns["keywords"]:
                if keyword in query_lower:
                    score += 0.3
                    matched.append(keyword)

            # Check patterns (0.5 weight each)
            for pattern in patterns["patterns"]:
                if re.search(pattern, query_lower):
                    score += 0.5
                    matched.append(f"pattern:{pattern}")

            # Boost score based on query length
            word_count = len(query.split())
            if word_count > 20:
                score += 0.2  # Long queries often need more context
            elif word_count < 5:
                score -= 0.1  # Short queries often need less

            scores[level] = {
                "score": max(0.0, score),
                "matched": matched,
                "complexity": patterns["complexity"],
            }

        # Find best match
        best_level = max(scores.keys(), key=lambda k: scores[k]["score"])
        best_score = scores[best_level]["score"]
        best_matched = scores[best_level]["matched"]
        best_complexity = scores[best_level]["complexity"]

        # Normalize confidence (0.0-1.0)
        confidence = min(1.0, best_score / 2.0)

        # Generate rationale
        if best_matched:
            matched_str = ", ".join(best_matched[:3])
            if len(best_matched) > 3:
                matched_str += f", +{len(best_matched) - 3} more"
            rationale = f"Detected {best_complexity} query ({matched_str})"
        else:
            rationale = "No specific patterns matched, using default level"

        return QueryAnalysis(
            detected_level=TokenBudgetLevel(best_level),
            confidence=confidence,
            matched_keywords=best_matched,
            query_complexity=best_complexity,
            rationale=rationale,
        )

    @staticmethod
    def suggest_budget(query: str) -> int:
        """Suggest token budget token count for query

        Args:
            query: User's search query

        Returns:
            Suggested token budget in tokens
        """
        from pystreampdf.config import TokenBudgetConfig

        analysis = QueryAnalyzer.analyze(query)
        return TokenBudgetConfig.get_preset(analysis.detected_level.value)

    @staticmethod
    def add_keywords(level: str, keywords: List[str]) -> None:
        """Add custom keywords for a budget level

        Args:
            level: Token budget level ("minimal", "standard", "rich", "comprehensive")
            keywords: List of keywords to add
        """
        if level not in QueryAnalyzer.KEYWORD_PATTERNS:
            raise ValueError(
                f"Unknown level '{level}'. "
                f"Available: {', '.join(QueryAnalyzer.KEYWORD_PATTERNS.keys())}"
            )

        QueryAnalyzer.KEYWORD_PATTERNS[level]["keywords"].extend(keywords)

    @staticmethod
    def remove_keywords(level: str, keywords: List[str]) -> None:
        """Remove keywords from a budget level

        Args:
            level: Token budget level
            keywords: Keywords to remove
        """
        if level not in QueryAnalyzer.KEYWORD_PATTERNS:
            raise ValueError(f"Unknown level '{level}'")

        current = QueryAnalyzer.KEYWORD_PATTERNS[level]["keywords"]
        QueryAnalyzer.KEYWORD_PATTERNS[level]["keywords"] = [
            k for k in current if k not in keywords
        ]

    @staticmethod
    def set_keywords(level: str, keywords: List[str]) -> None:
        """Replace all keywords for a budget level

        Args:
            level: Token budget level
            keywords: New list of keywords
        """
        if level not in QueryAnalyzer.KEYWORD_PATTERNS:
            raise ValueError(f"Unknown level '{level}'")

        QueryAnalyzer.KEYWORD_PATTERNS[level]["keywords"] = keywords


class AutoBudgetSelector:
    """Automatically select token budget based on query with override capability"""

    def __init__(self, auto_detect: bool = True, force_level: Optional[str] = None):
        """
        Initialize auto budget selector

        Args:
            auto_detect: Whether to auto-detect from query (True) or use default
            force_level: Force a specific level ("minimal", "standard", "rich", "comprehensive")
                        If set, overrides auto-detection
        """
        self.auto_detect = auto_detect
        self.force_level = force_level

        if force_level:
            valid_levels = [e.value for e in TokenBudgetLevel]
            if force_level not in valid_levels:
                raise ValueError(
                    f"Invalid force_level '{force_level}'. "
                    f"Use: {', '.join(valid_levels)}"
                )

    def select(self, query: str) -> Tuple[int, QueryAnalysis]:
        """
        Select token budget for query

        Args:
            query: User's search query

        Returns:
            Tuple of (token_budget, analysis)
        """
        from pystreampdf.config import TokenBudgetConfig

        # If force_level set, use it
        if self.force_level:
            budget = TokenBudgetConfig.get_preset(self.force_level)
            # Create dummy analysis for consistency
            analysis = QueryAnalysis(
                detected_level=TokenBudgetLevel(self.force_level),
                confidence=1.0,
                matched_keywords=[],
                query_complexity="forced",
                rationale=f"Forced to {self.force_level.upper()} level",
            )
            return budget, analysis

        # Auto-detect from query
        if self.auto_detect:
            analysis = QueryAnalyzer.analyze(query)
            budget = TokenBudgetConfig.get_preset(analysis.detected_level.value)
            return budget, analysis

        # Default fallback
        budget = TokenBudgetConfig.get_preset("standard")
        analysis = QueryAnalysis(
            detected_level=TokenBudgetLevel.STANDARD,
            confidence=0.0,
            matched_keywords=[],
            query_complexity="unknown",
            rationale="Auto-detection disabled, using standard fallback",
        )
        return budget, analysis

    def update_force_level(self, level: Optional[str]) -> None:
        """Update forced level

        Args:
            level: New level or None to disable force
        """
        if level:
            valid_levels = [e.value for e in TokenBudgetLevel]
            if level not in valid_levels:
                raise ValueError(
                    f"Invalid level '{level}'. Use: {', '.join(valid_levels)}"
                )
        self.force_level = level

    def enable_auto_detect(self, enable: bool = True) -> None:
        """Enable or disable auto-detection

        Args:
            enable: True to enable, False to disable
        """
        self.auto_detect = enable


# Convenience function
def auto_select_budget(
    query: str,
    force_level: Optional[str] = None,
    auto_detect: bool = True,
) -> Tuple[int, QueryAnalysis]:
    """
    Convenience function to auto-select budget for a query

    Args:
        query: User's search query
        force_level: Force specific level (overrides auto-detection)
        auto_detect: Enable auto-detection from query

    Returns:
        Tuple of (token_budget, analysis)

    Example:
        budget, analysis = auto_select_budget("What is machine learning?")
        # Returns: (500, QueryAnalysis(...))

        budget, analysis = auto_select_budget(
            "What is machine learning?",
            force_level="comprehensive"
        )
        # Returns: (2750, QueryAnalysis(...))
    """
    selector = AutoBudgetSelector(auto_detect=auto_detect, force_level=force_level)
    return selector.select(query)
