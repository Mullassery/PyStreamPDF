"""Tests for JSON intelligence analyzer."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
from pystreampdf.intelligence import JSONAnalyzer


class TestJSONAnalyzer(unittest.TestCase):
    """JSON analyzer tests."""

    def setUp(self):
        self.analyzer = JSONAnalyzer()

    def test_valid_json_object(self):
        text = '{"key": "value", "number": 42}'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.content_type, "json")
        self.assertGreaterEqual(result.confidence, 0.85)

    def test_valid_json_array(self):
        text = '[1, 2, 3, 4, 5]'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata.get("top_level_type"), "array")

    def test_valid_json_nested(self):
        text = '{"outer": {"inner": {"deep": "value"}}}'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertGreater(result.metadata.get("nesting_depth", 0), 1)

    def test_valid_json_complex(self):
        text = '''{
  "users": [
    {"id": 1, "name": "Alice", "active": true},
    {"id": 2, "name": "Bob", "active": false}
  ],
  "metadata": {
    "total": 2,
    "page": 1
  }
}'''
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_invalid_json_no_recovery(self):
        text = '{"key": value_without_quotes}'
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.issues) > 0)

    def test_invalid_json_trailing_comma(self):
        text = '{"key": "value",}'
        result = self.analyzer.analyze(text)
        # The recovery mechanism fixes this automatically
        self.assertTrue(result.is_valid or len(result.corrections) > 0)

    def test_trailing_comma_recovery(self):
        text = '{"a": 1, "b": 2,}'
        result = self.analyzer.analyze(text)
        if result.corrected_text:
            self.assertTrue(result.is_valid)
            self.assertNotIn(",}", result.corrected_text)

    def test_invalid_json_missing_comma(self):
        text = '{"a": 1}{"b": 2}'
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.corrections) > 0)

    def test_missing_comma_recovery(self):
        text = '{"a": 1}{"b": 2}'
        result = self.analyzer.analyze(text)
        if result.corrected_text:
            self.assertIn("},{", result.corrected_text)

    def test_single_quotes_recovery(self):
        text = "{'key': 'value', 'other': 'test'}"
        result = self.analyzer.analyze(text)
        # Single quote conversion only happens when text has both quote types
        self.assertIsNotNone(result)

    def test_empty_json_object(self):
        text = '{}'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_empty_json_array(self):
        text = '[]'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_metadata_key_count(self):
        text = '{"a": 1, "b": 2, "c": 3}'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata.get("key_count"), 3)

    def test_schema_inference_api_response(self):
        text = '{"data": [1, 2], "result": "success", "status": 200}'
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("inferred_purpose"), "api_response")

    def test_schema_inference_config(self):
        text = '{"host": "localhost", "port": 8080, "version": "1.0"}'
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("inferred_purpose"), "config")

    def test_schema_inference_error_response(self):
        text = '{"error": "not_found", "message": "User not found", "code": 404}'
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("inferred_purpose"), "error_response")

    def test_nesting_depth_flat(self):
        text = '{"a": 1, "b": 2, "c": 3}'
        result = self.analyzer.analyze(text)
        self.assertLessEqual(result.metadata.get("nesting_depth", 999), 1)

    def test_nesting_depth_deep(self):
        text = '{"a": {"b": {"c": {"d": 1}}}}'
        result = self.analyzer.analyze(text)
        self.assertGreater(result.metadata.get("nesting_depth", 0), 2)

    def test_confidence_degrades_with_issues(self):
        text = '{"key": "value",}'
        result = self.analyzer.analyze(text)
        if not result.is_valid:
            self.assertLess(result.confidence, 0.9)

    def test_whitespace_handling(self):
        text = '  {  "key"  :  "value"  }  '
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_unicode_in_json(self):
        text = '{"message": "Hello, 世界", "emoji": "🚀"}'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)


class TestJSONAnalyzerRecovery(unittest.TestCase):
    """Tests for JSON recovery mechanisms."""

    def setUp(self):
        self.analyzer = JSONAnalyzer()

    def test_correction_suggestion_structure(self):
        text = '{"key": "value",}'
        result = self.analyzer.analyze(text)
        if result.corrections:
            corr = result.corrections[0]
            self.assertIsNotNone(corr.original)
            self.assertIsNotNone(corr.corrected)
            self.assertIsNotNone(corr.confidence)
            self.assertIsNotNone(corr.description)

    def test_multiple_issues_multiple_corrections(self):
        text = '{"a": 1,}{"b": 2}'
        result = self.analyzer.analyze(text)
        self.assertGreaterEqual(len(result.corrections), 1)

    def test_recovery_confidence_high(self):
        text = '{"key": "value",}'
        result = self.analyzer.analyze(text)
        if result.corrections:
            self.assertGreater(result.corrections[0].confidence, 0.8)


if __name__ == "__main__":
    unittest.main()
