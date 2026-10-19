"""Regression: a missing Rust core must fail loudly and actionably."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_missing_core_raises_actionable_import_error() -> None:
    repo = Path(__file__).resolve().parents[1]
    code = r'''
import sys
sys.modules["pystreampdf._core"] = None
import pystreampdf

assert pystreampdf.HAS_RUST_CORE is False
for fn in (pystreampdf.open, pystreampdf.load_index):
    try:
        fn("x")
    except ImportError as exc:
        assert "maturin" in str(exc), exc
    else:
        raise AssertionError("expected ImportError, not a silent None")
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo / "python")
    subprocess.run([sys.executable, "-c", code], check=True, env=env, cwd=repo)
