#!/usr/bin/env python3
"""
PyStreamPDF Pipeline Visualization Example

Shows how to retrieve context and visualize the extraction → indexing → retrieval flow
"""

import sys
import os

# Add parent directory to path for importing pystreampdf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import pystreampdf
    from pystreampdf.pipeline import PipelineFlowVisualizer, SectionFlowData, PipelineSummaryData
except ImportError as e:
    print(f"Error importing pystreampdf: {e}")
    print("Note: Python bindings need to be built with: maturin develop")
    sys.exit(1)


def demo_pipeline_flow():
    """Demonstrate pipeline flow visualization"""

    if len(sys.argv) < 2:
        print("Usage: python3 pipeline_visualization.py <path_to_pdf> [query]")
        print("\nExample:")
        print("  python3 pipeline_visualization.py document.pdf 'machine learning'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "search query"

    try:
        # Open PDF
        doc = pystreampdf.open(pdf_path)
        print(f"\n📄 Opened: {doc.path} ({doc.page_count} pages)")

        # Build index
        index_path = "/tmp/test_index.db"
        index = doc.build_index(index_path)
        print(f"✓ Built index: {index_path}")

        # Create navigator with index
        navigator = doc.navigator_with_index(index)
        print(f"✓ Created navigator")

        # Retrieve context with pipeline flow visualization
        print(f"\n🔍 Retrieving context for: \"{query}\"")
        context, flow = navigator.retrieve_with_flow(query, max_tokens=2000)

        print(f"✓ Retrieved {len(context.sections)} sections")
        print(f"✓ Total tokens: {context.total_tokens}")

        # Display pipeline flow visualizations
        print("\n" + "=" * 140)
        print("📊 PIPELINE FLOW VISUALIZATION")
        print("=" * 140)

        # Print as CLI table
        print(flow.to_cli_table())

        # Print as flow diagram
        print(flow.to_flow_diagram())

        # Print JSON for machine consumption
        print("=" * 140)
        print("📋 JSON REPRESENTATION (for programmatic use)")
        print("=" * 140)
        print(flow.to_json())

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    demo_pipeline_flow()
