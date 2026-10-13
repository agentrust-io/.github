"""Contract tests for contributor assessment process exit codes."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "vendor" / "agt" / "contributor_check_action.py"
spec = importlib.util.spec_from_file_location("contributor_check_action_under_test", MODULE)
action = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action)


class RiskExitContractTests(unittest.TestCase):
    def run_case(self, code, value, expected=None):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.CompletedProcess(["python"], code, json.dumps(value), "")
            with patch.object(action.subprocess, "run", return_value=result):
                if expected is None:
                    with self.assertRaises(action.CheckExecutionError):
                        action._run_check("dummy.py", [], str(Path(directory) / "out"))
                else:
                    self.assertEqual(
                        action._run_check("dummy.py", [], str(Path(directory) / "out")),
                        expected,
                    )

    def test_valid_assessments(self):
        for risk, code, normalized in [
            ("NONE", 0, "LOW"), ("LOW", 0, "LOW"),
            ("UNKNOWN", 0, "UNKNOWN"),
            ("MEDIUM", 1, "MEDIUM"), ("HIGH", 2, "HIGH"),
        ]:
            with self.subTest(risk=risk):
                self.run_case(code, {"risk": risk}, normalized)

    def test_contradictions_and_bad_output_fail_closed(self):
        for code, value in [
            (0, {"risk": "HIGH"}), (1, {"risk": "LOW"}),
            (2, {"risk": "MEDIUM"}), (0, {"risk": "INVALID"}),
            (0, {}), (0, []), (3, {"risk": "HIGH"}),
            (127, {"risk": "LOW"}),
        ]:
            with self.subTest(code=code, value=value):
                self.run_case(code, value)

    def test_malformed_and_empty_json_fail_closed(self):
        for content in ["", "{", "null", "[1]", "42"]:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as directory:
                    result = subprocess.CompletedProcess(["python"], 0, content, "")
                    with patch.object(action.subprocess, "run", return_value=result):
                        with self.assertRaises(action.CheckExecutionError):
                            action._run_check("dummy.py", [], str(Path(directory) / "out"))

    def test_operational_failures_are_not_risk_assessments(self):
        for error in [subprocess.TimeoutExpired("test", 120), OSError("missing binary")]:
            with self.subTest(error=type(error).__name__):
                with tempfile.TemporaryDirectory() as directory:
                    with patch.object(action.subprocess, "run", side_effect=error):
                        with self.assertRaises(action.CheckExecutionError):
                            action._run_check("dummy.py", [], str(Path(directory) / "out"))

    def test_aggregation_preserves_high_and_unknown(self):
        self.assertEqual(action._aggregate_risk("LOW", "HIGH"), "HIGH")
        self.assertEqual(action._aggregate_risk("LOW", "UNKNOWN"), "UNKNOWN")
        self.assertEqual(action._aggregate_risk("MEDIUM", "HIGH"), "HIGH")


if __name__ == "__main__":
    unittest.main()
