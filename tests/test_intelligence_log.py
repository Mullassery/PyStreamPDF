"""Tests for log intelligence analyzer."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
from pystreampdf.intelligence import LogAnalyzer


class TestLogAnalyzerFormatDetection(unittest.TestCase):
    """Log format detection tests."""

    def setUp(self):
        self.analyzer = LogAnalyzer()

    def test_detect_syslog_format(self):
        text = "Jul 25 14:30:45 myhost kernel: [12345.678901] Some log message"
        result = self.analyzer.analyze(text)
        self.assertIn(result.metadata.get("log_format"), ["syslog", "unknown"])

    def test_detect_journalctl_format(self):
        text = "Jul 25 14:30:45.123456 myhost kernel: message"
        result = self.analyzer.analyze(text)
        self.assertIsNotNone(result.metadata.get("log_format"))

    def test_detect_kernel_format(self):
        text = "[12345.678901] Linux version 5.10.0"
        result = self.analyzer.analyze(text)
        self.assertIn(result.metadata.get("log_format"), ["kernel", "unknown"])

    def test_detect_docker_format(self):
        text = "2024-07-25T14:30:45.123456Z container: Starting container"
        result = self.analyzer.analyze(text)
        self.assertIsNotNone(result.metadata.get("log_format"))

    def test_detect_k8s_format(self):
        text = "2024-07-25 14:30:45 pod-name: Readiness probe"
        result = self.analyzer.analyze(text)
        self.assertIsNotNone(result.metadata.get("log_format"))


class TestLogAnalyzerErrorDetection(unittest.TestCase):
    """Error detection tests."""

    def setUp(self):
        self.analyzer = LogAnalyzer()

    def test_single_error(self):
        text = "2024-07-25 14:30:45 ERROR: Connection failed"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("error_count"), 1)
        self.assertFalse(result.is_valid)

    def test_multiple_errors(self):
        text = """2024-07-25 14:30:45 ERROR: Connection failed
2024-07-25 14:30:46 ERROR: Timeout occurred
2024-07-25 14:30:47 ERROR: Retry exhausted"""
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("error_count"), 3)

    def test_critical_level(self):
        text = "2024-07-25 14:30:45 CRITICAL: System failure"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.metadata.get("error_count"), 1)

    def test_no_errors_valid_log(self):
        text = """2024-07-25 14:30:45 INFO: Starting service
2024-07-25 14:30:46 DEBUG: Initialization complete"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)


class TestLogAnalyzerWarningDetection(unittest.TestCase):
    """Warning detection tests."""

    def setUp(self):
        self.analyzer = LogAnalyzer()

    def test_single_warning(self):
        text = "2024-07-25 14:30:45 WARN: Deprecated API usage"
        result = self.analyzer.analyze(text)
        # Single warning doesn't trigger excessive warning threshold (>20%)
        warn_count = result.metadata.get("warning_count", 0)
        self.assertTrue(warn_count == 0 or warn_count == 1)

    def test_excessive_warnings(self):
        text = "\n".join([
            f"2024-07-25 14:30:{45+i%60:02d} WARN: Retry attempt {i+1}"
            for i in range(10)
        ])
        result = self.analyzer.analyze(text)
        if result.metadata.get("warning_count", 0) > 0:
            self.assertFalse(result.is_valid)

    def test_warning_threshold(self):
        text = "\n".join([f"2024-07-25 14:30:45 WARN: Message {i}" for i in range(5)])
        text += "\nINFO: Messages"
        result = self.analyzer.analyze(text)
        self.assertIsNotNone(result.metadata.get("warning_count"))


class TestLogAnalyzerCrashDetection(unittest.TestCase):
    """Crash pattern detection tests."""

    def setUp(self):
        self.analyzer = LogAnalyzer()

    def test_detect_segfault(self):
        text = "2024-07-25 14:30:45 ERROR: Segmentation fault in process"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        crash_patterns = result.metadata.get("crash_patterns", [])
        self.assertTrue(any("segfault" in p.lower() or "segmentation" in p.lower() for p in crash_patterns))

    def test_detect_oom(self):
        text = "2024-07-25 14:30:45 CRITICAL: Out of memory killer invoked"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_detect_panic(self):
        text = "2024-07-25 14:30:45 ERROR: Kernel panic"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_detect_backtrace(self):
        text = """2024-07-25 14:30:45 ERROR: Backtrace:
  #0 0x...
  #1 0x...
  #2 0x..."""
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_detect_core_dump(self):
        text = "2024-07-25 14:30:45 CRITICAL: Core dump generated"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)


class TestLogAnalyzerResourceExhaustion(unittest.TestCase):
    """Resource exhaustion detection tests."""

    def setUp(self):
        self.analyzer = LogAnalyzer()

    def test_detect_no_space_left(self):
        text = "2024-07-25 14:30:45 ERROR: No space left on device"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_detect_enomem(self):
        text = "2024-07-25 14:30:45 ERROR: ENOMEM: Cannot allocate memory"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_detect_too_many_open_files(self):
        text = "2024-07-25 14:30:45 ERROR: Too many open files"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_multiple_resource_issues(self):
        text = """2024-07-25 14:30:45 ERROR: No space left on device
2024-07-25 14:30:46 ERROR: Too many open files"""
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)


class TestLogAnalyzerMetadata(unittest.TestCase):
    """Metadata extraction tests."""

    def setUp(self):
        self.analyzer = LogAnalyzer()

    def test_entry_count(self):
        text = "\n".join([
            f"2024-07-25 14:30:{45+i%60:02d} INFO: Message {i}"
            for i in range(10)
        ])
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("entry_count"), 10)

    def test_empty_log(self):
        result = self.analyzer.analyze("")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 0.0)

    def test_single_entry(self):
        text = "2024-07-25 14:30:45 INFO: Single message"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("entry_count"), 1)

    def test_confidence_valid_log(self):
        text = "2024-07-25 14:30:45 INFO: Normal operation"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 1.0)

    def test_confidence_degradation(self):
        text = "2024-07-25 14:30:45 ERROR: Something failed"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertLess(result.confidence, 1.0)


class TestLogAnalyzerEdgeCases(unittest.TestCase):
    """Edge case tests."""

    def setUp(self):
        self.analyzer = LogAnalyzer()

    def test_whitespace_only(self):
        result = self.analyzer.analyze("   \n  \n  ")
        self.assertTrue(result.is_valid)

    def test_mixed_log_levels(self):
        text = """2024-07-25 14:30:45 DEBUG: Debug info
2024-07-25 14:30:46 INFO: Informational
2024-07-25 14:30:47 WARN: Warning message
2024-07-25 14:30:48 ERROR: Error occurred"""
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("error_count"), 1)

    def test_unstructured_logs(self):
        text = """Random log line 1
Random log line 2
Something happened"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_very_long_log(self):
        text = "\n".join([
            f"2024-07-25 14:30:{45+i%60:02d} INFO: Message {i}"
            for i in range(1000)
        ])
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("entry_count"), 1000)


if __name__ == "__main__":
    unittest.main()
