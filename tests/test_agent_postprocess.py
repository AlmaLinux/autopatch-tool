"""Backward-compat tests for post-processing (now in agent_orchestrator).

Full coverage is in tests/test_agent_orchestrator.py.
"""

import json
from pathlib import Path

from freezegun import freeze_time

from src.agent_orchestrator import _write_log


class TestPostprocessWritesJsonl:

    @freeze_time("2026-03-25T14:05:00+00:00")
    def test_writes_jsonl(self, tmp_path):
        log_path = str(tmp_path / "logs" / "agent_runs.jsonl")

        _write_log(
            log_path, "httpd", "c9",
            {"success": True, "summary": "Fixed replace action"},
            {"error_type": "ActionNotAppliedError"},
            "agent-fix/c9-20260325-140000",
            False,
            "2026-03-25T14:00:00+00:00",
        )

        entry = json.loads(Path(log_path).read_text().strip())
        assert entry["package"] == "httpd"
        assert entry["success"] is True
        assert entry["branch_name"] == "agent-fix/c9-20260325-140000"
        assert entry["duration_sec"] == 300
