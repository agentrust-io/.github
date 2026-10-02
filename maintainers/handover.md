# Maintainer handover

Imran authorized this operational coverage rollout on 2026-10-02. Routing pairs are proposed responsibilities for existing appointed maintainers; capacity acceptance and publisher access are not yet confirmed. This record does not appoint new maintainers, change organization ownership or waive repository governance.

## Routing and capacity

[roster.json](roster.json) is the canonical source for deployed maintainer policy and CODEOWNERS. Repository snapshots are generated from it. The daily coverage workflow reports drift; it never changes access or merges work.

| Repository | Primary | Backup | Verified repository permission, 2026-10-02 | Capacity acceptance |
|---|---|---|---|---|
| [.github](https://github.com/agentrust-io/.github) | @Qiang-Xu | @pforest | admin / admin | Pending |
| [agent-manifest](https://github.com/agentrust-io/agent-manifest) | @rajnisht7 | @zohebk8s | write / write | Pending |
| [cmcp](https://github.com/agentrust-io/cmcp) | @carloshvp | @zohebk8s | write / write | Pending |
| [ca2a](https://github.com/agentrust-io/ca2a) | @carloshvp | @zohebk8s | write / write | Pending |
| [trace-spec](https://github.com/agentrust-io/trace-spec) | @lywinged | @rajnisht7 | write / write | Pending |
| [trace-registry](https://github.com/agentrust-io/trace-registry) | @Qiang-Xu | @pforest | admin / admin | Pending |
| [weight-custody-manifest](https://github.com/agentrust-io/weight-custody-manifest) | @Qiang-Xu | @pforest | admin / admin | Pending |
| [integrations](https://github.com/agentrust-io/integrations) | @carloshvp | @Qiang-Xu | write / write | Pending |
| [agentrust-telemetry](https://github.com/agentrust-io/agentrust-telemetry) | @Qiang-Xu | @pforest | write / write | Pending |
| [awesome-ai-governance](https://github.com/agentrust-io/awesome-ai-governance) | @pforest | @Qiang-Xu | write / write | Pending |
| [agentrust-io.github.io](https://github.com/agentrust-io/agentrust-io.github.io) | @pforest | @Qiang-Xu | write / write | Pending |

Route routine reviews to the primary. If unacknowledged after two business days, route to the backup; record the actual response here. An author or last pusher still needs independent review. A maintainer may merge after checks, required owners and discussion resolution pass. Specification comment periods, breaking-change approvals, security requirements, append-only registry history and project-lead publication decisions remain applicable.

### Specialist coverage requiring verification

- Agent Manifest: confirm two active members with explicit team write access in `spec-editors` and `sdk-maintainers`. Rajnish and Zoheb have repository write access, which does not prove membership in those teams.
- WCM: confirm two active spec editors and SDK maintainers. Qiang and Trish have repository admin access. Zoheb currently has read access; do not count him as an SDK owner or grant access without the applicable appointment process.
- Registry: confirm two active members of `opaque-lt`; repository admin access alone does not establish required code-owner coverage.
- CMCP and CA2A: the generated gate requires two distinct human maintainer approvals at the current head for listed security paths, including renames out of them. Other security-critical changes still need manual classification and two approvals under governance. CODEOWNERS accepts any one owner on a line and does not establish separate security-team sign-off.

### Administration

Qiang and Trish provide verified repository administration backups for .github, CMCP, Agent Manifest, TRACE, registry and WCM. They have write access to CA2A, integrations, telemetry, website and awesome-ai-governance. Organization-owner membership and recovery access remain unverified. Confirm two organization owners through private settings. Keep emergency administration separate from routine independent review; do not add bypass rights to clear normal PRs.

## Release operators

| Repository | Existing publisher workflow | Proposed operators | Package/environment access |
|---|---|---|---|
| agent-manifest | [publish.yml](https://github.com/agentrust-io/agent-manifest/blob/main/.github/workflows/publish.yml) | @rajnisht7 / @zohebk8s | Unverified |
| cmcp | [release.yml](https://github.com/agentrust-io/cmcp/blob/main/.github/workflows/release.yml) | @carloshvp / @zohebk8s | Unverified |
| ca2a | [release.yml](https://github.com/agentrust-io/ca2a/blob/main/.github/workflows/release.yml) | @carloshvp / @zohebk8s | Unverified |
| trace-spec | [publish.yml](https://github.com/agentrust-io/trace-spec/blob/main/.github/workflows/publish.yml) | @lywinged / @rajnisht7 | Unverified |
| trace-registry | [publish.yml](https://github.com/agentrust-io/trace-registry/blob/main/.github/workflows/publish.yml) | @Qiang-Xu / @pforest | Unverified |
| weight-custody-manifest | [publish.yml](https://github.com/agentrust-io/weight-custody-manifest/blob/main/.github/workflows/publish.yml) | @Qiang-Xu / @pforest | Unverified |
| integrations | [capture-core-publish.yml](https://github.com/agentrust-io/integrations/blob/main/.github/workflows/capture-core-publish.yml), [trace-adapters-publish.yml](https://github.com/agentrust-io/integrations/blob/main/.github/workflows/trace-adapters-publish.yml) | @carloshvp / @Qiang-Xu | Unverified |
| agentrust-telemetry | [release.yml](https://github.com/agentrust-io/agentrust-telemetry/blob/main/.github/workflows/release.yml) | @Qiang-Xu / @pforest | Unverified |

OIDC workflows already publish without shared API tokens. For each package, privately verify two package owners, exact trusted-publisher repository/workflow/environment binding, and two available environment approvers where applicable. Record verification date and workflow/run or package role evidence here; never record credentials. Verify the backup can initiate the permitted workflow and obtain independent environment approval. No new publisher is active merely because an operator is listed.

The WCM manual workflow publishes to TestPyPI; other manual publisher workflows may publish to production. For the handover rehearsal use package-build CI and installed-artifact smoke checks first. A TestPyPI run is appropriate only after its publisher/environment is verified and the project lead approves its existing pre-1.0 publication policy. Do not dispatch a production publisher as a dry run.

## One-week handover

Status: **not started**. Start after the relevant rollout PRs merge, routing capacity is accepted and specialist access is verified. Record the actual start/end dates; the week is not complete until its evidence exists.

Acceptance evidence:

- [ ] Primary and backup accept their routing scopes; record dates here.
- [ ] At least two non-Imran maintainers independently review and merge routine work across their scopes. Link PRs, current-head approvals and checks; author/pusher must not supply the required independent approval.
- [ ] A release operator other than Imran runs package build/install validation, and a second operator demonstrates the permitted backup path. Link workflow runs. A production release is optional and requires the existing release policy.
- [ ] Specialist code-owner coverage and organization-owner recovery coverage are verified privately and summarized without credentials.
- [ ] After seven days, record blocked work, review response times, merge operators, release evidence and any intervention by Imran. Fix access or routing gaps before declaring independence.

| Evidence | URL / verified fact | Date | Result / remaining action |
|---|---|---|---|
| Repository permissions | Connector permission reads for all 22 primary/backup assignments | 2026-10-02 | All write/admin; specialist and organization-owner memberships unverified |
| Deployment | Rollout PRs | Pending | Independent maintainer review required |
| Handover start/end | Not set | Pending | Await deployment, acceptance and access verification |

## Consolidation remaining work

Examples and demos imports, consumer updates and moved notices are merged. Their open issue/PR queues were empty on 2026-10-02. Recheck immediately before archiving; preserve repositories, releases and historical URLs. The available connector cannot archive repositories.

TRACE import is merged. Preserve [trace-tests PR #137](https://github.com/agentrust-io/trace-tests/pull/137) and its review: it remains unmerged. Port it to conformance or merge and import it before archival. Keep the original PyPI publisher and tests.agentrust-io.com deployment active until separately verified replacements exist. The specification website must not be overwritten by a second gh-deploy. See [TRACE cutover](https://github.com/agentrust-io/trace-spec/blob/main/docs/repository-consolidation.md).

## Rollout pull requests

- [.github #52](https://github.com/agentrust-io/.github/pull/52)
- [agent-manifest #484](https://github.com/agentrust-io/agent-manifest/pull/484)
- [cmcp #720](https://github.com/agentrust-io/cmcp/pull/720)
- [ca2a #223](https://github.com/agentrust-io/ca2a/pull/223)
- [trace-spec #462](https://github.com/agentrust-io/trace-spec/pull/462)
- [trace-registry #112](https://github.com/agentrust-io/trace-registry/pull/112)
- [weight-custody-manifest #178](https://github.com/agentrust-io/weight-custody-manifest/pull/178)
- [integrations #273](https://github.com/agentrust-io/integrations/pull/273)
- [agentrust-telemetry #77](https://github.com/agentrust-io/agentrust-telemetry/pull/77)
- [awesome-ai-governance #133](https://github.com/agentrust-io/awesome-ai-governance/pull/133)
- [agentrust-io.github.io #96](https://github.com/agentrust-io/agentrust-io.github.io/pull/96)

Auto-merge is enabled for ten rollout PRs; trace-registry has auto-merge disabled and requires a normal maintainer merge after independent review. The rollout is not deployed merely because its PR exists. CI validates the policies and gate boundaries; the handover week still awaits accepted capacity and verified private access.

[TRACE #462](https://github.com/agentrust-io/trace-spec/pull/462) prepares the separate conformance publisher with publication disabled until its exact environment/trusted-publisher binding is verified.
