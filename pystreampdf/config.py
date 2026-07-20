"""
PyStreamPDF configuration for token budgets and retrieval settings

Philosophy: Be selective, not comprehensive. PyStreamPDF's strength is retrieving
only relevant sections (10-50x token reduction vs naive extraction). Budget settings
should reflect quality-first approach, not maximize content volume.
"""

from typing import Dict, Optional


class TokenBudgetConfig:
    """Token budget configuration with preset values"""

    # Reasonable ranges: balance selectivity with quality
    # Philosophy: Retrieve only relevant sections, not everything
    PRESETS = {
        "minimal": 500,        # Use sparingly - bare essentials only
        "standard": 2000,      # RECOMMENDED: Selective extraction with good quality
        "comprehensive": 4000, # Include more context if needed
        "maximum": 8000,       # Practical upper limit
    }

    # Hard limits to prevent unreasonable values
    MIN_REASONABLE = 256      # Below this: loses too much context, diminishing returns
    MAX_REASONABLE = 8000     # Above this: defeats PyStreamPDF's efficiency mission

    @staticmethod
    def validate(max_tokens: int) -> int:
        """Validate token budget is within reasonable range"""
        if max_tokens < TokenBudgetConfig.MIN_REASONABLE:
            raise ValueError(
                f"max_tokens={max_tokens} too low. "
                f"Minimum reasonable: {TokenBudgetConfig.MIN_REASONABLE}. "
                f"Use presets: {list(TokenBudgetConfig.PRESETS.keys())}"
            )
        if max_tokens > TokenBudgetConfig.MAX_REASONABLE:
            raise ValueError(
                f"max_tokens={max_tokens} too high. "
                f"Maximum reasonable: {TokenBudgetConfig.MAX_REASONABLE}. "
                f"Use presets: {list(TokenBudgetConfig.PRESETS.keys())}"
            )
        return max_tokens

    @staticmethod
    def suggest_increase(current: int, retrieved_words: int, model: str = "default") -> int:
        """Suggest a reasonable token budget increase"""
        # Model-specific limits
        model_limits = {
            "gpt-3.5": 4000,
            "gpt-4": 8000,
            "claude-3-haiku": 4000,
            "claude-3-sonnet": 8000,
            "claude-3-opus": 16000,  # Capped at MAX_REASONABLE
            "default": TokenBudgetConfig.MAX_REASONABLE,
        }

        model_limit = model_limits.get(model, TokenBudgetConfig.MAX_REASONABLE)
        model_limit = min(model_limit, TokenBudgetConfig.MAX_REASONABLE)

        # Estimate tokens from words (rough: 1.3 tokens per word)
        estimated_tokens = int(retrieved_words * 1.3)

        # Suggest smallest preset that fits retrieved content
        if estimated_tokens <= TokenBudgetConfig.PRESETS["minimal"]:
            return TokenBudgetConfig.PRESETS["minimal"]
        elif estimated_tokens <= TokenBudgetConfig.PRESETS["standard"]:
            return TokenBudgetConfig.PRESETS["standard"]
        elif estimated_tokens <= TokenBudgetConfig.PRESETS["generous"]:
            return TokenBudgetConfig.PRESETS["generous"]
        else:
            return min(estimated_tokens, model_limit)

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
            "description": "Bare essentials only - fastest, lowest cost",
        },
        "default": {
            "max_tokens": TokenBudgetConfig.PRESETS["standard"],
            "description": "RECOMMENDED: Selective extraction with quality",
        },
        "quality": {
            "max_tokens": TokenBudgetConfig.PRESETS["comprehensive"],
            "description": "More context if query needs it - still selective",
        },
        "premium": {
            "max_tokens": TokenBudgetConfig.PRESETS["maximum"],
            "description": "Highest quality results while staying selective",
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

    All suggestions favor selectivity over comprehensiveness.
    If you need more context, verify retrieval quality first.
    """
    suggestions = {
        "qa": TokenBudgetConfig.PRESETS["standard"],
        "chat": TokenBudgetConfig.PRESETS["standard"],
        "code": TokenBudgetConfig.PRESETS["standard"],
        "summarization": TokenBudgetConfig.PRESETS["comprehensive"],
        "legal": TokenBudgetConfig.PRESETS["comprehensive"],
        "research": TokenBudgetConfig.PRESETS["comprehensive"],
        "extraction": TokenBudgetConfig.PRESETS["minimal"],
    }

    if use_case.lower() not in suggestions:
        available = ", ".join(suggestions.keys())
        raise ValueError(f"Unknown use case '{use_case}'. Available: {available}")

    return suggestions[use_case.lower()]


# Example usage patterns
USAGE_EXAMPLES = """
# Use preset
from pystreampdf.config import TokenBudgetConfig
budget = TokenBudgetConfig.get_preset("standard")  # 2000 tokens

# Use profile
from pystreampdf.config import RetrievalConfig
config = RetrievalConfig.get_profile("thorough")
navigator.retrieve_with_flow(query, max_tokens=config["max_tokens"])

# Suggest based on retrieval results
budget = TokenBudgetConfig.suggest_increase(
    current=2000,
    retrieved_words=3000,
    model="claude-3-opus"  # Respects model limits
)

# Use case-based
from pystreampdf.config import suggest_budget_for_use_case
budget = suggest_budget_for_use_case("legal")  # Returns 8000
"""
