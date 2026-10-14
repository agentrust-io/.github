#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# Vendored from microsoft/agent-governance-toolkit at commit
# 359a6b8cf453f95d6bc9caf932057e1e78ccffd9, path scripts/contributor_check_action.py.
# Local modification: _run_check reads the subprocess return code, so a check that
# could not be executed raises CheckExecutionError and the action exits with an
# operational error instead of reporting a contributor-risk level of UNKNOWN.
# See agentrust-io/.github#27. Every other file in this directory is verbatim.
"""Entrypoint for the contributor-check composite action.

Orchestrates profile analysis, credential audit, and cluster detection,
then posts a summary comment and applies labels on PRs/issues that meet
the risk threshold.

Usage (from the composite action):
    python scripts/contributor_check_action.py \
        --username <login> \
        --checks profile,credential \
        --target-repo owner/repo \
        --risk-threshold MEDIUM \
        --number 42 \
        --item-type pr
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MARKER = "<!-- agt-contributor-check -->"
# Fail-closed ordering: UNKNOWN ("could not be determined") must outrank LOW so
# a check that errored (e.g. GitHub API rate-limiting) cannot silently score a
# contributor as the lowest risk. We rank it just below HIGH so an uncertain
# result is treated as elevated/suspicious rather than clean. See issue #2950.
RISK_ORDER = {"LOW": 1, "MEDIUM": 2, "UNKNOWN": 3, "HIGH": 4}


# ── Helpers ───────────────────────────────────────────────────────


def _api(token: str, method: str, path: str, data: dict | None = None) -> dict | None:
    """Minimal GitHub API helper (no third-party deps)."""
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = Request(url, method=method, headers=headers)
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        if exc.code == 422:
            return None
        raise


class CheckExecutionError(RuntimeError):
    """A check could not be executed at all.

    This is an infrastructure fault (missing script, interpreter failure,
    timeout, or a check that exited non-zero) and it is deliberately NOT a
    contributor-risk level. UNKNOWN is reserved for a check that ran and could
    not determine an answer; conflating the two is what let a broken checkout
    label established contributors. See agentrust-io/.github#27.
    """


def _run_check(script: str, args: list[str], out_path: str) -> str:
    """Run a check script and return the risk level from its JSON output.

    Raises CheckExecutionError if the check could not be executed. Returns a
    risk level only when the check exited 0 and produced parseable JSON.
    """
    name = Path(script).name
    try:
        result = subprocess.run(
            [sys.executable, script, *args, "--json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise CheckExecutionError(f"{name} timed out after {exc.timeout}s") from exc
    except OSError as exc:
        raise CheckExecutionError(f"{name} could not be started: {exc}") from exc

    Path(out_path).write_text(result.stdout)

    # Scanners use 0/1/2 for completed LOW-or-NONE/MEDIUM/HIGH
    # assessments. A nonzero assessment is not a process failure.
    expected_exit = {"NONE": 0, "LOW": 0, "UNKNOWN": 0, "MEDIUM": 1, "HIGH": 2}
    if result.returncode not in (0, 1, 2):
        detail = (result.stderr or "").strip().splitlines()
        tail = detail[-1] if detail else "no stderr"
        raise CheckExecutionError(
            f"{name} exited {result.returncode}: {tail}"
        )

    try:
        data = json.loads(result.stdout)
    except ValueError as exc:
        raise CheckExecutionError(
            f"{name} exited {result.returncode} but produced invalid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise CheckExecutionError(f"{name} produced non-object JSON")
    risk = data.get("risk")
    if not isinstance(risk, str) or risk not in expected_exit:
        raise CheckExecutionError(f"{name} returned missing or unknown risk: {risk!r}")
    if result.returncode != expected_exit[risk]:
        raise CheckExecutionError(
            f"{name} reported risk {risk} but exited {result.returncode}"
        )
    # NONE means not applicable, not an unknown or failed scan.
    return "LOW" if risk == "NONE" else risk


def _aggregate_risk(*levels: str) -> str:
    """Return the highest risk level from a set of check results.

    Fail-closed: an UNKNOWN result (a check that could not be determined,
    e.g. an errored or rate-limited probe) outranks LOW/MEDIUM and surfaces
    as its own UNKNOWN aggregate rather than being silently scored LOW. See
    issue #2950.
    """
    if not levels:
        return "LOW"
    # Unrecognized labels are treated as UNKNOWN (uncertain), never LOW.
    max_val = max(RISK_ORDER.get(r, RISK_ORDER["UNKNOWN"]) for r in levels)
    for label, val in RISK_ORDER.items():
        if val == max_val:
            return label
    return "UNKNOWN"


def _set_output(name: str, value: str) -> None:
    """Write a value to $GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")


def _write_summary(text: str) -> None:
    """Append text to $GITHUB_STEP_SUMMARY."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(text)


# ── Comment / label helpers ───────────────────────────────────────


def _build_comment(username: str, overall: str, profile_risk: str,
                   cred_risk: str, cluster_risk: str) -> str:
    """Build a concise comment body with risk levels only."""
    # red=HIGH, white question=UNKNOWN (could not check), yellow=otherwise.
    if overall == "HIGH":
        icon = "\U0001f534"
    elif overall == "UNKNOWN":
        icon = "❔"
    else:
        icon = "\U0001f7e1"

    lines = [
        MARKER,
        f"{icon} **Contributor Check: {overall}**",
        "",
        "| Check | Result |",
        "|-------|--------|",
    ]
    if profile_risk:
        lines.append(f"| Profile | {profile_risk} |")
    if cred_risk:
        lines.append(f"| Credential | {cred_risk} |")
    if cluster_risk:
        lines.append(f"| Cluster | {cluster_risk} |")
    lines.append(f"| **Overall** | **{overall}** |")
    lines.append("")
    lines.append(
        "*Automated check by "
        "[AGT Contributor Check]"
        "(https://github.com/microsoft/agent-governance-toolkit"
        "/tree/main/scripts#contributor-reputation-tools).*"
    )
    return "\n".join(lines)


def _post_comment(token: str, owner: str, repo: str, number: int,
                  body: str) -> None:
    """Create or update the contributor-check comment (idempotent)."""
    page = 1
    existing_id = None
    while True:
        comments = _api(
            token, "GET",
            f"/repos/{owner}/{repo}/issues/{number}/comments?per_page=100&page={page}",
        ) or []
        for c in comments:
            if MARKER in (c.get("body") or ""):
                existing_id = c["id"]
                break
        if existing_id or len(comments) < 100:
            break
        page += 1

    if existing_id:
        _api(token, "PATCH",
             f"/repos/{owner}/{repo}/issues/comments/{existing_id}",
             {"body": body})
    else:
        _api(token, "POST",
             f"/repos/{owner}/{repo}/issues/{number}/comments",
             {"body": body})


def _apply_label(token: str, owner: str, repo: str, number: int,
                 risk: str) -> None:
    """Ensure the correct needs-review label is applied."""
    # red=HIGH, grey=UNKNOWN (could not check), orange=otherwise.
    color = {"HIGH": "D93F0B", "UNKNOWN": "BFBFBF"}.get(risk, "FFA500")
    try:
        _api(token, "POST", f"/repos/{owner}/{repo}/labels", {
            "name": f"needs-review:{risk}",
            "description": f"Contributor check flagged {risk} risk",
            "color": color,
        })
    except HTTPError:
        pass

    for level in ("LOW", "MEDIUM", "HIGH", "UNKNOWN"):
        if level != risk:
            try:
                req = Request(
                    f"https://api.github.com/repos/{owner}/{repo}"
                    f"/issues/{number}/labels/needs-review:{level}",
                    method="DELETE",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )
                urlopen(req, timeout=15)
            except Exception:
                pass

    _api(token, "POST", f"/repos/{owner}/{repo}/issues/{number}/labels", {
        "labels": [f"needs-review:{risk}"],
    })


# ── Main ──────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Contributor check action entrypoint")
    parser.add_argument("--username", required=True)
    parser.add_argument("--checks", default="profile,credential")
    parser.add_argument("--target-repo", required=True)
    parser.add_argument("--risk-threshold", default="MEDIUM")
    parser.add_argument("--number", type=int, default=0)
    parser.add_argument("--item-type", default="manual",
                        choices=["pr", "issue", "manual"])
    args = parser.parse_args()

    if not args.username:
        print("No username provided, skipping.")
        _set_output("risk", "UNKNOWN")
        return

    token = os.environ.get("GITHUB_TOKEN", "")
    scripts_dir = Path(__file__).resolve().parent
    checks = [c.strip() for c in args.checks.split(",")]

    profile_risk = ""
    cred_risk = ""
    cluster_risk = ""

    try:
        if "profile" in checks:
            profile_risk = _run_check(
                str(scripts_dir / "contributor_check.py"),
                ["--username", args.username, "--repo", args.target_repo],
                "/tmp/agt-profile.json",
            )

        if "credential" in checks:
            cred_risk = _run_check(
                str(scripts_dir / "credential_audit.py"),
                ["--username", args.username, "--repo", args.target_repo],
                "/tmp/agt-cred.json",
            )

        if "cluster" in checks:
            cluster_risk = _run_check(
                str(scripts_dir / "cluster_detect.py"),
                ["--seed", args.username],
                "/tmp/agt-cluster.json",
            )
    except CheckExecutionError as exc:
        # The check did not run, so no contributor risk was established. Fail
        # the step loudly rather than reporting a risk level: a fault here must
        # not become a needs-review label, and must not silently pass either.
        print(f"::error title=contributor-check could not run::{exc}")
        _set_output("risk", "ERROR")
        _set_output("profile-risk", profile_risk)
        _set_output("credential-risk", cred_risk)
        _set_output("cluster-risk", cluster_risk)
        _write_summary(
            f"## Contributor Check: `{args.username}`\n\n"
            "The check could not be run. No contributor risk level was "
            "established and no label was applied.\n\n"
            f"```\n{exc}\n```\n"
        )
        sys.exit(1)

    overall = _aggregate_risk(
        profile_risk or "LOW",
        cred_risk or "LOW",
        cluster_risk or "LOW",
    )

    # Set action outputs
    _set_output("risk", overall)
    _set_output("profile-risk", profile_risk)
    _set_output("credential-risk", cred_risk)
    _set_output("cluster-risk", cluster_risk)

    print(f"Contributor check for {args.username}: {overall}")

    # Post comment and label for PR/issue if risk meets threshold
    threshold_val = RISK_ORDER.get(args.risk_threshold, 2)
    risk_val = RISK_ORDER.get(overall, 0)

    if args.item_type != "manual" and args.number > 0 and risk_val >= threshold_val:
        owner, repo = args.target_repo.split("/", 1)
        body = _build_comment(
            args.username, overall, profile_risk, cred_risk, cluster_risk,
        )
        _post_comment(token, owner, repo, args.number, body)
        _apply_label(token, owner, repo, args.number, overall)
        print(f"Posted comment and label on #{args.number}")

    # Job summary
    summary_lines = [
        f"## Contributor Check: `{args.username}`\n",
        "| Check | Result |",
        "|-------|--------|",
    ]
    if profile_risk:
        summary_lines.append(f"| Profile | {profile_risk} |")
    if cred_risk:
        summary_lines.append(f"| Credential | {cred_risk} |")
    if cluster_risk:
        summary_lines.append(f"| Cluster | {cluster_risk} |")
    summary_lines.append(f"| **Overall** | **{overall}** |")
    summary_lines.append("")
    _write_summary("\n".join(summary_lines))


if __name__ == "__main__":
    main()
