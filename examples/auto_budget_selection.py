#!/usr/bin/env python3
"""
Auto Budget Selection Example

Demonstrates how PyStreamPDF automatically selects token budgets
based on query complexity and keywords, with override capability.
"""

import sys
sys.path.insert(0, '/tmp/PyStreamPDF/python')

from pystreampdf.query_analyzer import (
    QueryAnalyzer,
    AutoBudgetSelector,
    auto_select_budget,
    TokenBudgetLevel,
)
from pystreampdf.config import TokenBudgetConfig


def demo_1_basic_analysis():
    """Demo 1: Analyze different query types"""
    print("\n" + "=" * 140)
    print("DEMO 1: Query Analysis - Auto-Detect Complexity")
    print("=" * 140)

    queries = [
        ("What is machine learning?", "minimal"),
        ("Explain how neural networks work", "standard"),
        ("Compare supervised and unsupervised learning approaches", "rich"),
        ("Provide a comprehensive analysis of deep learning architectures and best practices", "comprehensive"),
    ]

    print(f"\n{'Query':<70} | {'Detected':<15} | {'Confidence':<12} | {'Complexity':<10}")
    print("-" * 140)

    for query, expected in queries:
        analysis = QueryAnalyzer.analyze(query)
        confidence_pct = f"{analysis.confidence:.0%}"
        detected = analysis.detected_level.value

        match = "✓" if detected == expected else "✗"
        print(f"{query:<70} | {detected:<15} | {confidence_pct:<12} | {analysis.query_complexity:<10} {match}")


def demo_2_keyword_matching():
    """Demo 2: Show matched keywords"""
    print("\n" + "=" * 140)
    print("DEMO 2: Keyword Matching - What Triggered Detection")
    print("=" * 140)

    queries = [
        "What is the definition of artificial intelligence?",
        "How can I optimize database queries for better performance?",
        "Analyze and compare the three different machine learning paradigms",
        "Deep dive into the architecture and design patterns of microservices",
    ]

    for query in queries:
        analysis = QueryAnalyzer.analyze(query)
        print(f"\nQuery: {query}")
        print(f"  Level: {analysis.detected_level.value.upper()} ({analysis.query_complexity})")
        print(f"  Confidence: {analysis.confidence:.0%}")
        print(f"  Matched: {', '.join(analysis.matched_keywords[:5])}")
        if len(analysis.matched_keywords) > 5:
            print(f"           +{len(analysis.matched_keywords) - 5} more")
        print(f"  Rationale: {analysis.rationale}")


def demo_3_auto_select():
    """Demo 3: Auto-select token budget"""
    print("\n" + "=" * 140)
    print("DEMO 3: Auto-Select Budget - Get Recommended Token Count")
    print("=" * 140)

    queries = [
        "Define machine learning",
        "How do gradient descent algorithms work?",
        "Compare CNNs, RNNs, and Transformers with detailed examples",
        "Exhaustive analysis of neural network architectures and training methods",
    ]

    print(f"\n{'Query':<60} | {'Budget':<10} | {'Level':<15}")
    print("-" * 140)

    for query in queries:
        budget, analysis = auto_select_budget(query)
        level = analysis.detected_level.value
        level_name = {
            "minimal": "MINIMAL (500)",
            "standard": "STANDARD (1500)",
            "rich": "RICH (2000)",
            "comprehensive": "COMPREHENSIVE (2750)",
        }[level]

        print(f"{query:<60} | {budget:<10} | {level_name:<15}")


def demo_4_force_override():
    """Demo 4: Force override auto-detection"""
    print("\n" + "=" * 140)
    print("DEMO 4: Force Override - Programmatic Control")
    print("=" * 140)

    query = "What is X?"  # Would normally detect as minimal

    print(f"\nQuery: '{query}'")
    print("\nAuto-Detected:")
    budget, analysis = auto_select_budget(query)
    print(f"  Budget: {budget} tokens (Level: {analysis.detected_level.value})")
    print(f"  Rationale: {analysis.rationale}")

    print("\nWith Force Override to 'comprehensive':")
    budget, analysis = auto_select_budget(query, force_level="comprehensive")
    print(f"  Budget: {budget} tokens (Level: {analysis.detected_level.value})")
    print(f"  Rationale: {analysis.rationale}")


def demo_5_selector_object():
    """Demo 5: Using AutoBudgetSelector for conditional logic"""
    print("\n" + "=" * 140)
    print("DEMO 5: AutoBudgetSelector - Conditional Control")
    print("=" * 140)

    selector = AutoBudgetSelector(auto_detect=True, force_level=None)

    print("\nScenario 1: Auto-detection enabled (default)")
    queries = ["What is X?", "How does Y work?", "Analyze Z in detail"]
    for query in queries:
        budget, analysis = selector.select(query)
        print(f"  '{query}' → {budget} tokens ({analysis.query_complexity})")

    print("\nScenario 2: Force to 'rich' level")
    selector.update_force_level("rich")
    for query in queries:
        budget, analysis = selector.select(query)
        print(f"  '{query}' → {budget} tokens (forced: {analysis.detected_level.value})")

    print("\nScenario 3: Clear force, use auto-detection")
    selector.update_force_level(None)
    for query in queries:
        budget, analysis = selector.select(query)
        print(f"  '{query}' → {budget} tokens ({analysis.query_complexity})")


def demo_6_custom_keywords():
    """Demo 6: Add custom keywords for domain"""
    print("\n" + "=" * 140)
    print("DEMO 6: Custom Keywords - Domain-Specific Configuration")
    print("=" * 140)

    # Before customization
    query = "Kubernetes configuration and deployment"
    analysis_before = QueryAnalyzer.analyze(query)

    print(f"\nQuery: '{query}'")
    print(f"\nBefore custom keywords:")
    print(f"  Detected Level: {analysis_before.detected_level.value}")
    print(f"  Confidence: {analysis_before.confidence:.0%}")

    # Add custom keywords
    print(f"\nAdding custom Kubernetes keywords to 'rich' level...")
    QueryAnalyzer.add_keywords("rich", [
        "kubernetes", "deployment", "pod", "service",
        "ingress", "orchestration", "containerization"
    ])

    # After customization
    analysis_after = QueryAnalyzer.analyze(query)

    print(f"\nAfter custom keywords:")
    print(f"  Detected Level: {analysis_after.detected_level.value}")
    print(f"  Confidence: {analysis_after.confidence:.0%}")
    print(f"  Matched Keywords: {analysis_after.matched_keywords}")


def demo_7_summary_comparison():
    """Demo 7: Side-by-side comparison of budgets"""
    print("\n" + "=" * 140)
    print("DEMO 7: Budget Comparison - What Each Level Gets")
    print("=" * 140)

    query = "Machine learning algorithms"

    print(f"\nQuery: '{query}'")
    print("\nBudget Levels and Their Characteristics:\n")

    for level in ["minimal", "standard", "rich", "comprehensive"]:
        selector = AutoBudgetSelector(force_level=level)
        budget, analysis = selector.select(query)

        token_info = {
            "minimal": "~385 words, 1 section",
            "standard": "~1155 words, 1-2 sections",
            "rich": "~1540 words, 2-3 sections",
            "comprehensive": "~2115 words, 3-4 sections",
        }

        print(f"{level.upper().ljust(15)} | {budget:4} tokens | {token_info[level]}")


def demo_8_confidence_scores():
    """Demo 8: Understand confidence scores"""
    print("\n" + "=" * 140)
    print("DEMO 8: Confidence Scores - How Certain is the Detection?")
    print("=" * 140)

    queries = [
        "What is X?",                    # High confidence
        "Tell me about Y and Z",          # Medium confidence
        "Foo bar baz qux",                # Low confidence
        "Analyze and compare A vs B",    # High confidence
    ]

    print(f"\n{'Query':<40} | {'Level':<15} | {'Confidence':<15} | {'Assessment':<15}")
    print("-" * 140)

    for query in queries:
        analysis = QueryAnalyzer.analyze(query)
        if analysis.confidence > 0.8:
            assessment = "High (Trust)"
        elif analysis.confidence > 0.6:
            assessment = "Medium (Verify)"
        else:
            assessment = "Low (Override)"

        conf_str = f"{analysis.confidence:.0%}"
        print(f"{query:<40} | {analysis.detected_level.value:<15} | {conf_str:<15} | {assessment:<15}")


def demo_9_real_world_scenario():
    """Demo 9: Real-world usage scenario"""
    print("\n" + "=" * 140)
    print("DEMO 9: Real-World Scenario - Search with Auto-Budget")
    print("=" * 140)

    print("\nScenario: Research paper search system with auto-budgeting\n")

    research_queries = [
        ("What is transformers?", "Quick definition for intro"),
        ("Explain attention mechanism in detail", "Tutorial/learning"),
        ("Compare BERT vs GPT architectures and performance", "Analysis paper"),
        ("Comprehensive review of LLM training methodologies and best practices", "Exhaustive review"),
    ]

    for query, context in research_queries:
        budget, analysis = auto_select_budget(query)

        print(f"Research Goal: {context}")
        print(f"  Query: '{query}'")
        print(f"  Auto-Detected: {analysis.query_complexity.upper()}")
        print(f"  Budget Assigned: {budget} tokens")
        print(f"  Confidence: {analysis.confidence:.0%}")
        print(f"  ✓ Ready to search\n")


def main():
    """Run all demos"""
    print("\n" + "█" * 140)
    print("█" + " " * 138 + "█")
    print("█" + "  PyStreamPDF: Automatic Token Budget Selection".center(138) + "█")
    print("█" + " " * 138 + "█")
    print("█" * 140)

    demos = [
        ("Query Analysis", demo_1_basic_analysis),
        ("Keyword Matching", demo_2_keyword_matching),
        ("Auto-Select Budget", demo_3_auto_select),
        ("Force Override", demo_4_force_override),
        ("Selector Object", demo_5_selector_object),
        ("Custom Keywords", demo_6_custom_keywords),
        ("Budget Comparison", demo_7_summary_comparison),
        ("Confidence Scores", demo_8_confidence_scores),
        ("Real-World Scenario", demo_9_real_world_scenario),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Demo {i} ({name}) failed: {e}")

    print("\n" + "=" * 140)
    print("✨ All demos complete!")
    print("=" * 140)
    print("\nFor more information, see: docs/AUTO_BUDGET_SELECTION.md\n")


if __name__ == "__main__":
    main()
