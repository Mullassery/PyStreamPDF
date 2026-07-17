"""Enhanced PDF Parsing and Extraction.

Improved handling of:
- Table structure preservation
- Text reading order correction
- Semantic-aware chunking
- Multi-modal element detection
- Citation tracking
- Token estimation
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ElementType(str, Enum):
    """Type of PDF element."""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    HEADING = "heading"
    LIST = "list"
    FORM = "form"
    DIAGRAM = "diagram"
    HANDWRITING = "handwriting"


class ReadingOrder(str, Enum):
    """Text reading order quality."""
    CORRECT = "correct"  # Natural reading order
    NEEDS_FIXING = "needs_fixing"  # Detected issues but fixable
    COMPLEX = "complex"  # Multiple columns or unusual layout


@dataclass
class TextFragment:
    """Single text fragment from PDF."""
    text: str
    x: float  # X coordinate
    y: float  # Y coordinate
    width: float
    height: float
    font_size: Optional[float] = None
    font_name: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False


@dataclass
class TableCell:
    """Cell in an extracted table."""
    content: str
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False


@dataclass
class TableStructure:
    """Extracted table with preserved structure."""
    rows: int
    cols: int
    cells: List[TableCell]
    headers: List[str]
    bounding_box: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float  # 0-1 confidence in extraction
    caption: Optional[str] = None


@dataclass
class MultimediaElement:
    """Detected image, chart, or diagram."""
    type: str  # "image", "chart", "diagram", "handwriting"
    page: int
    x: float
    y: float
    width: float
    height: float
    description: Optional[str] = None  # AI-generated description
    confidence: float = 0.0  # Detection confidence


@dataclass
class SourceLocation:
    """Precise location of a piece of content in PDF."""
    page: int
    bounding_box: Tuple[float, float, float, float]  # x1, y1, x2, y2
    text: str  # Exact source text
    offset_start: int  # Character offset in page
    offset_end: int


@dataclass
class ContentChunk:
    """Semantically meaningful chunk for RAG."""
    content: str
    chunk_type: ElementType
    page_start: int
    page_end: int
    source_locations: List[SourceLocation] = field(default_factory=list)
    heading_path: Optional[str] = None  # Breadcrumb: H1 > H2 > H3
    tables: List[TableStructure] = field(default_factory=list)
    images: List[MultimediaElement] = field(default_factory=list)
    estimated_tokens: int = 0
    confidence: float = 1.0  # Extraction confidence


class ReadingOrderCorrector:
    """Corrects PDF text reading order issues."""

    def __init__(self):
        """Initialize reading order corrector."""
        self.column_threshold = 50.0  # Points to distinguish columns
        self.line_threshold = 10.0  # Points to group into same line

    def analyze_fragments(self, fragments: List[TextFragment]) -> ReadingOrder:
        """Analyze text fragment layout.

        Args:
            fragments: List of text fragments

        Returns:
            Reading order quality assessment
        """
        if not fragments:
            return ReadingOrder.CORRECT

        # Extract Y coordinates (vertical positions)
        y_coords = sorted(set(f.y for f in fragments))
        x_coords = sorted(set(f.x for f in fragments))

        # Detect multi-column layout
        if len(x_coords) > 2 and max(x_coords) - min(x_coords) > 200:
            x_gaps = [x_coords[i + 1] - x_coords[i] for i in range(len(x_coords) - 1)]
            if max(x_gaps) > self.column_threshold:
                return ReadingOrder.COMPLEX

        # Check for fragmented text (unusual Y ordering)
        fragment_y_order = [f.y for f in fragments]
        sorted_y = sorted(fragment_y_order)
        deviation = sum(abs(fragment_y_order[i] - sorted_y[i]) for i in range(len(fragment_y_order)))

        if deviation > 100:
            return ReadingOrder.NEEDS_FIXING

        return ReadingOrder.CORRECT

    def correct_order(self, fragments: List[TextFragment]) -> List[TextFragment]:
        """Reorder fragments to natural reading order.

        Args:
            fragments: List of text fragments

        Returns:
            Fragments in corrected reading order
        """
        if not fragments:
            return []

        # Sort by Y (top-to-bottom), then X (left-to-right)
        sorted_fragments = sorted(fragments, key=lambda f: (round(f.y / self.line_threshold), f.x))
        return sorted_fragments

    def merge_fragments(self, fragments: List[TextFragment]) -> str:
        """Merge corrected fragments into flowing text.

        Args:
            fragments: Ordered text fragments

        Returns:
            Merged text
        """
        if not fragments:
            return ""

        result = []
        current_line_y = fragments[0].y
        line_texts = []

        for frag in fragments:
            # Check if we're on a new line
            if abs(frag.y - current_line_y) > self.line_threshold:
                if line_texts:
                    result.append(" ".join(line_texts))
                    line_texts = []
                current_line_y = frag.y

            line_texts.append(frag.text)

        # Don't forget last line
        if line_texts:
            result.append(" ".join(line_texts))

        return "\n".join(result)


class TableExtractor:
    """Extracts and preserves table structure from PDFs."""

    def __init__(self):
        """Initialize table extractor."""
        self.grid_threshold = 5.0  # Points to snap to grid

    def detect_table_grid(self, elements: List[Dict[str, Any]]) -> Optional[Tuple[List[float], List[float]]]:
        """Detect table grid (rows and columns).

        Args:
            elements: PDF elements (lines, rectangles, text)

        Returns:
            Tuple of (column_x, row_y) or None if no table
        """
        # Collect vertical and horizontal lines
        vertical_lines = []
        horizontal_lines = []

        for elem in elements:
            if elem.get("type") == "line":
                x1, y1, x2, y2 = elem["bbox"]
                if abs(x1 - x2) < 1:  # Vertical line
                    vertical_lines.append(x1)
                elif abs(y1 - y2) < 1:  # Horizontal line
                    horizontal_lines.append(y1)

        # Cluster nearby lines
        if len(vertical_lines) < 2 or len(horizontal_lines) < 2:
            return None

        col_x = self._cluster_coordinates(vertical_lines)
        row_y = self._cluster_coordinates(horizontal_lines)

        return (col_x, row_y)

    def _cluster_coordinates(self, coords: List[float]) -> List[float]:
        """Cluster nearby coordinates.

        Args:
            coords: List of coordinates

        Returns:
            Clustered coordinates
        """
        if not coords:
            return []

        sorted_coords = sorted(coords)
        clusters = [[sorted_coords[0]]]

        for coord in sorted_coords[1:]:
            if coord - clusters[-1][-1] < self.grid_threshold:
                clusters[-1].append(coord)
            else:
                clusters.append([coord])

        return [sum(c) / len(c) for c in clusters]

    def extract_table(
        self,
        grid: Tuple[List[float], List[float]],
        text_elements: List[Dict[str, Any]],
    ) -> TableStructure:
        """Extract table from grid and text.

        Args:
            grid: Column X and row Y coordinates
            text_elements: Text elements within table

        Returns:
            Extracted table structure
        """
        col_x, row_y = grid
        rows = len(row_y) - 1
        cols = len(col_x) - 1

        # Create empty cells
        cells = []
        for r in range(rows):
            for c in range(cols):
                cells.append(TableCell(content="", row=r, col=c))

        # Assign text to cells
        for text_elem in text_elements:
            tx, ty = text_elem["position"]
            text = text_elem["content"]

            # Find cell
            for c in range(cols):
                if col_x[c] <= tx <= col_x[c + 1]:
                    for r in range(rows):
                        if row_y[r] <= ty <= row_y[r + 1]:
                            # Update cell
                            for cell in cells:
                                if cell.row == r and cell.col == c:
                                    cell.content += text + " "

        return TableStructure(
            rows=rows,
            cols=cols,
            cells=cells,
            headers=[c.content.strip() for c in cells if c.row == 0],
            bounding_box=(min(col_x), min(row_y), max(col_x), max(row_y)),
            confidence=0.9,
        )


class SemanticChunker:
    """Creates semantically meaningful chunks for RAG."""

    def __init__(self, target_chunk_size: int = 1000, target_tokens: int = 500):
        """Initialize chunker.

        Args:
            target_chunk_size: Target characters per chunk
            target_tokens: Target tokens per chunk
        """
        self.target_chunk_size = target_chunk_size
        self.target_tokens = target_tokens
        self.token_ratio = 1.0 / 4.0  # Approximate tokens per character

    def chunk_content(
        self,
        content: str,
        element_type: ElementType,
        page_start: int,
        page_end: int,
        heading_path: Optional[str] = None,
    ) -> List[ContentChunk]:
        """Create semantic chunks from content.

        Args:
            content: Text content
            element_type: Type of element
            page_start: Starting page
            page_end: Ending page
            heading_path: Hierarchical heading path

        Returns:
            List of content chunks
        """
        chunks = []

        if element_type == ElementType.TABLE:
            # Tables stay as single chunks
            estimated_tokens = int(len(content) * self.token_ratio)
            chunks.append(ContentChunk(
                content=content,
                chunk_type=element_type,
                page_start=page_start,
                page_end=page_end,
                heading_path=heading_path,
                estimated_tokens=estimated_tokens,
            ))
        else:
            # Text: split by semantic boundaries
            paragraphs = content.split("\n\n")
            current_chunk_text = []
            current_tokens = 0

            for para in paragraphs:
                para_tokens = int(len(para) * self.token_ratio)

                # New chunk if adding this paragraph exceeds target
                if current_tokens + para_tokens > self.target_tokens and current_chunk_text:
                    chunk_content = "\n\n".join(current_chunk_text)
                    chunks.append(ContentChunk(
                        content=chunk_content,
                        chunk_type=element_type,
                        page_start=page_start,
                        page_end=page_end,
                        heading_path=heading_path,
                        estimated_tokens=current_tokens,
                    ))
                    current_chunk_text = []
                    current_tokens = 0

                current_chunk_text.append(para)
                current_tokens += para_tokens

            # Don't forget final chunk
            if current_chunk_text:
                chunk_content = "\n\n".join(current_chunk_text)
                chunks.append(ContentChunk(
                    content=chunk_content,
                    chunk_type=element_type,
                    page_start=page_start,
                    page_end=page_end,
                    heading_path=heading_path,
                    estimated_tokens=current_tokens,
                ))

        return chunks


class MultimediaAnalyzer:
    """Detects and describes multimedia elements in PDFs."""

    def __init__(self):
        """Initialize multimedia analyzer."""
        self.image_confidence_threshold = 0.7

    def detect_images(self, page_elements: List[Dict[str, Any]]) -> List[MultimediaElement]:
        """Detect images and charts in page.

        Args:
            page_elements: Elements on page

        Returns:
            List of detected multimedia elements
        """
        elements = []

        for elem in page_elements:
            if elem.get("type") == "image":
                elem_obj = MultimediaElement(
                    type="image",
                    page=elem.get("page", 0),
                    x=elem["bbox"][0],
                    y=elem["bbox"][1],
                    width=elem["bbox"][2] - elem["bbox"][0],
                    height=elem["bbox"][3] - elem["bbox"][1],
                    confidence=0.9,
                )
                elements.append(elem_obj)

            elif elem.get("type") == "chart":
                elem_obj = MultimediaElement(
                    type="chart",
                    page=elem.get("page", 0),
                    x=elem["bbox"][0],
                    y=elem["bbox"][1],
                    width=elem["bbox"][2] - elem["bbox"][0],
                    height=elem["bbox"][3] - elem["bbox"][1],
                    description=elem.get("chart_type"),
                    confidence=0.8,
                )
                elements.append(elem_obj)

        return elements

    def generate_alt_text(self, image: MultimediaElement) -> str:
        """Generate alternative text for image (for accessibility/indexing).

        Args:
            image: Multimedia element

        Returns:
            Alternative text description
        """
        if image.type == "chart":
            return f"{image.type.capitalize()} on page {image.page}: {image.description}"
        elif image.type == "diagram":
            return f"Diagram on page {image.page}"
        else:
            return f"{image.type.capitalize()} on page {image.page}"


class CitationTracker:
    """Tracks citations and content provenance."""

    def __init__(self):
        """Initialize citation tracker."""
        self.citations: Dict[str, List[SourceLocation]] = {}

    def add_citation(self, content: str, location: SourceLocation) -> None:
        """Register a citation.

        Args:
            content: Text content
            location: Source location in PDF
        """
        if content not in self.citations:
            self.citations[content] = []
        self.citations[content].append(location)

    def get_source(self, text: str) -> Optional[SourceLocation]:
        """Get source location for text.

        Args:
            text: Text to find

        Returns:
            Source location or None
        """
        for content, locations in self.citations.items():
            if text.lower() in content.lower():
                return locations[0]
        return None

    def verify_hallucination(self, claim: str, chunks: List[ContentChunk]) -> bool:
        """Check if claim is grounded in source content.

        Args:
            claim: Claim to verify
            chunks: Content chunks to search

        Returns:
            True if claim is grounded in content
        """
        claim_lower = claim.lower()
        for chunk in chunks:
            if claim_lower in chunk.content.lower():
                return True
        return False
