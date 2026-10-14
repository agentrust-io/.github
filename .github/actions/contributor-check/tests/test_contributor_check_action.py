"""Regression tests for the contributor-check action entrypoint.

The case these exist for is agentrust-io/.github#27: a check that could not be
executed used to be reported as the contributor-risk level UNKNOWN, which is
fail-closed ordered above LOW, so an infrastructure fault labelled established
contributors as more suspicious than genuinely low-risk ones.

The shape of that fault is a script that exits non-zero with empty stdout. It
happens when a vendored sibling is missing, and it is exactly what a
`sparse-checkout: scripts` produced against an upstream shim that imports a
package outside `scripts/`.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ACTION_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ACTION_DIR / "vendor" / "agt" / "contributor_check_action.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("contributor_check_action", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


action = _load_module()


def _stub(tmp_path: Path, name: str, body: str) -> str:
    """Write a stub check script that behaves like `body` says."""
    script = tmp_path / name
    script.write_text(body, encoding="utf-8")
    return str(script)


# ── The regression case ───────────────────────────────────────────


def test_scripts_only_style_failure_raises_instead_of_returning_unknown(tmp_path):
    """A check that exits non-zero with empty stdout is an execution fault.

    This is the #27 case. Before the fix, json.loads("") raised, the bare
    `except Exception` swallowed it, and the caller received "UNKNOWN".
    """
    script = _stub(
        tmp_path,
        "contributor_check.py",
        "import sys\n"
        "print(\"ModuleNotFoundError: No module named 'agent_compliance'\","
        " file=sys.stderr)\n"
        "sys.exit(1)\n",
    )

    with pytest.raises(action.CheckExecutionError) as excinfo:
        action._run_check(script, ["--username", "someone"], str(tmp_path / "out.json"))

    message = str(excinfo.value)
    assert "contributor_check.py" in message
    assert "exited 1" in message
    assert "UNKNOWN" not in message


def test_missing_script_is_an_execution_fault(tmp_path):
    """A vendored sibling that is not on disk must not score as a risk level."""
    with pytest.raises(action.CheckExecutionError):
        action._run_check(
            str(tmp_path / "does_not_exist.py"),
            ["--username", "someone"],
            str(tmp_path / "out.json"),
        )


def test_zero_exit_with_empty_stdout_is_an_execution_fault(tmp_path):
    """Exiting 0 while producing nothing is still not a determination."""
    script = _stub(tmp_path, "quiet.py", "pass\n")

    with pytest.raises(action.CheckExecutionError):
        action._run_check(script, [], str(tmp_path / "out.json"))


# ── The cases the fix must not break ──────────────────────────────


def test_genuine_unknown_is_still_returned(tmp_path):
    """A check that ran and could not determine an answer still reports UNKNOWN.

    This is the distinction #27 item 2 asks for: UNKNOWN keeps its upstream
    meaning, and only the execution fault is pulled out of it.
    """
    script = _stub(tmp_path, "profile.py", 'print(\'{"risk": "UNKNOWN"}\')\n')

    assert action._run_check(script, [], str(tmp_path / "out.json")) == "UNKNOWN"


@pytest.mark.parametrize("risk,expected", [("LOW", "LOW"), ("MEDIUM", "MEDIUM"), ("HIGH", "HIGH")])
def test_computed_risk_passes_through(tmp_path, risk, expected):
    exit_code = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}[risk]
    script = _stub(
        tmp_path, "profile.py",
        f'import sys\nprint(\'{{"risk": "{risk}"}}\')\nsys.exit({exit_code})\n',
    )

    assert action._run_check(script, [], str(tmp_path / "out.json")) == expected


def test_none_still_normalises_to_low(tmp_path):
    """credential_audit returns NONE when there is nothing to audit."""
    script = _stub(tmp_path, "cred.py", 'print(\'{"risk": "NONE"}\')\n')

    assert action._run_check(script, [], str(tmp_path / "out.json")) == "LOW"


def test_stdout_is_still_written_for_the_failing_case(tmp_path):
    """The output file is written even when the check fails, for debugging."""
    out = tmp_path / "out.json"
    script = _stub(tmp_path, "partial.py", "import sys\nprint('half')\nsys.exit(3)\n")

    with pytest.raises(action.CheckExecutionError):
        action._run_check(script, [], str(out))

    assert out.read_text(encoding="utf-8").strip() == "half"


# ── What the action does with the fault ───────────────────────────


def test_execution_fault_exits_nonzero_and_applies_no_label(tmp_path, monkeypatch, capsys):
    """An execution fault fails the step and never reaches comment or label."""
    outputs = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(outputs))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))
    monkeypatch.setenv("GITHUB_TOKEN", "x")

    def _boom(*_args, **_kwargs):
        raise action.CheckExecutionError("contributor_check.py exited 1: boom")

    posted: list[object] = []
    monkeypatch.setattr(action, "_run_check", _boom)
    monkeypatch.setattr(action, "_post_comment", lambda *a, **k: posted.append("comment"))
    monkeypatch.setattr(action, "_apply_label", lambda *a, **k: posted.append("label"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "contributor_check_action.py",
            "--username", "Mayur021",
            "--target-repo", "agentrust-io/agent-manifest",
            "--number", "272",
            "--item-type", "issue",
        ],
    )

    with pytest.raises(SystemExit) as excinfo:
        action.main()

    assert excinfo.value.code == 1
    assert posted == []

    written = outputs.read_text(encoding="utf-8")
    assert "risk=ERROR" in written
    for level in ("LOW", "MEDIUM", "HIGH", "UNKNOWN"):
        assert f"risk={level}\n" not in written

    assert "::error" in capsys.readouterr().out


def test_unknown_still_aggregates_above_low():
    """The fail-closed ordering itself is unchanged."""
    assert action._aggregate_risk("LOW", "UNKNOWN") == "UNKNOWN"
    assert action._aggregate_risk("UNKNOWN", "HIGH") == "HIGH"
    assert action._aggregate_risk("LOW", "LOW") == "LOW"


def test_vendored_siblings_the_action_invokes_are_present():
    """Every script the entrypoint can run must be vendored beside it.

    contributor_check_action.py resolves its checks as siblings through
    Path(__file__).parent, so a sibling that is missing is a deployment fault
    that only shows up at runtime. The default checks are profile and
    credential; cluster runs on workflow_dispatch.
    """
    vendor = MODULE_PATH.parent
    for name in (
        "contributor_check.py",
        "credential_audit.py",
        "cluster_detect.py",
        "contributor_check_allowlist.json",
    ):
        assert (vendor / name).is_file(), f"{name} is not vendored beside the entrypoint"


def test_vendored_files_keep_their_upstream_licence_header():
    vendor = MODULE_PATH.parent
    for path in sorted(vendor.glob("*.py")):
        head = path.read_text(encoding="utf-8").splitlines()[:3]
        assert "Copyright (c) Microsoft Corporation." in head[1], path.name
        assert "Licensed under the MIT License." in head[2], path.name


def test_allowlist_is_valid_json_and_ships_empty():
    data = json.loads(
        (MODULE_PATH.parent / "contributor_check_allowlist.json").read_text(encoding="utf-8")
    )
    assert data["users"] == []
    assert data["orgs"] == []
