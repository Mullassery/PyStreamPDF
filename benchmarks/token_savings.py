#!/usr/bin/env python3
"""Committed token-savings benchmark (synthetic, no external PDF corpus).

Measures the real ``SemanticChunker`` and ``TokenBudgetConfig`` on a
generated multi-section document, then reports the token reduction from
scoping a query to matching sections instead of sending the whole document.

This is a reproducible micro-benchmark, not a claim about every PDF. Run it
on your own documents to get numbers for your workload.
"""

from __future__ import annotations

import argparse
import statistics
import time

from pystreampdf import BudgetRule, SemanticChunker, TokenBudgetConfig
from pystreampdf.extraction import ElementType, count_tokens

SECTIONS = {
    "financial": (
        "Quarterly revenue rose 12% year over year. Operating margin remained "
        "flat at 18% while free cash flow improved. Management raised full-year "
        "guidance on stronger enterprise demand."
    ),
    "legal": (
        "The agreement is governed by the laws of the State of Delaware. "
        "Either party may terminate for material breach after a thirty-day "
        "cure period. Confidentiality obligations survive termination."
    ),
    "operations": (
        "Warehouse throughput increased after the conveyor upgrade. Inventory "
        "turnover improved and backlog fell for the third consecutive month. "
        "Two new distribution centers are scheduled to open next year."
    ),
    "people": (
        "Headcount grew 7% with most additions in engineering and support. "
        "Voluntary attrition declined. The onboarding program was expanded to "
        "cover all new managers."
    ),
}


def build_document(paragraphs_per_section: int) -> tuple[str, list[tuple[str, str]]]:
    blocks = []
    sections = []
    for index in range(1, paragraphs_per_section + 1):
        for name, paragraph in SECTIONS.items():
            body = " ".join([paragraph] * 2) + f" (section {index})"
            blocks.append(f"{name.title()} update {index}\n\n{body}")
            sections.append((name, body))
    return "\n\n".join(blocks), sections


def run(paragraphs_per_section: int, iterations: int, query_section: str) -> None:
    document, sections = build_document(paragraphs_per_section)
    budget_config = TokenBudgetConfig(
        base_budget=1000,
        rules=[BudgetRule(query_section, 2.0, match_fields=["filename"])],
    )
    budget = budget_config.evaluate(f"{query_section}_report.pdf")
    chunker = SemanticChunker(target_chunk_size=1000, target_tokens=200)

    timings = []
    chunks = []
    for _ in range(iterations):
        started = time.perf_counter()
        chunks = chunker.chunk_content(document, ElementType.TEXT, 1, paragraphs_per_section * 4)
        timings.append((time.perf_counter() - started) * 1000)

    full_tokens = count_tokens(document)
    chunk_tokens = sum(chunk.estimated_tokens for chunk in chunks)
    query_chunks = [chunk for chunk in chunks if query_section in chunk.content.lower()]
    scoped_tokens = sum(chunk.estimated_tokens for chunk in query_chunks)
    selected_tokens = 0
    selected_chunks = 0
    for chunk in query_chunks:
        if selected_tokens + chunk.estimated_tokens > budget:
            break
        selected_tokens += chunk.estimated_tokens
        selected_chunks += 1
    reduction = (1 - selected_tokens / full_tokens) * 100 if full_tokens else 0.0

    chars_per_second = len(document) / (statistics.fmean(timings) / 1000)

    print(f"document chars: {len(document)}  sections: {len(sections)}")
    print(f"full-document tokens: {full_tokens}")
    print(f"chunked tokens (all sections): {chunk_tokens}")
    print(f"budget for query section: {budget} tokens")
    print(f"query-scoped sections: {len(query_chunks)}  tokens (unbudgeted): {scoped_tokens}")
    print(f"selected chunks within budget: {selected_chunks}  tokens: {selected_tokens}")
    print(f"token reduction (budgeted query vs whole document): {reduction:.1f}%")
    print(
        "chunking latency ms: "
        f"mean={statistics.fmean(timings):.2f} "
        f"p95={sorted(timings)[min(len(timings) - 1, int(len(timings) * 0.95))]:.2f}"
    )
    print(f"chunking throughput: {chars_per_second:,.0f} chars/sec")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sections", type=int, default=40, help="Paragraphs per section")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument(
        "--query-section",
        choices=sorted(SECTIONS),
        default="financial",
        help="Section the synthetic query targets",
    )
    args = parser.parse_args()
    if args.sections < 1 or args.iterations < 1:
        parser.error("--sections and --iterations must be positive")
    run(args.sections, args.iterations, args.query_section)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
