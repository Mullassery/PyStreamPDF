"""Keyword-driven token budget configuration system.

Allows users to define rules that scale token budgets based on PDF metadata
(filename, title, content preview). Enables teams to allocate larger budgets
to financial reports, compliance docs, etc., and smaller budgets to summaries.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import yaml
import re


@dataclass
class BudgetRule:
    """Rule for scaling token budget based on keywords."""
    keyword: str
    multiplier: float
    match_fields: List[str] = field(default_factory=lambda: ["filename", "title"])
    case_sensitive: bool = False

    def matches(self, filename: str, title: Optional[str] = None, content_preview: Optional[str] = None) -> bool:
        """Check if this rule matches any of the specified fields."""
        fields_to_check = {
            "filename": filename,
            "title": title or "",
            "content_preview": content_preview or "",
        }

        for field_name in self.match_fields:
            if field_name not in fields_to_check:
                continue

            text = fields_to_check[field_name]
            search_keyword = self.keyword if self.case_sensitive else self.keyword.lower()
            search_text = text if self.case_sensitive else text.lower()

            if search_keyword in search_text:
                return True

        return False


class TokenBudgetConfig:
    """Configuration for keyword-driven token budget scaling.

    Allows defining rules that multiply the base token budget based on
    keywords found in PDF metadata. Multipliers stack multiplicatively.

    Example YAML:
        base_budget: 2000
        rules:
          - keyword: "financial"
            multiplier: 2.0
            match_fields: ["filename", "title"]
          - keyword: "summary"
            multiplier: 0.5
            match_fields: ["filename"]
    """

    MIN_BUDGET = 100
    MAX_BUDGET = 32000

    def __init__(self, base_budget: int = 2000, rules: Optional[List[BudgetRule]] = None):
        """Initialize token budget configuration.

        Args:
            base_budget: Default token budget if no rules match (default 2000)
            rules: List of BudgetRule objects to evaluate
        """
        self.base_budget = base_budget
        self.rules = rules or []

    @classmethod
    def from_yaml(cls, path: str) -> "TokenBudgetConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            TokenBudgetConfig instance

        Raises:
            FileNotFoundError: If config file does not exist
            yaml.YAMLError: If YAML is invalid
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenBudgetConfig":
        """Load configuration from a dictionary.

        Args:
            data: Dictionary with 'base_budget' and 'rules' keys

        Returns:
            TokenBudgetConfig instance
        """
        base_budget = data.get("base_budget", 2000)
        rules_data = data.get("rules", [])

        rules = []
        for rule_data in rules_data:
            rule = BudgetRule(
                keyword=rule_data["keyword"],
                multiplier=rule_data.get("multiplier", 1.0),
                match_fields=rule_data.get("match_fields", ["filename", "title"]),
                case_sensitive=rule_data.get("case_sensitive", False),
            )
            rules.append(rule)

        return cls(base_budget=base_budget, rules=rules)

    def evaluate(
        self,
        filename: str,
        title: Optional[str] = None,
        content_preview: Optional[str] = None,
    ) -> int:
        """Evaluate token budget based on PDF metadata.

        Applies all matching rules multiplicatively. For example:
        - base_budget=2000
        - "financial" rule with 2.0 multiplier
        - "quarterly" rule with 3.0 multiplier
        - If filename is "financial_quarterly_report.pdf", result = 2000 * 2.0 * 3.0 = 12000

        Args:
            filename: PDF filename (without path)
            title: PDF title/metadata (optional)
            content_preview: First ~500 chars of first page text (optional)

        Returns:
            Evaluated token budget, clamped to [MIN_BUDGET, MAX_BUDGET]
        """
        budget = float(self.base_budget)

        for rule in self.rules:
            if rule.matches(filename, title, content_preview):
                budget *= rule.multiplier

        # Clamp to valid range
        budget = max(self.MIN_BUDGET, min(self.MAX_BUDGET, int(budget)))
        return budget

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary for YAML serialization."""
        return {
            "base_budget": self.base_budget,
            "rules": [
                {
                    "keyword": rule.keyword,
                    "multiplier": rule.multiplier,
                    "match_fields": rule.match_fields,
                    "case_sensitive": rule.case_sensitive,
                }
                for rule in self.rules
            ],
        }

    def to_yaml(self, path: str) -> None:
        """Export configuration to a YAML file.

        Args:
            path: Output path for YAML file
        """
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
