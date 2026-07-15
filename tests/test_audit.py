import pytest
import pystreampdf
import os
import json
import tempfile


def test_audit_log_creation():
    """Test creating an audit log"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "audit_test.jsonl")

        audit = streampdf._core.PyAuditLog.new(log_path)
        assert audit is not None


def test_record_open(simple_pdf):
    """Test recording an open event"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "audit_test.jsonl")

        audit = streampdf._core.PyAuditLog.new(log_path)
        audit.record_open(simple_pdf)

        # Check file exists and has content
        assert os.path.exists(log_path)
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) > 0
            event = json.loads(lines[0])
            assert event["doc_path"] == simple_pdf
            assert event["kind"] == "DocumentOpened"


def test_record_search(simple_pdf):
    """Test recording a search event"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "audit_test.jsonl")

        audit = streampdf._core.PyAuditLog.new(log_path)
        audit.record_search(simple_pdf, "test query", 5)

        # Check file exists and has content
        assert os.path.exists(log_path)
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) > 0
            event = json.loads(lines[0])
            # Enum is serialized as {variant_name: {...details...}}
            assert "SearchPerformed" in event["kind"]
            kind_data = event["kind"]["SearchPerformed"]
            assert kind_data["query"] == "test query"
            assert kind_data["results_count"] == 5


def test_events_readable(simple_pdf):
    """Test reading events from audit log"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "audit_test.jsonl")

        audit = streampdf._core.PyAuditLog.new(log_path)
        audit.record_open(simple_pdf)
        audit.record_search(simple_pdf, "test", 3)

        events = audit.events()
        assert isinstance(events, list)
        assert len(events) == 2
        assert events[0]["kind"] == "DocumentOpened"
        assert events[1]["kind"] == "SearchPerformed"


def test_in_memory_audit():
    """Test in-memory audit log"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "inmem_audit_test.jsonl")

        audit = streampdf._core.PyAuditLog.new(log_path)
        audit.record_open("/path/to/doc.pdf")

        events = audit.events()
        assert len(events) >= 1
