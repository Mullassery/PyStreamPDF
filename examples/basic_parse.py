#!/usr/bin/env python3
"""Basic StreamPDF usage example"""

import pystreampdf
import sys

if len(sys.argv) < 2:
    print("Usage: python3 basic_parse.py <path_to_pdf>")
    print("\nExample:")
    print("  python3 basic_parse.py /path/to/document.pdf")
    sys.exit(1)

pdf_path = sys.argv[1]

print(f"Opening PDF: {pdf_path}")
doc = pystreampdf.open(pdf_path)

print(f"\n📄 Document: {doc.path}")
print(f"📊 Page count: {doc.page_count}")

meta = doc.metadata
print(f"\n📋 Metadata:")
print(f"  - Title: {meta.get('title', 'N/A')}")
print(f"  - Author: {meta.get('author', 'N/A')}")
print(f"  - Pages: {meta.get('page_count', 'N/A')}")

print(f"\n📖 First page preview:")
page = doc.page(1)
print(f"  - Page number: {page.page_number}")
print(f"  - Size: {page.width:.0f}x{page.height:.0f} points")
print(f"  - Word count: {page.word_count}")
if page.text_preview:
    preview = page.text_preview[:200]
    print(f"  - Text preview: {preview}...")
else:
    print(f"  - Text preview: (empty)")

print(f"\n🏗️ Document structure:")
structure = doc.structure
if structure.toc:
    print(f"  - Table of contents: {len(structure.toc)} entries")
    for entry in structure.toc[:3]:
        print(f"    - Page {entry.page_number}: {entry.title}")
    if len(structure.toc) > 3:
        print(f"    ... and {len(structure.toc) - 3} more")
else:
    print(f"  - Table of contents: not available")

if structure.headings:
    print(f"  - Headings: {len(structure.headings)} found")
    for heading in structure.headings[:3]:
        indent = "  " * heading.level
        print(f"    {indent}h{heading.level}: {heading.text} (p.{heading.page_number})")
    if len(structure.headings) > 3:
        print(f"    ... and {len(structure.headings) - 3} more")
else:
    print(f"  - Headings: not detected")

print("\n✓ StreamPDF API demonstration complete!")
