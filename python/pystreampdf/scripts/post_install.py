"""Post-installation message for PyStreamPDF"""


def post_install():
    message = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ PyStreamPDF v2.1.0 installed successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 WHAT IS PyStreamPDF?
   High-performance document processing pipeline. Extract text and structure
   from 1000s of PDFs with batch processing, progress tracking, and multi-format output.

🚀 GET STARTED IN 2 MINUTES:

   Step 1 — Ingest PDFs from directory:
   $ pystreampdf ingest ./documents --watch

   Step 2 — Extract to markdown format:
   $ pystreampdf extract --format markdown --output ./markdown

   Step 3 — View processing dashboard:
   $ pystreampdf dashboard

📚 KEY FEATURES YOU CAN DO:
   • Batch process 1000s of PDFs with real-time progress tracking
   • Extract text, tables, and structure with high accuracy
   • Multi-format output: Markdown, JSON, XML
   • Error recovery and automatic retries for failed documents
   • Watch mode: automatically process new PDFs as they arrive
   • Real-time processing dashboard and metrics

📊 VIEW DASHBOARD:
   $ pystreampdf dashboard              # Interactive processing view
   $ pystreampdf dashboard --static     # Static snapshot
   $ pystreampdf dashboard --alerts     # Show alerts only

📖 LEARN MORE:
   Quick Start:  https://github.com/mullassery/pystreampdf#quickstart
   Examples:     https://github.com/mullassery/pystreampdf/tree/main/examples
   Issues:       https://github.com/mullassery/pystreampdf/issues

❓ GET HELP ANYTIME:
   $ pystreampdf --help
   $ pystreampdf --version
   $ pystreampdf ingest --help         # Help for specific command

⏱️  NEXT STEP: Run `pystreampdf ingest ./documents` to start processing!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(message)


if __name__ == "__main__":
    post_install()
