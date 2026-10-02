# Organization maintainers

The [maintainers team](https://github.com/orgs/agentrust-io/teams/maintainers) maintains all current AgenTrust repositories. Its members are `imran-siddique`, `pforest` and `Qiang-Xu`.

Qiang is a maintainer across all AgenTrust repositories. Repository-specific maintainers retain their existing scope.

Maintainers can merge after the applicable reviews, checks and thread-resolution requirements pass. Approval must cover the current head; authors and the last pusher still need independent approval. Repository access does not waive specification governance or specialist code-owner requirements.

When adding a repository or appointing a maintainer, keep team access, CODEOWNERS and any named-maintainer workflow list aligned.

## Operational coverage

The canonical [roster](maintainers/roster.json) defines repository routing pairs, generated approval policies and CODEOWNERS. The [handover record](maintainers/handover.md) distinguishes verified repository permissions from pending capacity, specialist, organization-owner and publisher checks. A routing role does not appoint a new maintainer or waive repository governance.

Run `node scripts/maintainer-roster.mjs validate` and `node --test scripts/maintainer-roster.test.mjs` before changing the roster. Generate snapshots with `node scripts/maintainer-roster.mjs render OUTPUT_DIRECTORY`, then apply the reviewed gate template with `renderGate`. Update canonical and consumer PRs together. The daily audit fails on deployed drift and retains its report for 14 days.
