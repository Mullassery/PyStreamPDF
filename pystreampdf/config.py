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
        "minimal": 150,        # Essential facts only
        "standard": 500,       # RECOMMENDED: Core relevant content
        "comprehensive": 1000, # More context if query is complex
    }

    # Hard limits to prevent unreasonable values
    MIN_REASONABLE = 100      # Below this: too aggressive
    MAX_REASONABLE = 2000     # Above this: defeats PyStreamPDF's selective mission

    @staticmethod
    def validate(max_tokens: int) -> int:
        """Validate token budget is within allowed range

        PyStreamPDF enforces strict limits to maintain selectivity:
        - Below 100: Loses too much context
        - Above 2000: Defeats selective extraction mission

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
        "complex": {
            "max_tokens": TokenBudgetConfig.PRESETS["comprehensive"],
            "description": "For complex queries - more context, still selective",
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


def suggest_budget_for_use_case(use_case: str) -> int:
    """Suggest appropriate token budget for common use cases

    Biased toward minimal/standard to encourage selective retrieval.
    Use comprehensive only if standard retrieval is insufficient.
    """
    suggestions = {
        # Most use cases: standard (500)
        "qa": TokenBudgetConfig.PRESETS["standard"],
        "chat": TokenBudgetConfig.PRESETS["standard"],
        "code": TokenBudgetConfig.PRESETS["standard"],
        "extraction": TokenBudgetConfig.PRESETS["minimal"],

        # Complex queries may need comprehensive (1000)
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
