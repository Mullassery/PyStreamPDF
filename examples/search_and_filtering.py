#!/usr/bin/env python3
"""
Example: Search and Filtering

Demonstrates PyStreamPDF's search result metadata and filtering capabilities.
Shows how to search documents, filter results by various criteria, and display results.
"""

import pystreampdf
from pystreampdf.search import SearchFilter, combine_filters


def example_basic_search():
    """Basic search with result display"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Search with Result Display")
    print("=" * 80)

    # Setup
    doc = pystreampdf.open("document.pdf")
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    # Search
    results = navigator.search("neural networks", max_results=10)

    # Display
    print(f"\nFound {results.count()} results for 'neural networks'")
    print("\nResults as table:")
    print(results.to_cli_table())

    print("\nSummary:")
    print(results.summary())


def example_filtering():
    """Filter search results by various criteria"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Filtering Search Results")
    print("=" * 80)

    doc = pystreampdf.open("document.pdf")
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    # Get initial results
    results = navigator.search("machine learning", max_results=20)
    print(f"\nInitial results: {results.count()}")

    # Filter 1: By relevance
    filtered_1 = results.by_relevance(0.7)
    print(f"After filtering by relevance (>0.7): {filtered_1.count()}")

    # Filter 2: By page range
    filtered_2 = results.by_page_range(10, 50)
    print(f"After filtering by page range (10-50): {filtered_2.count()}")

    # Filter 3: By section title
    filtered_3 = results.by_section("chapter")
    print(f"After filtering by section 'chapter': {filtered_3.count()}")

    # Filter 4: By content length
    filtered_4 = results.by_length(min_words=200, max_words=800)
    print(f"After filtering by length (200-800 words): {filtered_4.count()}")


def example_chaining_filters():
    """Chain multiple filters together"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Chaining Filters")
    print("=" * 80)

    doc = pystreampdf.open("document.pdf")
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    # Search with chained filters
    results = (navigator.search("optimization")
               .by_page_range(1, 100)           # First 100 pages
               .by_relevance(0.5)               # 50%+ relevance
               .by_length(min_words=100)        # At least 100 words
               .sorted_by_relevance()           # Sort by score
               .top(5))                         # Top 5 only

    print(f"\nFiltered results (chained): {results.count()}")
    print(results.to_cli_table())


def example_advanced_filtering():
    """Advanced: Combine filters with AND logic"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Advanced Filter Combination")
    print("=" * 80)

    doc = pystreampdf.open("document.pdf")
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    # Create individual filters
    by_pages = SearchFilter.by_page_range(20, 80)
    by_score = SearchFilter.by_relevance(0.6)
    by_length = SearchFilter.by_length(min_words=150, max_words=600)

    # Combine filters (AND logic)
    combined = combine_filters(by_pages, by_score, by_length)

    # Apply combined filter
    results = navigator.search("training").filter(combined)

    print(f"\nResults with combined filter: {results.count()}")
    print(results.to_cli_table())


def example_sorting():
    """Sort results by different criteria"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Sorting Results")
    print("=" * 80)

    doc = pystreampdf.open("document.pdf")
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    results = navigator.search("algorithm", max_results=10)

    # Sort by relevance (highest first)
    print(f"\nSorted by relevance (highest first):")
    by_score = results.sorted_by_relevance(descending=True)
    for r in by_score.results[:3]:
        print(f"  {r.relevance_score:.0%} | {r.section_title}")

    # Sort by page number (ascending)
    print(f"\nSorted by page (ascending):")
    by_page = results.sorted_by_pages(ascending=True)
    for r in by_page.results[:3]:
        print(f"  {r.pages_range()} | {r.section_title}")


def example_export():
    """Export search results"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Exporting Results")
    print("=" * 80)

    doc = pystreampdf.open("document.pdf")
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    results = navigator.search("neural networks", max_results=5)

    # Export as JSON
    print("\nJSON Export:")
    print(results.to_json(pretty=True))

    # Export as table
    print("\nTable Export:")
    print(results.to_cli_table())

    # Custom processing
    print("\nCustom Processing:")
    for result in results.results:
        data = result.to_dict()
        print(f"  {data['section_title']} ({data['pages']}) - {data['relevance_score']}%")


def example_metadata_access():
    """Access individual result metadata"""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Accessing Result Metadata")
    print("=" * 80)

    doc = pystreampdf.open("document.pdf")
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    results = navigator.search("learning", max_results=5)

    if results.count() > 0:
        result = results.results[0]

        print("\nMetadata from first result:")
        print(f"  Section Title: {result.section_title}")
        print(f"  Page Range: {result.pages_range()}")
        print(f"  Start Page: {result.page_start}")
        print(f"  End Page: {result.page_end}")
        print(f"  Relevance Score: {result.relevance_score:.2f}")
        print(f"  Word Count: {result.word_count}")
        print(f"  Preview: {result.preview[:100]}...")
        print(f"  Matched Terms: {result.matched_terms}")


if __name__ == "__main__":
    print("PyStreamPDF Search and Filtering Examples")
    print("=" * 80)
    print()
    print("These examples show how to:")
    print("1. Perform basic searches and display results")
    print("2. Filter results by various criteria")
    print("3. Chain filters together")
    print("4. Combine filters with AND logic")
    print("5. Sort results by different criteria")
    print("6. Export results as JSON or tables")
    print("7. Access individual result metadata")
    print()
    print("Note: These examples assume 'document.pdf' exists in current directory.")
    print()

    # Uncomment examples to run:
    # example_basic_search()
    # example_filtering()
    # example_chaining_filters()
    # example_advanced_filtering()
    # example_sorting()
    # example_export()
    # example_metadata_access()

    print("See SEARCH_RESULTS_FILTERING.md in docs/ for complete documentation.")
