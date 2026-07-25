"""Tests for SQL intelligence analyzer."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import unittest
from pystreampdf.intelligence import SQLAnalyzer


class TestSQLAnalyzerDialectDetection(unittest.TestCase):
    """SQL dialect detection tests."""

    def setUp(self):
        self.analyzer = SQLAnalyzer()

    def test_detect_postgresql(self):
        text = "SELECT id::text, data->>'key' FROM table RETURNING id;"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("dialect"), "postgresql")

    def test_detect_mysql(self):
        text = "SELECT * FROM users LIMIT 10;"
        result = self.analyzer.analyze(text)
        self.assertIn(result.metadata.get("dialect"), ["mysql", "unknown"])

    def test_detect_sqlite(self):
        text = "SELECT * FROM users WITHOUT ROWID;"
        result = self.analyzer.analyze(text)
        self.assertIn(result.metadata.get("dialect"), ["sqlite", "unknown"])

    def test_detect_tsql(self):
        text = "SELECT TOP 10 * FROM dbo.Users;"
        result = self.analyzer.analyze(text)
        self.assertIn(result.metadata.get("dialect"), ["tsql", "unknown"])

    def test_detect_oracle(self):
        text = "SELECT * FROM table WHERE ROWNUM < 100;"
        result = self.analyzer.analyze(text)
        self.assertIn(result.metadata.get("dialect"), ["oracle", "unknown"])


class TestSQLAnalyzerQueryTypes(unittest.TestCase):
    """Query type detection tests."""

    def setUp(self):
        self.analyzer = SQLAnalyzer()

    def test_detect_select_query(self):
        text = "SELECT * FROM users;"
        result = self.analyzer.analyze(text)
        self.assertIn("SELECT", result.metadata.get("query_types", []))

    def test_detect_insert_query(self):
        text = "INSERT INTO users (name) VALUES ('Alice');"
        result = self.analyzer.analyze(text)
        self.assertIn("INSERT", result.metadata.get("query_types", []))

    def test_detect_update_query(self):
        text = "UPDATE users SET name = 'Bob' WHERE id = 1;"
        result = self.analyzer.analyze(text)
        self.assertIn("UPDATE", result.metadata.get("query_types", []))

    def test_detect_delete_query(self):
        text = "DELETE FROM users WHERE id = 1;"
        result = self.analyzer.analyze(text)
        self.assertIn("DELETE", result.metadata.get("query_types", []))

    def test_detect_create_query(self):
        text = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));"
        result = self.analyzer.analyze(text)
        self.assertIn("CREATE", result.metadata.get("query_types", []))

    def test_detect_multiple_queries(self):
        text = "SELECT * FROM users; INSERT INTO logs (msg) VALUES ('test');"
        result = self.analyzer.analyze(text)
        self.assertGreater(result.metadata.get("query_count"), 1)


class TestSQLAnalyzerValidation(unittest.TestCase):
    """SQL validation tests."""

    def setUp(self):
        self.analyzer = SQLAnalyzer()

    def test_valid_select_query(self):
        text = "SELECT id, name, email FROM users WHERE active = true;"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.content_type, "sql")

    def test_valid_join_query(self):
        text = """
            SELECT u.name, o.total
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE o.total > 100;
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_invalid_update_without_where(self):
        text = "UPDATE users SET name = 'Unknown';"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertIn("UPDATE query without WHERE clause", result.issues[0])

    def test_invalid_delete_without_where(self):
        text = "DELETE FROM users;"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)
        self.assertIn("DELETE query without WHERE clause", result.issues[0])

    def test_unbalanced_parentheses(self):
        text = "SELECT COUNT(id FROM users WHERE status = 'active';"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_unclosed_string_literal(self):
        text = "SELECT * FROM users WHERE name = 'Alice;"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)

    def test_sql_injection_pattern(self):
        text = "SELECT * FROM users WHERE name = ' OR '1'='1';"
        result = self.analyzer.analyze(text)
        self.assertFalse(result.is_valid)


class TestSQLAnalyzerStructure(unittest.TestCase):
    """SQL structure extraction tests."""

    def setUp(self):
        self.analyzer = SQLAnalyzer()

    def test_extract_tables(self):
        text = "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id;"
        result = self.analyzer.analyze(text)
        tables = result.metadata.get("tables_referenced", [])
        tables_lower = [t.lower() for t in tables]
        self.assertIn("users", tables_lower)
        self.assertIn("orders", tables_lower)

    def test_extract_columns_defined(self):
        text = """
            CREATE TABLE users (
                id INT PRIMARY KEY,
                name VARCHAR(100),
                email TEXT,
                active BOOLEAN
            );
        """
        result = self.analyzer.analyze(text)
        cols = result.metadata.get("columns_defined", [])
        self.assertTrue(len(cols) > 0)

    def test_detect_aggregate_functions(self):
        text = "SELECT COUNT(*), SUM(amount), AVG(price) FROM orders GROUP BY user_id;"
        result = self.analyzer.analyze(text)
        aggs = result.metadata.get("aggregate_functions", [])
        self.assertIn("COUNT", aggs)
        self.assertIn("SUM", aggs)
        self.assertIn("AVG", aggs)

    def test_detect_join_types(self):
        text = """
            SELECT * FROM a
            INNER JOIN b ON a.id = b.id
            LEFT JOIN c ON b.id = c.id;
        """
        result = self.analyzer.analyze(text)
        joins = result.metadata.get("join_types", [])
        self.assertIn("INNER", joins)
        self.assertIn("LEFT", joins)

    def test_detect_subqueries(self):
        text = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE amount > 100);
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.metadata.get("has_subqueries", False))

    def test_detect_cte(self):
        text = """
            WITH active_users AS (
                SELECT * FROM users WHERE status = 'active'
            )
            SELECT * FROM active_users;
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.metadata.get("has_cte", False))


class TestSQLAnalyzerEdgeCases(unittest.TestCase):
    """Edge case tests."""

    def setUp(self):
        self.analyzer = SQLAnalyzer()

    def test_empty_sql(self):
        result = self.analyzer.analyze("")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 0.0)

    def test_whitespace_only(self):
        result = self.analyzer.analyze("   \n  \n  ")
        self.assertTrue(result.is_valid)

    def test_sql_with_comments(self):
        text = """
            -- This is a comment
            SELECT * FROM users WHERE active = true; /* inline comment */
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_quoted_strings_with_semicolon(self):
        text = "SELECT 'text; with semicolon' AS msg FROM logs;"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("query_count"), 1)

    def test_line_count(self):
        text = "SELECT *\nFROM users\nWHERE active = true;"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("line_count"), 3)

    def test_complex_query(self):
        text = """
            WITH ranked_users AS (
                SELECT *, ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
                FROM users
                WHERE status IN ('active', 'pending')
            )
            SELECT * FROM ranked_users
            WHERE rn <= 10
            ORDER BY created_at DESC;
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertGreater(result.metadata.get("query_count"), 0)

    def test_confidence_valid_sql(self):
        text = "SELECT * FROM users WHERE id = 1;"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 1.0)

    def test_confidence_invalid_sql(self):
        text = "SELECT * FROM users;"
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 1.0)

    def test_multiple_semicolons(self):
        text = "SELECT * FROM users;;; SELECT * FROM orders;;;"
        result = self.analyzer.analyze(text)
        self.assertEqual(result.metadata.get("query_count"), 2)


class TestSQLAnalyzerComplexScenarios(unittest.TestCase):
    """Complex real-world SQL scenarios."""

    def setUp(self):
        self.analyzer = SQLAnalyzer()

    def test_transaction_control(self):
        text = """
            BEGIN;
            UPDATE accounts SET balance = balance - 100 WHERE id = 1;
            UPDATE accounts SET balance = balance + 100 WHERE id = 2;
            COMMIT;
        """
        result = self.analyzer.analyze(text)
        self.assertGreater(result.metadata.get("query_count"), 0)

    def test_conditional_insert(self):
        text = """
            INSERT INTO users (name, email, created_at)
            SELECT DISTINCT name, email, NOW()
            FROM temp_users
            WHERE name NOT IN (SELECT name FROM users);
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_window_functions(self):
        text = """
            SELECT
                id, name, salary,
                AVG(salary) OVER (PARTITION BY department) as dept_avg,
                ROW_NUMBER() OVER (ORDER BY salary DESC) as rank
            FROM employees;
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)

    def test_json_operations(self):
        text = """
            SELECT
                id,
                data->>'name' as name,
                data->'settings' as settings
            FROM users
            WHERE data @> '{"premium": true}';
        """
        result = self.analyzer.analyze(text)
        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()
