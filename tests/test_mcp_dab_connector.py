"""Integration test for the real MCP/DAB subprocess path.

Uses a fake ``dab`` executable on PATH so the connector's actual
``subprocess.Popen(["dab", "start", "--config", ...])`` wiring is exercised
without requiring the real DAB binary.
"""

from __future__ import annotations

import json
import os
import stat
import time

import pytest

from pystreampdf._mcp_connector import PDFProcessor, _MCPPDFConnector

pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="fake dab executable uses a POSIX shebang"
)

FAKE_DAB = """#!/usr/bin/env python3
import json
import os
import shutil
import sys
import time

args = sys.argv[1:]
if args[:1] != ["start"] or "--config" not in args:
    print("unexpected args: " + repr(args), file=sys.stderr)
    raise SystemExit(2)
config_path = args[args.index("--config") + 1]
with open(config_path) as handle:
    config = json.load(handle)
capture = os.environ["FAKE_DAB_CAPTURE"]
with open(capture, "w") as handle:
    json.dump(config, handle)
while True:
    time.sleep(1)
"""


def test_start_stop_connector_spawns_dab_with_real_config(tmp_path, monkeypatch):
    fake_dab = tmp_path / "dab"
    fake_dab.write_text(FAKE_DAB)
    fake_dab.chmod(fake_dab.stat().st_mode | stat.S_IXUSR)
    capture = tmp_path / "captured-config.json"
    monkeypatch.setenv("FAKE_DAB_CAPTURE", str(capture))
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")

    connector = _MCPPDFConnector(PDFProcessor(), port=8799)
    try:
        url = connector.start_mcp_connector()
        assert url == "http://localhost:8799/mcp"
        assert connector.is_ready()
        assert connector.dab_process is not None
        assert connector.dab_process.poll() is None

        deadline = time.monotonic() + 5
        while not capture.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert capture.exists(), "fake dab did not write its config copy"
        config = json.loads(capture.read_text())
        assert config["runtime"]["host"] == "127.0.0.1"
        assert config["runtime"]["port"] == 8799
        assert config["mcp"]["path"] == "/mcp"
        assert config["entities"]
        for entity in config["entities"].values():
            assert entity["permissions"] == [{"actions": ["read"], "roles": ["local"]}]
    finally:
        connector.stop_mcp_connector()

    assert connector.dab_process is None or connector.dab_process.poll() is not None
    assert not connector.is_ready()
