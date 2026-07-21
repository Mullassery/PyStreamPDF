"""Example: Using token budget configuration and PDF caching together.

This example demonstrates how to:
1. Define keyword-based token budget rules via YAML
2. Cache PDFs to avoid re-processing
3. Automatically adjust token budgets based on document metadata
4. Track cache performance metrics
"""

from pathlib import Path
import tempfile
from pystreampdf import (
    TokenBudgetConfig,
    BudgetRule,
    PDFCache,
    SemanticChunker,
    ElementType,
)


def example_basic_budget_config():
    """Example 1: Basic token budget configuration."""
    print("=" * 60)
    print("Example 1: Basic Token Budget Configuration")
    print("=" * 60)

    # Option A: Define rules in code
    rules = [
        BudgetRule("financial", 2.0, match_fields=["filename", "title"]),
        BudgetRule("summary", 0.5, match_fields=["filename"]),
        BudgetRule("quarterly", 3.0, match_fields=["content_preview"]),
    ]
    config = TokenBudgetConfig(base_budget=2000, rules=rules)

    # Evaluate budgets for different documents
    print("\nBase budget: 2000 tokens")
    print("Rules: financial (2.0x), summary (0.5x), quarterly (3.0x)")
    print()

    test_cases = [
        ("annual_report.pdf", None, None),
        ("financial_report.pdf", None, None),
        ("summary_2024.pdf", None, None),
        ("financial_quarterly_report.pdf", None, None),
        ("report.pdf", "Quarterly Financial Summary", None),
    ]

    for filename, title, preview in test_cases:
        budget = config.evaluate(filename, title, preview)
        print(f"  {filename:40s} → {budget:5d} tokens")

    print()


def example_yaml_config():
    """Example 2: Load token budget config from YAML file."""
    print("=" * 60)
    print("Example 2: YAML Configuration")
    print("=" * 60)

    # Create a sample YAML config
    yaml_content = """
base_budget: 2000

rules:
  - keyword: financial
    multiplier: 2.0
    match_fields: [filename, title]
    case_sensitive: false

  - keyword: legal
    multiplier: 2.5
    match_fields: [filename, title, content_preview]
    case_sensitive: false

  - keyword: summary
    multiplier: 0.5
    match_fields: [filename]

  - keyword: draft
    multiplier: 0.75
    match_fields: [filename]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    # Load from YAML
    config = TokenBudgetConfig.from_yaml(yaml_path)

    print(f"\nLoaded config from: {yaml_path}")
    print(f"Base budget: {config.base_budget}")
    print(f"Number of rules: {len(config.rules)}")
    print()

    for rule in config.rules:
        print(f"  '{rule.keyword}' → {rule.multiplier}x in {rule.match_fields}")

    print()


def example_pdf_caching():
    """Example 3: Using PDF caching with token budgets."""
    print("=" * 60)
    print("Example 3: PDF Caching with Token Budget Integration")
    print("=" * 60)

    # Define budget configuration
    config = TokenBudgetConfig(
        base_budget=2000,
        rules=[
            BudgetRule("financial", 2.0, match_fields=["filename"]),
        ],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize cache with budget config
        cache = PDFCache(
            memory_limit_mb=500,
            disk_cache_dir=tmpdir,
            token_budget_config=config,
        )

        print(f"\nCache directory: {tmpdir}")
        print(f"Memory limit: 500 MB")
        print(f"Token budget config: base=2000, financial=2.0x")
        print()

        # Simulate processing different PDFs
        def simulate_pdf_processing(path):
            """Simulate PDF extraction."""
            print(f"  → Processing: {Path(path).name}")

            # In real usage, you would extract chunks like:
            # chunker = SemanticChunker(target_tokens=500)
            # chunks = chunker.chunk_content(...)

            # For this example, return mock chunks
            from pystreampdf.extraction import ContentChunk

            chunks = [
                ContentChunk(
                    content=f"Sample content from {Path(path).name}",
                    chunk_type=ElementType.TEXT,
                    page_start=1,
                    page_end=1,
                    estimated_tokens=100,
                )
            ]

            return chunks, "Sample preview text...", "Document Title", 10

        # Create test PDFs
        test_files = []
        for name in ["financial_report.pdf", "summary.pdf"]:
            with tempfile.NamedTemporaryFile(
                suffix=f"_{name}", delete=False
            ) as f:
                f.write(b"PDF content" * 100)
                test_files.append(f.name)

        print("Processing PDFs (first time - cache miss):")
        results = []
        for path in test_files:
            doc = cache.get_or_process(path, simulate_pdf_processing)
            results.append((Path(path).name, doc.evaluated_budget))

        print("\nCache statistics after first pass:")
        stats = cache.stats()
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']:.1%}")
        print()

        print("Processing PDFs (second time - cache hit):")
        for path in test_files:
            doc = cache.get_or_process(path, simulate_pdf_processing)
            filename = Path(path).name
            print(f"  ✓ {filename} cached, budget={doc.evaluated_budget}")

        print("\nCache statistics after second pass:")
        stats = cache.stats()
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']:.1%}")
        print(f"  L1 entries: {stats['l1_entries']}")
        print(f"  Memory used: {stats['memory_used_mb']:.2f} MB")
        print(f"  Disk used: {stats['disk_used_mb']:.2f} MB")

        print()


def example_integration_with_chunker():
    """Example 4: Using budget override with SemanticChunker."""
    print("=" * 60)
    print("Example 4: Integration with SemanticChunker")
    print("=" * 60)

    # Create budget config
    config = TokenBudgetConfig(
        base_budget=2000,
        rules=[BudgetRule("financial", 2.0, match_fields=["filename"])],
    )

    # Create chunker
    chunker = SemanticChunker(target_tokens=500)

    print("\nSemanticChunker can accept budget overrides per call:")
    print()

    # Simulate extracting chunks with different budgets
    sample_text = """
    This is a sample document with multiple paragraphs.

    Each paragraph will be split into chunks based on the target token budget.

    This demonstrates how budget rules can be applied during extraction.
    """

    print("Option 1: Use default chunk size (500 tokens)")
    chunks_default = chunker.chunk_content(
        sample_text,
        ElementType.TEXT,
        page_start=1,
        page_end=1,
    )
    print(f"  → Created {len(chunks_default)} chunks")

    print("\nOption 2: Override with keyword-adjusted budget (1000 tokens)")
    chunks_large = chunker.chunk_content(
        sample_text,
        ElementType.TEXT,
        page_start=1,
        page_end=1,
        budget_override=1000,  # 2x the default
    )
    print(f"  → Created {len(chunks_large)} chunks")

    print()


def main():
    """Run all examples."""
    example_basic_budget_config()
    example_yaml_config()
    example_pdf_caching()
    example_integration_with_chunker()

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
