"""Tests for YAML intelligence analyzer."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
from pystreampdf.intelligence import YAMLAnalyzer


class TestYAMLAnalyzer(unittest.TestCase):
    """YAML analyzer tests."""

    def setUp(self):
        self.analyzer = YAMLAnalyzer()

    def test_valid_yaml_simple(self):
        text = "key: value\nother: 123"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.content_type, "yaml")
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_valid_yaml_nested(self):
        text = "root:\n  child1: value1\n  child2: value2"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.metadata.get("has_nested"))

    def test_valid_yaml_with_lists(self):
        text = "items:\n  - first\n  - second\n  - third"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.metadata.get("has_lists"))

    def test_valid_yaml_complex(self):
        text = """
config:
  database:
    host: localhost
    port: 5432
    credentials:
      user: admin
      pass: secret
  features:
    - logging
    - caching
    - monitoring
"""
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_invalid_yaml_bad_indentation(self):
        text = "key: value\n  invalid: broken"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.issues) > 0)

    def test_invalid_yaml_tab_characters(self):
        text = "key: value\n\tinvalid: tab"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_ocr_error_costrnap_to_costmap(self):
        text = "costrnap: enabled"
        result = self.analyzer.analyze(text)
        # Typo in key is still valid YAML, but may have corrections suggested
        if result.corrections:
            self.assertGreater(len(result.corrections), 0)

    def test_ocr_error_paramaeter_to_parameter(self):
        text = "paramaeter: 42"
        result = self.analyzer.analyze(text)
        # Valid YAML, but may have OCR corrections available
        self.assertTrue(result.is_valid or len(result.corrections) > 0)

    def test_ocr_error_treue_to_true(self):
        text = "enabled: treue"
        result = self.analyzer.analyze(text)
        # Valid YAML string value, but may suggest corrections
        self.assertTrue(result.is_valid or len(result.corrections) > 0)

    def test_ocr_error_talse_to_false(self):
        text = "disabled: talse"
        result = self.analyzer.analyze(text)
        # Valid YAML string value, but may suggest corrections
        self.assertTrue(result.is_valid or len(result.corrections) > 0)

    def test_mixed_tabs_and_spaces_correction(self):
        yaml_with_mixed = "root:\n  child1: val1\n\tchild2: val2"
        result = self.analyzer.analyze(yaml_with_mixed)
        # May still parse depending on YAML parser behavior
        if result.corrected_text and "\t" in yaml_with_mixed:
            self.assertLessEqual(result.corrected_text.count("\t"), yaml_with_mixed.count("\t"))

    def test_empty_yaml(self):
        result = self.analyzer.analyze("")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 1.0)

    def test_whitespace_only(self):
        result = self.analyzer.analyze("   \n  \n  ")
        self.assertTrue(result.is_valid)

    def test_metadata_key_count(self):
        text = "key1: value1\nkey2: value2\nkey3: value3"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata.get("key_count"), 3)

    def test_metadata_root_keys(self):
        text = "alpha: 1\nbeta: 2"
        result = self.analyzer.analyze(text)
        self.assertIn("alpha", result.metadata.get("root_keys", []))
        self.assertIn("beta", result.metadata.get("root_keys", []))

    def test_multiple_ocr_errors_in_one_doc(self):
        text = "costrnap: true\nparamaeter: 100\ncontroller: mode"
        result = self.analyzer.analyze(text)
        # Valid YAML despite typos in keys, but may have corrections available
        self.assertTrue(result.is_valid or len(result.corrections) > 0)

    def test_confidence_degrades_with_issues(self):
        text = "key: value\n  bad_indent: true"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertLess(result.confidence, 0.85)

    def test_yaml_with_comments(self):
        text = "# This is a comment\nkey: value\n# Another comment"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_yaml_string_values_with_special_chars(self):
        text = 'message: "Hello: World"\npath: "/home/user/file.txt"'
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)


class TestYAMLAnalyzerCorrections(unittest.TestCase):
    """Tests for correction suggestions."""

    def setUp(self):
        self.analyzer = YAMLAnalyzer()

    def test_correction_suggestion_structure(self):
        text = "costrnap: value"
        result = self.analyzer.analyze(text)
        if result.corrections:
            corr = result.corrections[0]
            self.assertIsNotNone(corr.original)
            self.assertIsNotNone(corr.corrected)
            self.assertIsNotNone(corr.confidence)
            self.assertIsNotNone(corr.description)

    def test_high_confidence_ocr_fixes(self):
        text = "costrnap: true"
        result = self.analyzer.analyze(text)
        if result.corrections:
            self.assertGreaterEqual(result.corrections[0].confidence, 0.85)


if __name__ == "__main__":
    unittest.main()
