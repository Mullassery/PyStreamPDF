#!/usr/bin/env python3
"""
Search and Filtering Demo - Shows realistic examples with mock data
"""

from pystreampdf.search import SearchResult, SearchFilter, SearchResults, combine_filters


def create_sample_results():
    """Create sample search results for demonstration"""
    results = [
        SearchResult(
            section_title="Chapter 1: Introduction to Neural Networks",
            page_start=1,
            page_end=8,
            relevance_score=0.95,
            word_count=3200,
            preview="Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes that process information using connectionist approaches.",
            matched_terms=["neural", "networks"]
        ),
        SearchResult(
            section_title="Chapter 2: Fundamentals of Deep Learning",
            page_start=9,
            page_end=15,
            relevance_score=0.82,
            word_count=2800,
            preview="Deep learning is part of a broader family of machine learning methods based on learning data representations. The networks learn multiple levels of representations.",
            matched_terms=["learning", "networks"]
        ),
        SearchResult(
            section_title="Section 3.1: Activation Functions",
            page_start=20,
            page_end=25,
            relevance_score=0.78,
            word_count=1500,
            preview="Activation functions introduce non-linearity to neural networks. Common functions include ReLU, sigmoid, and tanh. Each has different properties and use cases.",
            matched_terms=["neural", "networks"]
        ),
        SearchResult(
            section_title="Chapter 4: Convolutional Neural Networks",
            page_start=28,
            page_end=45,
            relevance_score=0.88,
            word_count=5200,
            preview="CNNs are designed for processing grid-like data, especially images. They use local connections and weight sharing to reduce parameters and improve efficiency.",
            matched_terms=["neural", "networks"]
        ),
        SearchResult(
            section_title="Section 5.2: Recurrent Neural Networks",
            page_start=50,
            page_end=62,
            relevance_score=0.85,
            word_count=4100,
            preview="RNNs are powerful for sequential data. They maintain hidden states that capture temporal dependencies. LSTMs and GRUs are popular variants.",
            matched_terms=["neural", "networks"]
        ),
        SearchResult(
            section_title="Appendix A: Mathematical Notation",
            page_start=200,
            page_end=210,
            relevance_score=0.45,
            word_count=800,
            preview="This appendix defines mathematical notation used throughout the book. Includes matrix operations, derivatives, and vector spaces.",
            matched_terms=["networks"]
        ),
    ]
    return SearchResults("neural networks", results)


def demo_1_basic_display():
    """Demo 1: Basic search result display"""
    print("\n" + "=" * 100)
    print("DEMO 1: Basic Search Result Display")
    print("=" * 100)

    results = create_sample_results()
    print(f"\nSearch query: '{results.query}'")
    print(f"Found {results.count()} results\n")
    print(results.to_cli_table())


def demo_2_filtering_by_relevance():
    """Demo 2: Filter by relevance score"""
    print("\n" + "=" * 100)
    print("DEMO 2: Filter by Relevance Score")
    print("=" * 100)

    results = create_sample_results()

    print(f"\nOriginal results: {results.count()}")
    print(results.to_cli_table())

    print("\n" + "-" * 100)
    print("After filtering for relevance > 0.80:")
    print("-" * 100)

    filtered = results.by_relevance(0.80)
    print(f"\nFiltered results: {filtered.count()}\n")
    print(filtered.to_cli_table())


def demo_3_filtering_by_pages():
    """Demo 3: Filter by page range"""
    print("\n" + "=" * 100)
    print("DEMO 3: Filter by Page Range")
    print("=" * 100)

    results = create_sample_results()

    print(f"\nOriginal results: {results.count()}")
    print(results.to_cli_table())

    print("\n" + "-" * 100)
    print("After filtering for pages 1-50 (main content, exclude appendix):")
    print("-" * 100)

    filtered = results.by_page_range(1, 50)
    print(f"\nFiltered results: {filtered.count()}\n")
    print(filtered.to_cli_table())


def demo_4_filtering_by_section():
    """Demo 4: Filter by section title"""
    print("\n" + "=" * 100)
    print("DEMO 4: Filter by Section Title")
    print("=" * 100)

    results = create_sample_results()

    print(f"\nOriginal results: {results.count()}")
    print(results.to_cli_table())

    print("\n" + "-" * 100)
    print("After filtering for 'Chapter' in title:")
    print("-" * 100)

    filtered = results.by_section("chapter")
    print(f"\nFiltered results: {filtered.count()}\n")
    print(filtered.to_cli_table())


def demo_5_filtering_by_length():
    """Demo 5: Filter by content length"""
    print("\n" + "=" * 100)
    print("DEMO 5: Filter by Content Length")
    print("=" * 100)

    results = create_sample_results()

    print(f"\nOriginal results: {results.count()}")
    print(results.to_cli_table())

    print("\n" + "-" * 100)
    print("After filtering for 2000-4500 words (substantial content):")
    print("-" * 100)

    filtered = results.by_length(min_words=2000, max_words=4500)
    print(f"\nFiltered results: {filtered.count()}\n")
    print(filtered.to_cli_table())


def demo_6_chaining_filters():
    """Demo 6: Chain multiple filters"""
    print("\n" + "=" * 100)
    print("DEMO 6: Chaining Multiple Filters")
    print("=" * 100)

    results = create_sample_results()

    print(f"\nStarting with: {results.count()} results")

    print("\nApplying filters in sequence:")
    print("  1. Relevance > 0.80")
    print("  2. Pages 1-60 (main chapters)")
    print("  3. Length 2000+ words (substantial)")
    print("  4. Sort by relevance\n")

    filtered = (results
        .by_relevance(0.80)
        .by_page_range(1, 60)
        .by_length(min_words=2000)
        .sorted_by_relevance())

    print(f"Final filtered results: {filtered.count()}\n")
    print(filtered.to_cli_table())


def demo_7_combining_filters():
    """Demo 7: Combine filters with AND logic"""
    print("\n" + "=" * 100)
    print("DEMO 7: Advanced Filter Combination (AND logic)")
    print("=" * 100)

    results = create_sample_results()

    # Create individual filters
    high_relevance = SearchFilter.by_relevance(0.75)
    main_chapters = SearchFilter.by_page_range(1, 100)
    substantial = SearchFilter.by_length(min_words=2000)

    print(f"\nStarting with: {results.count()} results")
    print("\nCreating combined filter from:")
    print("  - Relevance filter: min_score=0.75")
    print("  - Page filter: pages 1-100")
    print("  - Length filter: min 2000 words\n")

    combined = combine_filters(high_relevance, main_chapters, substantial)
    filtered = results.filter(combined)

    print(f"Results matching all criteria: {filtered.count()}\n")
    print(filtered.to_cli_table())


def demo_8_sorting():
    """Demo 8: Sorting results"""
    print("\n" + "=" * 100)
    print("DEMO 8: Sorting Results")
    print("=" * 100)

    results = create_sample_results()

    print("\nSort by relevance (highest first):")
    print("-" * 100)
    by_relevance = results.sorted_by_relevance(descending=True)
    for i, result in enumerate(by_relevance.results, 1):
        print(f"{i}. {result.relevance_score:.0%} | {result.pages_range():10} | {result.section_title}")

    print("\nSort by page number (ascending):")
    print("-" * 100)
    by_pages = results.sorted_by_pages(ascending=True)
    for i, result in enumerate(by_pages.results, 1):
        print(f"{i}. {result.pages_range():10} | {result.relevance_score:.0%} | {result.section_title}")


def demo_9_sampling():
    """Demo 9: Get top results"""
    print("\n" + "=" * 100)
    print("DEMO 9: Sampling (Top N Results)")
    print("=" * 100)

    results = create_sample_results()

    print(f"\nOriginal results: {results.count()}")
    print(results.to_cli_table())

    print("\n" + "-" * 100)
    print("Top 3 results (by relevance):")
    print("-" * 100)

    top_3 = results.sorted_by_relevance().top(3)
    print(f"\nResults: {top_3.count()}\n")
    print(top_3.to_cli_table())


def demo_10_export():
    """Demo 10: Export formats"""
    print("\n" + "=" * 100)
    print("DEMO 10: Export Formats")
    print("=" * 100)

    results = create_sample_results().by_relevance(0.80).top(2)

    print("\nAs JSON:")
    print("-" * 100)
    print(results.to_json(pretty=True))

    print("\n\nAs Summary:")
    print("-" * 100)
    print(results.summary())


def demo_11_metadata_access():
    """Demo 11: Access individual result metadata"""
    print("\n" + "=" * 100)
    print("DEMO 11: Accessing Result Metadata")
    print("=" * 100)

    results = create_sample_results()
    result = results.results[0]  # Get first result

    print(f"\nMetadata from: '{result.section_title}'")
    print("-" * 100)
    print(f"Section Title:    {result.section_title}")
    print(f"Pages:            {result.pages_range()}")
    print(f"Page Start:       {result.page_start}")
    print(f"Page End:         {result.page_end}")
    print(f"Relevance Score:  {result.relevance_score:.2f} ({result.relevance_score:.0%})")
    print(f"Word Count:       {result.word_count}")
    print(f"Preview:          {result.preview}")
    print(f"Matched Terms:    {', '.join(result.matched_terms)}")

    print(f"\nAs dictionary:")
    print(result.to_dict())


def main():
    """Run all demos"""
    print("\n")
    print("█" * 100)
    print("█" + " " * 98 + "█")
    print("█" + "  PyStreamPDF: Search Results and Filtering Examples".center(98) + "█")
    print("█" + " " * 98 + "█")
    print("█" * 100)

    demos = [
        ("Basic Display", demo_1_basic_display),
        ("Filter by Relevance", demo_2_filtering_by_relevance),
        ("Filter by Page Range", demo_3_filtering_by_pages),
        ("Filter by Section Title", demo_4_filtering_by_section),
        ("Filter by Content Length", demo_5_filtering_by_length),
        ("Chain Filters", demo_6_chaining_filters),
        ("Combine Filters (AND)", demo_7_combining_filters),
        ("Sorting", demo_8_sorting),
        ("Sampling (Top N)", demo_9_sampling),
        ("Export Formats", demo_10_export),
        ("Metadata Access", demo_11_metadata_access),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        demo_func()
        if i < len(demos):
            input(f"\nPress Enter to continue to Demo {i+1}... ({name}) ")

    print("\n" + "=" * 100)
    print("All demos complete!")
    print("=" * 100)
    print("\nFor more information, see: docs/SEARCH_RESULTS_FILTERING.md")


if __name__ == "__main__":
    main()
