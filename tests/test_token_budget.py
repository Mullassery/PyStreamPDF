"""Tests for keyword-driven token budget configuration."""

import pytest
import tempfile
from pathlib import Path
from pystreampdf.token_budget import BudgetRule, TokenBudgetConfig


class TestBudgetRule:
    """Test BudgetRule matching logic."""

    def test_simple_keyword_match_in_filename(self):
        """Test keyword match in filename."""
        rule = BudgetRule("financial", 2.0, match_fields=["filename"])
        assert rule.matches("financial_report.pdf") is True
        assert rule.matches("quarterly_summary.pdf") is False

    def test_keyword_match_in_title(self):
        """Test keyword match in title."""
        rule = BudgetRule("financial", 2.0, match_fields=["title"])
        assert rule.matches("report.pdf", title="Financial Analysis 2024") is True
        assert rule.matches("report.pdf", title="Quarterly Summary") is False

    def test_keyword_match_in_preview(self):
        """Test keyword match in content preview."""
        rule = BudgetRule("quarterly", 2.0, match_fields=["content_preview"])
        assert rule.matches("report.pdf", content_preview="This is our quarterly earnings...") is True
        assert rule.matches("report.pdf", content_preview="Annual report for 2024") is False

    def test_case_sensitive_match(self):
        """Test case-sensitive matching."""
        rule_sensitive = BudgetRule("Financial", 2.0, case_sensitive=True)
        rule_insensitive = BudgetRule("Financial", 2.0, case_sensitive=False)

        assert rule_sensitive.matches("Financial_Report.pdf") is True
        assert rule_sensitive.matches("financial_report.pdf") is False
        assert rule_insensitive.matches("financial_report.pdf") is True

    def test_multiple_fields(self):
        """Test matching across multiple fields."""
        rule = BudgetRule("financial", 2.0, match_fields=["filename", "title", "content_preview"])
        assert rule.matches("report.pdf", title="Financial Analysis") is True
        assert rule.matches("financial.pdf", title="Annual Report") is True
        assert rule.matches("summary.pdf", content_preview="Financial statements...") is True
        assert rule.matches("summary.pdf", title="Summary") is False


class TestTokenBudgetConfig:
    """Test TokenBudgetConfig evaluation."""

    def test_no_rules_returns_base_budget(self):
        """Test that no rules returns base budget unchanged."""
        config = TokenBudgetConfig(base_budget=800, rules=[])
        assert config.evaluate("report.pdf") == 800
        assert config.evaluate("financial_report.pdf") == 800

    def test_single_rule_match(self):
        """Test single rule that matches."""
        rule = BudgetRule("financial", 1.1, match_fields=["filename"])
        config = TokenBudgetConfig(base_budget=800, rules=[rule])

        assert config.evaluate("financial_report.pdf") == 880
        assert config.evaluate("summary_report.pdf") == 800

    def test_multiple_rules_stack_multiplicatively(self):
        """Test that multiple matching rules multiply."""
        rules = [
            BudgetRule("financial", 1.05, match_fields=["filename"]),
            BudgetRule("quarterly", 1.06, match_fields=["filename"]),
        ]
        config = TokenBudgetConfig(base_budget=800, rules=rules)

        # Both match: 800 * 1.05 * 1.06 = 890.4 ≈ 890
        assert config.evaluate("financial_quarterly_report.pdf") == 890
        # Only first matches: 800 * 1.05 = 840
        assert config.evaluate("financial_report.pdf") == 840
        # Neither matches: 800
        assert config.evaluate("summary.pdf") == 800

    def test_budget_clamped_to_max(self):
        """Test that budget is clamped to MAX_BUDGET."""
        rules = [
            BudgetRule("financial", 1.5, match_fields=["filename"]),
        ]
        config = TokenBudgetConfig(base_budget=800, rules=rules)

        # 800 * 1.5 = 1200, should be clamped to 1000
        result = config.evaluate("financial_report.pdf")
        assert result == TokenBudgetConfig.MAX_BUDGET

    def test_budget_clamped_to_min(self):
        """Test that budget is clamped to MIN_BUDGET."""
        rules = [
            BudgetRule("summary", 0.4, match_fields=["filename"]),
        ]
        config = TokenBudgetConfig(base_budget=1000, rules=rules)

        # 1000 * 0.4 = 400, should be clamped to 500
        result = config.evaluate("summary.pdf")
        assert result == TokenBudgetConfig.MIN_BUDGET

    def test_from_dict(self):
        """Test loading config from dictionary."""
        data = {
            "base_budget": 3000,
            "rules": [
                {
                    "keyword": "financial",
                    "multiplier": 2.0,
                    "match_fields": ["filename", "title"],
                    "case_sensitive": False,
                }
            ],
        }
        config = TokenBudgetConfig.from_dict(data)

        assert config.base_budget == 3000
        assert len(config.rules) == 1
        assert config.rules[0].keyword == "financial"
        assert config.rules[0].multiplier == 2.0

    def test_from_yaml(self):
        """Test loading config from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "budget_config.yaml"
            yaml_content = """
base_budget: 2000
rules:
  - keyword: financial
    multiplier: 2.0
    match_fields: [filename, title]
    case_sensitive: false
  - keyword: summary
    multiplier: 0.5
    match_fields: [filename]
    case_sensitive: true
"""
            yaml_path.write_text(yaml_content)

            config = TokenBudgetConfig.from_yaml(str(yaml_path))

            assert config.base_budget == 2000
            assert len(config.rules) == 2
            assert config.rules[0].keyword == "financial"
            assert config.rules[0].multiplier == 2.0
            assert config.rules[1].keyword == "summary"
            assert config.rules[1].multiplier == 0.5
            assert config.rules[1].case_sensitive is True

    def test_to_yaml(self):
        """Test exporting config to YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output_config.yaml"

            rules = [
                BudgetRule("financial", 2.0, match_fields=["filename"]),
                BudgetRule("summary", 0.5, match_fields=["title"]),
            ]
            config = TokenBudgetConfig(base_budget=3000, rules=rules)
            config.to_yaml(str(output_path))

            assert output_path.exists()

            reloaded = TokenBudgetConfig.from_yaml(str(output_path))
            assert reloaded.base_budget == 3000
            assert len(reloaded.rules) == 2
            assert reloaded.rules[0].keyword == "financial"

    def test_complex_matching(self):
        """Test complex multi-field matching scenario."""
        rules = [
            BudgetRule("legal", 1.05, match_fields=["filename", "title", "content_preview"]),
            BudgetRule("compliance", 1.1, match_fields=["content_preview"]),
            BudgetRule("draft", 0.95, match_fields=["filename"]),
        ]
        config = TokenBudgetConfig(base_budget=800, rules=rules)

        # Only "legal" matches in filename: 800 * 1.05 = 840
        assert config.evaluate("legal_document.pdf") == 840

        # "legal" in title and "compliance" in preview: 800 * 1.05 * 1.1 = 924
        assert config.evaluate(
            "contract.pdf",
            title="Legal Agreement",
            content_preview="This compliance document...",
        ) == 924

        # "legal" and "draft": 800 * 1.05 * 0.95 = 798
        assert config.evaluate("legal_draft.pdf") == 798

    def test_empty_fields_ignored(self):
        """Test that empty/None fields don't cause errors."""
        rule = BudgetRule("financial", 1.1, match_fields=["title", "content_preview"])
        config = TokenBudgetConfig(base_budget=800, rules=[rule])

        # None values should be treated as empty strings
        assert config.evaluate("report.pdf", title=None, content_preview=None) == 800
        assert config.evaluate("report.pdf", title="Financial Report") == 880
