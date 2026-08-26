# agentrust-io security baseline

Shared security tooling for agentrust-io repositories.

## Reusable Python security workflow

`.github/workflows/reusable-python-security.yml` runs ruff (lint), mypy (types), bandit (SAST), pip-audit (SCA), and generates a CycloneDX SBOM. Call it from any Python repo with `.github/workflows/security.yml`:

    name: security
    on:
      push: { branches: [main] }
      pull_request: { branches: [main] }
    jobs:
      security:
        uses: agentrust-io/.github/.github/workflows/reusable-python-security.yml@main

## Per-repo additions (not centralised)

Each repo should also carry, matching cmcp / ca2a / agent-manifest:

- `codeql.yml` (CodeQL SAST) and `scorecard.yml` (OSSF Scorecard)
- `.github/dependabot.yml` (pip + github-actions, weekly)
- `.github/CODEOWNERS`
- a standard `LICENSE`

Copy-paste versions of these, plus the org-level settings (secret scanning, push protection, Dependabot alerts, and the branch-protection ruleset), are in the internal security hardening bundle.

## Action pinning

All actions first-party (`actions/*`) and third-party (e.g. `anchore/sbom-action`) are pinned to a commit SHA with a `# vX.Y.Z` comment for readability. This applies org-wide; see `reusable-python-security.yml` and `sbom.yml` in cmcp / ca2a / trace-spec for the pattern. When bumping a version, update both the SHA and the comment together.
