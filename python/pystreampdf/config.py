"""
PyStreamPDF configuration for token budgets and retrieval settings

Philosophy: Be selective, not comprehensive. PyStreamPDF's strength is retrieving
only relevant sections (10-50x token reduction vs naive extraction). Budget settings
should reflect quality-first approach, not maximize content volume.
"""

from typing import Dict, Optional


class TokenBudgetConfig:
    """Token budget configuration with preset values"""

    # Tight budgets emphasize selective extraction
    # Philosophy: Retrieve only what's relevant, nothing more
    PRESETS = {
        "minimal": 250,        # Essential facts only
        "standard": 500,       # RECOMMENDED: Core relevant content
        "rich": 750,           # Richer context for complex queries
        "comprehensive": 1000, # Full context if needed
    }

    # Hard limits to prevent unreasonable values
    MIN_REASONABLE = 250      # Below this: too aggressive, loses context
    MAX_REASONABLE = 1000     # Above this: defeats PyStreamPDF's selective mission

    @staticmethod
    def validate(max_tokens: int) -> int:
        """Validate token budget is within allowed range

        PyStreamPDF enforces strict limits to maintain selectivity:
        - Below 250: Loses too much context
        - Above 1000: Defeats selective extraction mission

        No exceptions to these limits.
        """
        if max_tokens < TokenBudgetConfig.MIN_REASONABLE:
            raise ValueError(
                f"max_tokens={max_tokens} not allowed. "
                f"Minimum: {TokenBudgetConfig.MIN_REASONABLE} (use presets: "
                f"{', '.join(TokenBudgetConfig.PRESETS.keys())})"
            )
        if max_tokens > TokenBudgetConfig.MAX_REASONABLE:
            raise ValueError(
                f"max_tokens={max_tokens} not allowed. "
                f"Maximum: {TokenBudgetConfig.MAX_REASONABLE} (use presets: "
                f"{', '.join(TokenBudgetConfig.PRESETS.keys())})"
            )
        return max_tokens

    @staticmethod
    def suggest_increase(current: int, retrieved_words: int, model: str = "default") -> int:
        """Suggest a reasonable token budget increase

        Returns the smallest preset that can fit the content,
        capped at MAX_REASONABLE to maintain selectivity.
        """
        # Estimate tokens from words (rough: 1.3 tokens per word)
        estimated_tokens = int(retrieved_words * 1.3)

        # Suggest smallest preset that fits retrieved content
        if estimated_tokens <= TokenBudgetConfig.PRESETS["minimal"]:
            return TokenBudgetConfig.PRESETS["minimal"]
        elif estimated_tokens <= TokenBudgetConfig.PRESETS["standard"]:
            return TokenBudgetConfig.PRESETS["standard"]
        elif estimated_tokens <= TokenBudgetConfig.PRESETS["comprehensive"]:
            return TokenBudgetConfig.PRESETS["comprehensive"]
        else:
            # Even if more tokens needed, cap at MAX_REASONABLE
            # (encourages query refinement over unlimited extraction)
            return TokenBudgetConfig.MAX_REASONABLE

    @staticmethod
    def get_preset(name: str) -> int:
        """Get preset token budget by name"""
        if name not in TokenBudgetConfig.PRESETS:
            available = ", ".join(TokenBudgetConfig.PRESETS.keys())
            raise ValueError(f"Unknown preset '{name}'. Available: {available}")
        return TokenBudgetConfig.PRESETS[name]


class RetrievalConfig:
    """Configuration for retrieval behavior"""

    # Recommended settings per use case
    # All focused on selective extraction (PyStreamPDF's core value)
    PROFILES = {
        "extraction": {
            "max_tokens": TokenBudgetConfig.PRESETS["minimal"],
            "description": "Essential facts only - fastest, lowest cost",
        },
        "default": {
            "max_tokens": TokenBudgetConfig.PRESETS["standard"],
            "description": "RECOMMENDED: Core relevant content",
        },
        "rich": {
            "max_tokens": TokenBudgetConfig.PRESETS["rich"],
            "description": "Richer context for complex or multi-part queries",
        },
        "complex": {
            "max_tokens": TokenBudgetConfig.PRESETS["comprehensive"],
            "description": "Full context for highly complex queries - still selective",
        },
    }

    @staticmethod
    def get_profile(name: str) -> Dict:
        """Get retrieval profile by name"""
        if name not in RetrievalConfig.PROFILES:
            available = ", ".join(RetrievalConfig.PROFILES.keys())
            raise ValueError(f"Unknown profile '{name}'. Available: {available}")
        return RetrievalConfig.PROFILES[name]

    @staticmethod
    def describe_profile(name: str) -> str:
        """Get human-readable description of a profile"""
        profile = RetrievalConfig.get_profile(name)
        return f"{name}: {profile['description']} ({profile['max_tokens']} tokens)"


class FilteringConfig:
    """Configuration for filtering stage (relevance scoring and selection)"""

    # Filtering strategies with different strictness levels
    STRATEGIES = {
        "strict": {
            "min_relevance_score": 0.7,    # Only high-confidence matches
            "max_sections": 3,              # Limit to top 3 sections
            "require_threshold": True,      # Must meet minimum score
            "description": "Only highest relevance - minimal, focused output",
        },
        "balanced": {
            "min_relevance_score": 0.5,    # Moderate confidence
            "max_sections": 5,              # RECOMMENDED: balanced set
            "require_threshold": True,
            "description": "RECOMMENDED: High-quality selections",
        },
        "lenient": {
            "min_relevance_score": 0.3,    # Broader matches
            "max_sections": 10,             # Include more sections
            "require_threshold": False,     # Allow lower scores if relevant
            "description": "Broader retrieval for comprehensive coverage",
        },
    }

    # Hard limits to maintain quality
    MIN_RELEVANCE_SCORE = 0.1    # Below this: score is meaningless
    MAX_RELEVANCE_SCORE = 1.0    # Perfect match
    MIN_MAX_SECTIONS = 1         # At least one section
    MAX_MAX_SECTIONS = 20        # Don't over-retrieve

    @staticmethod
    def get_strategy(name: str) -> Dict:
        """Get filtering strategy by name"""
        if name not in FilteringConfig.STRATEGIES:
            available = ", ".join(FilteringConfig.STRATEGIES.keys())
            raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
        return FilteringConfig.STRATEGIES[name]

    @staticmethod
    def validate_relevance_score(score: float) -> float:
        """Validate relevance score is in valid range [0.1, 1.0]"""
        if score < FilteringConfig.MIN_RELEVANCE_SCORE:
            raise ValueError(
                f"Relevance score {score} too low. "
                f"Minimum: {FilteringConfig.MIN_RELEVANCE_SCORE}"
            )
        if score > FilteringConfig.MAX_RELEVANCE_SCORE:
            raise ValueError(
                f"Relevance score {score} too high. "
                f"Maximum: {FilteringConfig.MAX_RELEVANCE_SCORE}"
            )
        return score

    @staticmethod
    def validate_max_sections(count: int) -> int:
        """Validate max sections is in valid range"""
        if count < FilteringConfig.MIN_MAX_SECTIONS:
            raise ValueError(
                f"Max sections {count} too low. "
                f"Minimum: {FilteringConfig.MIN_MAX_SECTIONS}"
            )
        if count > FilteringConfig.MAX_MAX_SECTIONS:
            raise ValueError(
                f"Max sections {count} too high. "
                f"Maximum: {FilteringConfig.MAX_MAX_SECTIONS}"
            )
        return count


def suggest_budget_for_use_case(use_case: str) -> int:
    """Suggest appropriate token budget for common use cases

    Biased toward selective retrieval. Use higher budgets only if
    standard retrieval is insufficient.
    """
    suggestions = {
        # Quick retrieval: minimal (250)
        "extraction": TokenBudgetConfig.PRESETS["minimal"],

        # Most use cases: standard (500)
        "qa": TokenBudgetConfig.PRESETS["standard"],
        "chat": TokenBudgetConfig.PRESETS["standard"],

        # Code needs context: rich (750)
        "code": TokenBudgetConfig.PRESETS["rich"],

        # Complex queries need more: comprehensive (1000)
        "summarization": TokenBudgetConfig.PRESETS["comprehensive"],
        "legal": TokenBudgetConfig.PRESETS["comprehensive"],
        "research": TokenBudgetConfig.PRESETS["comprehensive"],
    }

    if use_case.lower() not in suggestions:
        available = ", ".join(suggestions.keys())
        raise ValueError(f"Unknown use case '{use_case}'. Available: {available}")

    return suggestions[use_case.lower()]


# Example usage patterns
USAGE_EXAMPLES = """
# Use preset
from pystreampdf.config import TokenBudgetConfig
budget = TokenBudgetConfig.get_preset("standard")  # 500 tokens (recommended)

# Use profile
from pystreampdf.config import RetrievalConfig
config = RetrievalConfig.get_profile("complex")
navigator.retrieve_with_flow(query, max_tokens=config["max_tokens"])

# Suggest based on retrieval results
budget = TokenBudgetConfig.suggest_increase(
    current=500,
    retrieved_words=600,
    model="claude-3-opus"  # Capped at MAX_REASONABLE (2000)
)

# Use case-based
from pystreampdf.config import suggest_budget_for_use_case
budget = suggest_budget_for_use_case("legal")  # Returns 1000 (comprehensive)
"""
