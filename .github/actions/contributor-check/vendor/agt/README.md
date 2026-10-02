# Vendored AGT contributor-check scripts

These files are copied from
[microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit),
MIT License, at commit `359a6b8cf453f95d6bc9caf932057e1e78ccffd9`
(`main` as of 2026-07-31), from the `scripts/` directory. Each file keeps its
original copyright and licence header.

They were previously fetched at action runtime by a pinned `actions/checkout`
with `sparse-checkout: scripts`. That coupled contributor gating to an upstream
repository's internal script layout: a layout change upstream becomes a runtime
failure here, and a runtime failure used to be reported as a contributor-risk
level. See agentrust-io/.github#27.

## Contents

| File | Upstream path | SHA-256 |
|---|---|---|
| `contributor_check.py` | `scripts/contributor_check.py` | modified, see below |
| `contributor_check_allowlist.json` | `scripts/contributor_check_allowlist.json` | `d8a5ddbb0695c21b3eae88e6bc85edcda6cbd9721cad3ca9d10fbeeed4fc0636` |
| `credential_audit.py` | `scripts/credential_audit.py` | `9650675038e7720a6d5cdd8be058fa38b2e004cc1e6f7bc81c48ed100e4680e1` |
| `cluster_detect.py` | `scripts/cluster_detect.py` | `da36c10074aa638bf61c5873fbe6cff975533563553689eba5e90329e3d8d7cf` |
| `contributor_check_action.py` | `scripts/contributor_check_action.py` | modified, see below |

The first three unmodified files are byte-identical to upstream at that commit.
The checksums above are the upstream bytes, so `sha256sum` here is a one-line
verification for those three.

## The two local modifications

### `contributor_check_action.py`

`contributor_check_action.py` differs from upstream in `_run_check` and in the
block of `main()` that calls it. `_run_check` now reads the subprocess return
code. A check that could not be executed raises `CheckExecutionError` and the
action exits non-zero with an operational error, instead of returning the
contributor-risk level `UNKNOWN`.

`UNKNOWN` still means what its upstream comment says it means: a check that ran
and could not determine an answer. That case is unchanged and still labels.

### `contributor_check.py`

`_api` now carries a bounded retry. Upstream loops three times but only a 403
retries; a 5xx raises on the first attempt and `URLError` is not imported at
all, so the `timeout=15` socket timeout propagates straight through the loop.
That is the failure behind agentrust-io/.github#27. Since the
`contributor_check_action.py` change above, it no longer mislabels a
contributor; it fails the action instead. A single transient blip still ends a
check that a retry would have passed, which is what this change addresses.

The retry is limited to transient failures and reports anything else as itself:

| Condition | Behaviour |
|---|---|
| 404 | Returns `None`. An answer, never retried. |
| 403 rate limit | Honours `Retry-After`, clamped to 5-60s, within the attempt bound. |
| 5xx | Full-jitter exponential backoff within the attempt bound. |
| `URLError` | Full-jitter exponential backoff within the attempt bound. |
| Any other HTTP status | Raised on the first attempt. |

When a retryable condition outlasts the bound, the final line written to stderr
names the cause before the exception propagates. `contributor_check_action.py`
reports the last stderr line, so a rate limit surfaces as a rate limit and a
server error as a server error rather than as an unattributed execution fault.

## Why more than two files

`contributor_check_action.py` resolves the scripts it runs as siblings of
itself, through `Path(__file__).resolve().parent`. The composite action runs
`profile,credential` by default and `profile,credential,cluster` on dispatch,
so `credential_audit.py` is invoked on every run and `cluster_detect.py` on
some. `contributor_check.py` reads `contributor_check_allowlist.json` from its
own directory and silently grants no exemptions if it is absent.

Vendoring only the two files named in #27 would leave those siblings missing,
and with the return-code change that is now a hard failure on every run rather
than a silent `UNKNOWN`. All five move together or none of them do.

## Updating

These files are no longer tracked against upstream. Per the decision recorded
on agentrust-io/.github#27, AGT is not being invested in and this copy is owned
here. The commit above is provenance, not a sync point, and no resync is
planned.

Change these files directly, as you would any other file in this repository.
If a change lands in one of the three that remain byte-identical, move it out of
the checksum table above and out of the `vendor-integrity` job, and describe the
change here, the way the two modified files are described.
