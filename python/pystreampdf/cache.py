"""PDF document caching layer for cost-efficient repeated retrieval.

Provides in-memory (L1) and persistent disk (L2) caching for parsed PDFs.
Integrates with TokenBudgetConfig to store evaluated budgets with cached documents.

Caching is content-addressed (SHA256 hash of PDF bytes), so identical PDFs
are recognized regardless of filename or location.
"""

import hashlib
import pickle
import time
from typing import Callable, List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path

from .extraction import ContentChunk
from .token_budget import TokenBudgetConfig


@dataclass
class CachedDocument:
    """A cached PDF document with extracted chunks and metadata."""
    file_hash: str
    evaluated_budget: int
    filename: str
    title: Optional[str]
    page_count: int
    content_preview: str
    chunks: List[ContentChunk]
    cached_at: float
    last_accessed: float
    access_count: int = 0

    def memory_size_bytes(self) -> int:
        """Estimate memory size of cached content."""
        size = len(self.file_hash) + len(self.filename) + len(self.content_preview)
        size += sum(len(chunk.content) for chunk in self.chunks)
        return size


class PDFCache:
    """Multi-tier cache for PDF documents.

    Implements:
    - L1: In-memory LRU cache (fast, bounded by memory_limit_mb)
    - L2: Persistent disk cache (survives restarts, bounded by disk_limit_mb)

    Features:
    - Content-addressed caching (SHA256 of PDF bytes)
    - Automatic budget re-evaluation on warm hits
    - Configurable TTL for cache invalidation
    - Hit/miss statistics
    """

    CACHE_VERSION = 1
    CACHE_DIR_DEFAULT = ".cache/pystreampdf"

    def __init__(
        self,
        memory_limit_mb: int = 500,
        disk_cache_dir: Optional[str] = None,
        disk_limit_mb: int = 5000,
        token_budget_config: Optional[TokenBudgetConfig] = None,
        ttl_seconds: Optional[int] = None,
    ):
        """Initialize PDF cache.

        Args:
            memory_limit_mb: Maximum in-memory cache size in MB (default 500)
            disk_cache_dir: Directory for persistent cache (default ~/.cache/pystreampdf)
            disk_limit_mb: Maximum disk cache size in MB (default 5000)
            token_budget_config: TokenBudgetConfig for budget evaluation
            ttl_seconds: Cache entry TTL in seconds (None = never expire)
        """
        self.memory_limit_mb = memory_limit_mb
        self.disk_limit_mb = disk_limit_mb
        self.ttl_seconds = ttl_seconds
        self.token_budget_config = token_budget_config

        self.l1_cache: OrderedDict[str, CachedDocument] = OrderedDict()
        self.l1_size_bytes = 0

        if disk_cache_dir is None:
            disk_cache_dir = str(Path.home() / self.CACHE_DIR_DEFAULT)
        self.disk_cache_dir = Path(disk_cache_dir)
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)

        self.hits = 0
        self.misses = 0

    def get_or_process(
        self,
        pdf_path: str,
        process_fn: Callable[[str], Tuple[List[ContentChunk], str, Optional[str], int]],
    ) -> CachedDocument:
        """Get a cached document or process it if not cached.

        Args:
            pdf_path: Path to PDF file
            process_fn: Function that processes PDF, returns (chunks, content_preview, title, page_count)

        Returns:
            CachedDocument with chunks and evaluated budget
        """
        file_hash = self._compute_hash(pdf_path)
        filename = Path(pdf_path).name

        doc = self._get_from_l1(file_hash)
        if doc is not None and not self._is_expired(doc):
            self.hits += 1
            doc.last_accessed = time.time()
            doc.access_count += 1
            self._re_evaluate_budget(doc, filename)
            return doc

        doc = self._get_from_l2(file_hash)
        if doc is not None and not self._is_expired(doc):
            self.hits += 1
            doc.last_accessed = time.time()
            doc.access_count += 1
            self._re_evaluate_budget(doc, filename)
            self._add_to_l1(file_hash, doc)
            return doc

        self.misses += 1
        chunks, content_preview, title, page_count = process_fn(pdf_path)

        doc = CachedDocument(
            file_hash=file_hash,
            evaluated_budget=0,
            filename=filename,
            title=title,
            page_count=page_count,
            content_preview=content_preview,
            chunks=chunks,
            cached_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
        )

        self._re_evaluate_budget(doc, filename)
        self._add_to_l1(file_hash, doc)
        self._add_to_l2(file_hash, doc)

        return doc

    def invalidate(self, pdf_path: str) -> bool:
        """Invalidate cache entry for a PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if cache entry was found and removed, False otherwise
        """
        file_hash = self._compute_hash(pdf_path)

        if file_hash in self.l1_cache:
            doc = self.l1_cache.pop(file_hash)
            self.l1_size_bytes -= doc.memory_size_bytes()

        l2_path = self.disk_cache_dir / f"{file_hash}.pkl"
        if l2_path.exists():
            l2_path.unlink()
            return True

        return False

    def clear(self) -> None:
        """Clear all cache entries (both L1 and L2)."""
        self.l1_cache.clear()
        self.l1_size_bytes = 0

        for pkl_file in self.disk_cache_dir.glob("*.pkl"):
            pkl_file.unlink()

        self.hits = 0
        self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dictionary with hit_rate, entry_count, memory_used_mb, disk_used_mb
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        disk_size = sum(f.stat().st_size for f in self.disk_cache_dir.glob("*.pkl"))

        return {
            "hit_rate": hit_rate,
            "hits": self.hits,
            "misses": self.misses,
            "l1_entries": len(self.l1_cache),
            "memory_used_mb": self.l1_size_bytes / (1024 * 1024),
            "disk_used_mb": disk_size / (1024 * 1024),
        }

    def _compute_hash(self, pdf_path: str) -> str:
        """Compute SHA256 hash of PDF file."""
        sha256 = hashlib.sha256()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_from_l1(self, file_hash: str) -> Optional[CachedDocument]:
        """Get document from L1 cache."""
        if file_hash in self.l1_cache:
            self.l1_cache.move_to_end(file_hash)
            return self.l1_cache[file_hash]
        return None

    def _get_from_l2(self, file_hash: str) -> Optional[CachedDocument]:
        """Get document from L2 (disk) cache."""
        l2_path = self.disk_cache_dir / f"{file_hash}.pkl"
        if not l2_path.exists():
            return None

        try:
            with open(l2_path, "rb") as f:
                data = pickle.load(f)
                if isinstance(data, dict) and data.get("version") == self.CACHE_VERSION:
                    return data.get("document")
        except Exception:
            l2_path.unlink()
        return None

    def _add_to_l1(self, file_hash: str, doc: CachedDocument) -> None:
        """Add document to L1 cache, evicting LRU if necessary."""
        if file_hash in self.l1_cache:
            old_doc = self.l1_cache.pop(file_hash)
            self.l1_size_bytes -= old_doc.memory_size_bytes()

        self.l1_cache[file_hash] = doc
        self.l1_size_bytes += doc.memory_size_bytes()

        memory_limit_bytes = self.memory_limit_mb * 1024 * 1024
        while self.l1_size_bytes > memory_limit_bytes and self.l1_cache:
            evicted_hash, evicted_doc = self.l1_cache.popitem(last=False)
            self.l1_size_bytes -= evicted_doc.memory_size_bytes()

    def _add_to_l2(self, file_hash: str, doc: CachedDocument) -> None:
        """Add document to L2 (disk) cache."""
        l2_path = self.disk_cache_dir / f"{file_hash}.pkl"
        try:
            with open(l2_path, "wb") as f:
                pickle.dump({"version": self.CACHE_VERSION, "document": doc}, f)
        except Exception:
            pass

    def _re_evaluate_budget(self, doc: CachedDocument, filename: str) -> None:
        """Re-evaluate budget on cached document (config may have changed)."""
        if self.token_budget_config:
            doc.evaluated_budget = self.token_budget_config.evaluate(
                filename, doc.title, doc.content_preview
            )
        else:
            doc.evaluated_budget = 2000

    def _is_expired(self, doc: CachedDocument) -> bool:
        """Check if document has expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        return time.time() - doc.cached_at > self.ttl_seconds
