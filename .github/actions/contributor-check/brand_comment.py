#!/usr/bin/env python3
"""Apply AgenTrust branding to the public contributor-check comment.

The check implementation delegates to microsoft/agent-governance-toolkit at a
pinned commit. That upstream script owns the risk calculation and writes an
idempotent PR/issue comment. Keep its hidden marker so future runs update the
same comment, but make the visible footer point at the AgenTrust action.
"""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


MARKER = "<!-- agt-contributor-check -->"
AGENTRUST_FOOTER = (
    "*Automated check by "
    "[AgenTrust Contributor Check]"
    "(https://github.com/agentrust-io/.github/tree/main/.github/actions/contributor-check).*"
)


def _api(token: str, method: str, path: str, data: dict | None = None) -> dict | list | None:
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = Request(url, method=method, headers=headers)
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()

    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _branded_body(body: str) -> str:
    if AGENTRUST_FOOTER in body:
        return body

    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("*Automated check by ") and "Contributor Check" in line:
            lines[index] = AGENTRUST_FOOTER
            return "\n".join(lines)

    return f"{body.rstrip()}\n\n{AGENTRUST_FOOTER}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Brand contributor-check comment")
    parser.add_argument("--github-token", required=True)
    parser.add_argument("--target-repo", required=True)
    parser.add_argument("--number", type=int, required=True)
    parser.add_argument("--item-type", choices=["pr", "issue", "manual"], required=True)
    args = parser.parse_args()

    if args.item_type == "manual" or args.number <= 0:
        print("No PR/issue comment to brand.")
        return

    owner, repo = args.target_repo.split("/", 1)
    page = 1
    while True:
        comments = _api(
            args.github_token,
            "GET",
            f"/repos/{owner}/{repo}/issues/{args.number}/comments?per_page=100&page={page}",
        )
        if not comments:
            print("No contributor-check comment found.")
            return

        for comment in comments:
            body = comment.get("body") or ""
            if MARKER not in body:
                continue

            branded = _branded_body(body)
            if branded == body:
                print("Contributor-check comment already has AgenTrust branding.")
                return

            _api(
                args.github_token,
                "PATCH",
                f"/repos/{owner}/{repo}/issues/comments/{comment['id']}",
                {"body": branded},
            )
            print("Applied AgenTrust branding to contributor-check comment.")
            return

        if len(comments) < 100:
            print("No contributor-check comment found.")
            return
        page += 1


if __name__ == "__main__":
    main()
