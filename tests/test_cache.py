"""Tests for PDF caching layer."""

import pytest
import tempfile
import time
from pathlib import Path
from pystreampdf.cache import PDFCache, CachedDocument
from pystreampdf.token_budget import TokenBudgetConfig, BudgetRule
from pystreampdf.extraction import ContentChunk, ElementType


# Import Path at module level for use in test_budget_reevaluation_on_warm_hit


@pytest.fixture
def sample_pdf_path():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"PDF test content" * 100)
        return f.name


@pytest.fixture
def sample_chunks():
    """Create sample content chunks."""
    return [
        ContentChunk(
            content="This is a test chunk",
            chunk_type=ElementType.TEXT,
            page_start=1,
            page_end=1,
            estimated_tokens=5,
        ),
        ContentChunk(
            content="Another test chunk",
            chunk_type=ElementType.TEXT,
            page_start=2,
            page_end=2,
            estimated_tokens=4,
        ),
    ]


class TestPDFCache:
    """Test PDFCache functionality."""

    def test_cache_miss_calls_process_fn(self, sample_pdf_path, sample_chunks):
        """Test that cache miss calls process function."""
        process_fn_calls = []

        def mock_process(path):
            process_fn_calls.append(path)
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PDFCache(disk_cache_dir=tmpdir)
            doc = cache.get_or_process(sample_pdf_path, mock_process)

            assert len(process_fn_calls) == 1
            assert process_fn_calls[0] == sample_pdf_path
            assert len(doc.chunks) == 2
            assert doc.title == "Test Title"
            assert cache.misses == 1
            assert cache.hits == 0

    def test_cache_hit_skips_process_fn(self, sample_pdf_path, sample_chunks):
        """Test that second call hits cache."""
        process_fn_calls = []

        def mock_process(path):
            process_fn_calls.append(path)
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PDFCache(disk_cache_dir=tmpdir)

            # First call: cache miss
            doc1 = cache.get_or_process(sample_pdf_path, mock_process)
            assert len(process_fn_calls) == 1

            # Second call: cache hit
            doc2 = cache.get_or_process(sample_pdf_path, mock_process)
            assert len(process_fn_calls) == 1  # Not called again

            assert doc1.file_hash == doc2.file_hash
            assert cache.hits == 1
            assert cache.misses == 1

    def test_l1_cache_lru_eviction(self, sample_pdf_path, sample_chunks):
        """Test that L1 cache respects memory limits."""
        process_calls = []

        def mock_process(path):
            process_calls.append(path)
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            # Small memory limit: ~10KB
            cache = PDFCache(memory_limit_mb=0.01, disk_cache_dir=tmpdir)

            # Add first document
            doc1 = cache.get_or_process(sample_pdf_path, mock_process)
            hash1 = doc1.file_hash
            initial_l1_size = len(cache.l1_cache)

            # Create additional large PDFs to trigger eviction
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(b"PDF content " * 1000)
                    pdf_path = f.name
                cache.get_or_process(pdf_path, mock_process)

            # L1 should not grow unbounded even with multiple entries
            # (some should be evicted to disk)
            assert len(cache.l1_cache) < 4
            # The first document should have been evicted to disk cache
            assert hash1 not in cache.l1_cache or len(cache.l1_cache) < initial_l1_size + 3

    def test_disk_cache_persistence(self, sample_pdf_path, sample_chunks):
        """Test that L2 disk cache persists between cache instances."""
        def mock_process(path):
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            # First cache instance
            cache1 = PDFCache(memory_limit_mb=500, disk_cache_dir=tmpdir)
            doc1 = cache1.get_or_process(sample_pdf_path, mock_process)
            file_hash = doc1.file_hash

            # Second cache instance with same disk directory
            process_fn_calls = []

            def mock_process_2(path):
                process_fn_calls.append(path)
                return sample_chunks, "preview text", "Test Title", 2

            cache2 = PDFCache(memory_limit_mb=500, disk_cache_dir=tmpdir)
            doc2 = cache2.get_or_process(sample_pdf_path, mock_process_2)

            # Process function should not be called (disk cache hit)
            assert len(process_fn_calls) == 0
            assert doc2.file_hash == file_hash
            assert cache2.hits == 1

    def test_invalidate_removes_cache_entry(self, sample_pdf_path, sample_chunks):
        """Test that invalidate() removes cache entries."""
        def mock_process(path):
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PDFCache(disk_cache_dir=tmpdir)

            # Add to cache
            doc1 = cache.get_or_process(sample_pdf_path, mock_process)
            file_hash = doc1.file_hash
            assert len(cache.l1_cache) == 1

            # Invalidate
            invalidated = cache.invalidate(sample_pdf_path)
            assert invalidated is True
            assert file_hash not in cache.l1_cache

            # L2 file should also be gone
            l2_path = cache.disk_cache_dir / f"{file_hash}.pkl"
            assert not l2_path.exists()

    def test_clear_wipes_all_cache(self, sample_pdf_path, sample_chunks):
        """Test that clear() wipes all cache entries."""
        def mock_process(path):
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PDFCache(disk_cache_dir=tmpdir)

            # Add multiple entries
            doc1 = cache.get_or_process(sample_pdf_path, mock_process)

            # Clear
            cache.clear()
            assert len(cache.l1_cache) == 0
            assert cache.hits == 0
            assert cache.misses == 0
            assert len(list(cache.disk_cache_dir.glob("*.pkl"))) == 0

    def test_stats_returns_metrics(self, sample_pdf_path, sample_chunks):
        """Test that stats() returns correct metrics."""
        def mock_process(path):
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PDFCache(disk_cache_dir=tmpdir)

            # No requests yet
            stats = cache.stats()
            assert stats["hits"] == 0
            assert stats["misses"] == 0
            assert stats["hit_rate"] == 0.0

            # Miss then hit
            cache.get_or_process(sample_pdf_path, mock_process)
            cache.get_or_process(sample_pdf_path, mock_process)

            stats = cache.stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 1
            assert stats["hit_rate"] == 0.5
            assert stats["l1_entries"] >= 1
            assert stats["memory_used_mb"] > 0
            assert stats["disk_used_mb"] > 0

    def test_budget_reevaluation_on_warm_hit(self, sample_pdf_path, sample_chunks):
        """Test that budget is re-evaluated on cache hit."""
        def mock_process(path):
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            # First config: "xyz_marker" files get 1.2x (sample_pdf_path won't match)
            config1 = TokenBudgetConfig(
                base_budget=800,
                rules=[BudgetRule("xyz_marker", 1.2, match_fields=["filename"])],
            )
            cache = PDFCache(disk_cache_dir=tmpdir, token_budget_config=config1)

            # Process a file (with first config - no match)
            doc1 = cache.get_or_process(sample_pdf_path, mock_process)
            assert doc1.evaluated_budget == 800

            # Update config to match the actual filename pattern
            filename = Path(sample_pdf_path).name
            keyword = filename.split('.')[0][:3]  # Match first 3 chars of filename

            config2 = TokenBudgetConfig(
                base_budget=800,
                rules=[BudgetRule(keyword, 1.1, match_fields=["filename"])],
            )
            cache.token_budget_config = config2

            # Hit same cache with new config - budget should be re-evaluated
            doc2 = cache.get_or_process(sample_pdf_path, mock_process)
            assert doc2.evaluated_budget == 880  # 800 * 1.1

    def test_ttl_expiry_reprocesses(self, sample_pdf_path, sample_chunks):
        """Test that expired cache entries are reprocessed."""
        process_fn_calls = []

        def mock_process(path):
            process_fn_calls.append(path)
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            # Very short TTL for testing
            cache = PDFCache(disk_cache_dir=tmpdir, ttl_seconds=1)

            # First call: cache miss
            doc1 = cache.get_or_process(sample_pdf_path, mock_process)
            assert len(process_fn_calls) == 1

            # Second call immediately: cache hit
            doc2 = cache.get_or_process(sample_pdf_path, mock_process)
            assert len(process_fn_calls) == 1

            # Wait for TTL to expire
            time.sleep(1.1)

            # Third call: cache expired, reprocess
            doc3 = cache.get_or_process(sample_pdf_path, mock_process)
            assert len(process_fn_calls) == 2

    def test_content_change_detected(self, sample_chunks):
        """Test that modified PDF content is detected."""
        def mock_process_v1(path):
            return sample_chunks, "preview text", "Title V1", 2

        def mock_process_v2(path):
            return sample_chunks, "preview text", "Title V2", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PDFCache(disk_cache_dir=tmpdir)

            # Create first version of PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"PDF version 1" * 100)
                pdf_path = f.name

            # Process first version
            doc1 = cache.get_or_process(pdf_path, mock_process_v1)
            assert doc1.title == "Title V1"
            hash1 = doc1.file_hash

            # Overwrite file with different content
            with open(pdf_path, "wb") as f:
                f.write(b"PDF version 2 with different content" * 100)

            # Process second version
            doc2 = cache.get_or_process(pdf_path, mock_process_v2)
            assert doc2.title == "Title V2"
            hash2 = doc2.file_hash

            # Hashes should be different
            assert hash1 != hash2

    def test_access_tracking(self, sample_pdf_path, sample_chunks):
        """Test that access_count and last_accessed are tracked."""
        def mock_process(path):
            return sample_chunks, "preview text", "Test Title", 2

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PDFCache(disk_cache_dir=tmpdir)

            doc1 = cache.get_or_process(sample_pdf_path, mock_process)
            initial_accessed = doc1.last_accessed
            initial_count = doc1.access_count
            assert initial_count == 1

            time.sleep(0.1)

            doc2 = cache.get_or_process(sample_pdf_path, mock_process)
            assert doc2.access_count == initial_count + 1
            assert doc2.last_accessed >= initial_accessed
