"""
Pipeline visualization for PyStreamPDF
Terminal-friendly CLI rendering of extraction → indexing → retrieval → selection flow
"""

from typing import Optional, List


class SectionFlowData:
    """Represents a section's journey through the pipeline"""

    def __init__(
        self,
        title: str,
        pages: str,
        raw_words: int,
        extracted_words: int,
        indexed_words: int,
        retrieved_words: int,
        selected_words: int,
        selected: bool,
        relevance_score: Optional[float] = None,
        reason: Optional[str] = None,
    ):
        self.title = title
        self.pages = pages
        self.raw_words = raw_words
        self.extracted_words = extracted_words
        self.indexed_words = indexed_words
        self.retrieved_words = retrieved_words
        self.selected_words = selected_words
        self.selected = selected
        self.relevance_score = relevance_score
        self.reason = reason

    def extraction_loss(self) -> int:
        return max(0, self.raw_words - self.extracted_words)

    def indexing_loss(self) -> int:
        return max(0, self.extracted_words - self.indexed_words)

    def retrieval_loss(self) -> int:
        return max(0, self.indexed_words - self.retrieved_words)

    def filtering_loss(self) -> int:
        return max(0, self.retrieved_words - self.selected_words)

    def extraction_loss_pct(self) -> float:
        if self.raw_words == 0:
            return 0.0
        return (self.extraction_loss() / self.raw_words) * 100.0


class PipelineSummaryData:
    """Summary statistics for the entire pipeline"""

    def __init__(
        self,
        raw_words: int,
        extracted_words: int,
        indexed_words: int,
        retrieved_words: int,
        selected_words: int,
    ):
        self.raw_words = raw_words
        self.extracted_words = extracted_words
        self.indexed_words = indexed_words
        self.retrieved_words = retrieved_words
        self.selected_words = selected_words

    def extraction_loss(self) -> int:
        return max(0, self.raw_words - self.extracted_words)

    def indexing_loss(self) -> int:
        return max(0, self.extracted_words - self.indexed_words)

    def retrieval_loss(self) -> int:
        return max(0, self.indexed_words - self.retrieved_words)

    def filtering_loss(self) -> int:
        return max(0, self.retrieved_words - self.selected_words)

    def extraction_loss_pct(self) -> float:
        if self.raw_words == 0:
            return 0.0
        return (self.extraction_loss() / self.raw_words) * 100.0

    def retrieval_loss_pct(self) -> float:
        if self.indexed_words == 0:
            return 0.0
        return (self.retrieval_loss() / self.indexed_words) * 100.0

    def filtering_loss_pct(self) -> float:
        if self.retrieved_words == 0:
            return 0.0
        return (self.filtering_loss() / self.retrieved_words) * 100.0


class PipelineFlowVisualizer:
    """Renders pipeline flow as CLI-friendly visualizations"""

    def __init__(self, query: str, sections: List[SectionFlowData], summary: PipelineSummaryData):
        self.query = query
        self.sections = sections
        self.summary = summary

    def to_cli_table(self) -> str:
        """Format as terminal table"""
        lines = []
        lines.append("\n" + "=" * 140)
        lines.append(f'PDF PROCESSING PIPELINE: "{self.query}"')
        lines.append("=" * 140)
        lines.append("")

        # Headers
        lines.append(
            f"{'Section':<40} | {'Raw':<6} | {'Extract':<12} | {'Index':<12} | {'Retrieve':<12} | {'Select':<12}"
        )
        lines.append("-" * 140)

        for section in self.sections:
            name = section.title[:35].ljust(35) if len(section.title) > 35 else section.title.ljust(35)
            pages = f"p.{section.pages}"
            raw_col = f"{section.raw_words:4d}w"

            # Extract column
            extract_marker = "[*]" if section.extraction_loss() > 0 else "[OK]"
            extract_col = f"{extract_marker} {section.extracted_words:4d}w"
            if section.extraction_loss() > 0:
                extract_col += f" (-{section.extraction_loss()})"

            # Index column
            index_marker = "[*]" if section.indexing_loss() > 0 else "[OK]"
            index_col = f"{index_marker} {section.indexed_words:4d}w"
            if section.indexing_loss() > 0:
                index_col += f" (-{section.indexing_loss()})"

            # Retrieve column
            retrieve_col = (
                f"[OK] {section.retrieved_words:4d}w"
                if section.retrieved_words > 0
                else "[--]    0w"
            )

            # Select column
            if section.selected_words > 0:
                select_col = f"[OK] {section.selected_words:4d}w"
            elif section.filtering_loss() > 0:
                select_col = "[X]     0w"
            else:
                select_col = "[--]    0w"

            lines.append(
                f"{name} {pages:<8} | {raw_col:<6} | {extract_col:<12} | {index_col:<12} | {retrieve_col:<12} | {select_col:<12}"
            )

        lines.append("")
        lines.append("=" * 140)
        lines.append("LEGEND:")
        lines.append("  [OK]  = Passed through this stage")
        lines.append("  [*]   = Data loss at this stage (text missed during extraction/indexing)")
        lines.append("  [--]  = Filtered out at this stage (intentional filtering)")
        lines.append("  [X]   = Exceeds token budget constraint")
        lines.append("=" * 140)
        lines.append("")

        return "\n".join(lines)

    def to_flow_diagram(self) -> str:
        """Format as text flow diagram"""
        lines = []
        lines.append("")
        lines.append("=" * 140)
        lines.append("PIPELINE SUMMARY: Complete Text Flow")
        lines.append("=" * 140)
        lines.append("")

        s = self.summary
        lines.append("                       PDF Content")
        lines.append("                            |")
        lines.append(f"                    {s.raw_words} words [RAW PDF]")
        lines.append("                            |")
        lines.append("                      Extraction")
        lines.append("                      pdfium-render")
        lines.append("                            v")

        if s.extraction_loss() > 0:
            lines.append(
                f"  [WARNING] Lost {s.extraction_loss()} words ({s.extraction_loss_pct():.1f}%) during parsing"
            )
            lines.append("            -> Likely causes: scanned PDF, embedded images, complex formatting")

        lines.append(f"                    {s.extracted_words} words [EXTRACTED]")
        lines.append("                            |")
        lines.append("                         Indexing")
        lines.append("                       FTS5 cleanup")
        lines.append("                            v")

        if s.indexing_loss() > 0:
            lines.append(f"  [INFO] Normalized {s.indexing_loss()} words during indexing")

        lines.append(f"                    {s.indexed_words} words [INDEXED]")
        lines.append("                            |")
        lines.append("                    Query Matching")
        lines.append("                      (keyword/score)")
        lines.append("                            v")

        lines.append(
            f"  [FILTER] {s.retrieval_loss()} words ({s.retrieval_loss_pct():.1f}%) not relevant to query"
        )
        lines.append(f"                    {s.retrieved_words} words [RETRIEVED]")
        lines.append("                            |")
        lines.append("                     Token Budget")
        lines.append("                      (max_tokens constraint)")
        lines.append("                            v")

        if s.filtering_loss() > 0:
            lines.append(
                f"  [FILTER] {s.filtering_loss()} words ({s.filtering_loss_pct():.1f}%) exceeds budget"
            )

        lines.append(f"                    {s.selected_words} words [SELECTED]")
        lines.append("                            |")
        lines.append("                       Send to LLM")
        lines.append("")
        lines.append("=" * 140)
        lines.append("")

        return "\n".join(lines)

    def print_table(self) -> None:
        """Print CLI table to stdout"""
        print(self.to_cli_table())

    def print_flow(self) -> None:
        """Print flow diagram to stdout"""
        print(self.to_flow_diagram())

    def print_full(self) -> None:
        """Print both table and diagram"""
        print(self.to_cli_table())
        print(self.to_flow_diagram())
