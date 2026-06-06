# agentrust-io

Open trust infrastructure for the agentic AI era.

## Projects

| Project | Description | License | Status |
|---------|-------------|---------|--------|
| [agent-manifest](https://github.com/agentrust-io/agent-manifest) | Agent Manifest SDK — attest all 10 artifacts defining an agent at deployment. Python + TypeScript. | Apache 2.0 | Private — Preview Ai4 Aug 4 |
| [cmcp](https://github.com/agentrust-io/cmcp) | cMCP — Confidential MCP Gateway. Hardware-attested policy enforcement for MCP tool calls. | MIT | Private — CC Summit Jun 23 |
| [trace-spec](https://github.com/agentrust-io/trace-spec) | TRACE — Trust Runtime Attestation and Compliance Evidence. Open attestation standard. | CC BY 4.0 | Private — AAIF submission Jul 2026 |
| [trace-registry](https://github.com/agentrust-io/trace-registry) | Append-only public Merkle registry mirror for TRACE claim anchors. | CC BY 4.0 | Private |
| [trace-tests](https://github.com/agentrust-io/trace-tests) | TRACE compliance test suite for certification. | Apache 2.0 | Private |
| [examples](https://github.com/agentrust-io/examples) | Integration examples across financial services, healthcare, and SaaS. | MIT | Private |

## Principles

Everything a developer needs to produce attested artifacts is free and open here. Everything an enterprise needs to verify those artifacts at scale, with SLAs, for regulators — that is commercial at [opaque.co](https://opaque.co).

The open-source projects in this org are developed in the open and submitted to standards bodies:

- **TRACE spec** — submitting to the Agentic AI Foundation (AAIF) under the Linux Foundation
- **Agent Manifest spec** — submitting to CoSAI under OASIS Open, building on CoSAI WS4 publications
- **AGT** — the governance engine this stack builds on is entering AAIF via Microsoft

---

## Zero-Trust Framework Alignment

The Anthropic *Zero-Trust for AI Agents* eBook (May 2026) adapts NIST SP 800-207 to agentic systems, calling for continuous verification at six layers: agent identity and authentication, supply chain security, MCP and tool security, policy enforcement and governance, multi-agent coordination, and detection and response. This section maps each layer to the agentrust-io stack and names the gaps honestly.

The core argument in that document: traditional perimeter security fails for AI agents because a signed JWT proves *who called an API*, not *what agent made the call*, *which system prompt was active*, *which model version ran*, or *under which policy it was operating*. That is the problem this org was built to solve.

### Agent Identity — closing the attestation gap

The PDF frames agent identity as an authentication problem. The sharper framing: it is an **attestation** gap. Authentication proves who called. Attestation proves what ran and under what configuration.

**Agent Manifest** binds ten artifacts into a single cryptographically signed, hardware-attestable document:

| # | Artifact | Attack if unattested |
|---|---|---|
| 1 | System prompt | Prompt injection redefines agent goals |
| 2 | Policy bundle | Policy swap grants unapproved permissions |
| 3 | Tool manifest | Schema extension silently expands capabilities |
| 4 | Model identity | Unapproved version may lack safety alignment |
| 5 | RAG corpus | Corpus poisoning changes outputs silently |
| 6 | Memory baseline | Memory drift corrupts long-running agents |
| 7 | Decision trace | No accountability for high-stakes decisions |
| 8 | A2A delegation chain | Orchestrator spoofing, scope laundering |
| 9 | Supply chain provenance | Compromised dependency runs as approved binary |
| 10 | HITL approvals | EU AI Act Art. 14 violation |

The signing key is hardware-sealed in a TEE (TPM, AMD SEV-SNP, Intel TDX, or Opaque Managed Runtime). A verifier holding the manifest and attestation report can prove — without trusting the operator — that a specific agent ran specific code under specific policy. Agent identity and user identity are cryptographically separate credentials: SPIFFE SVIDs for workload identity, Ed25519 (or post-quantum ML-DSA-65 at Level 3) for the manifest signature.

Four conformance levels address the full deployment range:

| Level | Name | Use case |
|---|---|---|
| 0 | Software-only | Development, staging |
| 1 | TEE-attested | Enterprise production, EU AI Act Art. 15 |
| 2 | Full stack | Regulated industries, DORA Art. 9 |
| 3 | Post-quantum | Sovereign, classified, long-horizon financial |

### Supply Chain Security

Agent Manifest artifact #9 binds container digest, SLSA provenance level, and SBOMs into the signed manifest. A supply chain attack that swaps the container invalidates the TEE measurement, which invalidates the manifest signature. Hardware attestation makes this structurally detectable, not just policy-prohibited.

**TRACE** includes `build_provenance` as a first-class field (SLSA Provenance v1.0) and an `AIBOM` field (SPDX 3.0 / CycloneDX 1.7) capturing the model weights digest. The model component inventory is bound into a hardware-attested record — it cannot be swapped after signing.

Every agentrust-io repository carries OpenSSF Scorecard badges, CodeQL SAST, Dependabot, pip-audit on every PR, and bandit security linting. The tooling in this org practices what it recommends.

### MCP and Tool Security

The Anthropic eBook cites specific MCP attacks: the Invariant Labs GitHub compromise via MCP integration, the Zenity AgentFlayer 0-click attack, the Postmark MCP npm backdoor. These are not hypothetical threats.

**cMCP (Confidential MCP Gateway)** is a direct response. Every MCP tool call is intercepted, evaluated against a Cedar policy bundle, and enforced by a policy engine running inside a TEE. The policy bundle hash is measured into the hardware attestation report before any code runs.

| Threat | Software governance | cMCP |
|---|---|---|
| Admin replaces Cedar policy on disk | Undetected — hash chain runs in compromised OS | Policy hash measured by hardware before code runs |
| Supply chain CVE flips allow/deny signal | Undetected — evaluator in attacker's address space | Evaluator in isolated enclave memory |
| Admin regenerates audit log post-breach | Undetected — any party with signing key can reconstruct | Signing key hardware-sealed — new valid signatures structurally impossible |

Every cMCP tool call produces a GatewayClaim (a TRACE Profile) containing the runtime platform measurement, policy bundle hash, and hardware-sealed confirmation key. Tool call authorization is independently auditable and tamper-evident.

### Policy Enforcement and Governance

The eBook calls for policy at four layers — model, agent, tool, request — with fleet management, centralized policy management, audit logging, and compliance monitoring.

**cMCP** handles tool-level and request-level policy with Cedar inside a TEE. Cedar is designed for per-request evaluation; this is not a batch audit — it is runtime enforcement on every call.

**TRACE** defines the governance record format: what a compliance artifact should contain, how it is cryptographically bound, and how it anchors in a transparency log. TRACE composes existing standards rather than replacing them:

| Primitive | Role in TRACE |
|---|---|
| RATS / EAT (RFC 9711) | Wire envelope and claim model |
| SLSA Provenance v1.0 | Build-time provenance |
| SPIFFE SVID | Workload identity |
| SCITT | Append-only transparency anchoring |
| EAR (draft-ietf-rats-ar4si) | Verifier appraisal output |
| MCP / A2A | Agent tool-call transcript surface |
| AIBOM (SPDX 3.0 / CycloneDX 1.7) | Model component inventory |

**TRACE Registry** is the public append-only Merkle registry of TRACE claim anchors. The canonical registry API is operated by [Opaque Systems](https://opaque.co); the GitHub mirror exists so any party can verify anchors without trusting Opaque. Git's immutable commit history is the tamper-evident proof.

**AGT (Agent Governance Toolkit)** — [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit), entering AAIF — provides the runtime governance layer: trust score decay (a score at deployment is meaningless six months later), the VADP delegation protocol (scope-narrowing agent-to-agent delegation with verifiable credentials), and a fleet daemon for multi-agent orchestration.

### Multi-Agent Coordination Security

The eBook calls for authentication of agent-to-agent communication, RBAC for agent hierarchies, and consensus for high-stakes decisions.

Agent Manifest artifact #8 (A2A Delegation) binds the full agent-to-agent trust chain into the manifest. A delegated scope cannot exceed the orchestrator's own attested manifest permissions — orchestrator spoofing and scope laundering are structurally prevented. AGT's VADP provides the specific mechanism: scope-narrowing delegation with verifiable credentials. This is the differentiator over A2A, ACP, MCP, ANP, and APTP, which do not combine scope-narrowing delegation with verifiable credentials in this way.

TRACE's `tool_transcript` field surfaces the MCP/A2A call surface as a hashed, counted artifact in each governance record. In a multi-agent system, each agent's TRACE record enables reconstruction of the full interaction graph post-hoc.

### Detection and Response

**Current coverage:** TRACE provides the immutable audit chain from which anomalies could be detected. AGT's GovernanceEventSink SPI is a pluggable event sink — anomaly detection can be wired in without vendor coupling. Trust score decay in AGT is a passive form of behavioral posture management.

**Gaps:** There is no dedicated behavioral anomaly detection or agent quarantine tooling in the current repos. Automated response — quarantine procedures, rollback — is on the AGT roadmap but not shipped. The eBook's recommendation for sleeper agent detection through behavioral analysis has no direct counterpart here yet. TRACE provides the audit foundation; detection is not included.

---

## Standards Coverage

| Standard | Agent Manifest | TRACE | cMCP | AGT |
|---|---|---|---|---|
| NIST SP 800-207 (Zero Trust) | Identity, policy layers | Governance records | Tool-level ZT enforcement | Fleet policy, observability |
| OWASP Agentic AI Top 10 (2026) | All 10 risk categories | Evidence chain | MCP call enforcement | Runtime governance |
| NIST AI RMF 1.0 | GOVERN, MAP, MEASURE, MANAGE | MEASURE, MANAGE | GOVERN (tool policy) | Full RMF lifecycle |
| EU AI Act Art. 13-15 | Transparency, HITL (Art. 14), cybersecurity (Art. 15 Level 1) | Compliance evidence | Enforcement evidence | Governance lifecycle |
| DORA Art. 9 | Attestation + 180-day log retention (Level 2) | Immutable audit chain | Per-call audit records | Risk management |
| MITRE ATL | Supply chain, model identity, prompt constraints | Verifiable evidence | Policy enforcement | Detection foundation |
| SLSA | Level 2 build provenance | `build_provenance` field | SLSA-aware claims | Supply chain |
| CoSAI WS1 | Secure-by-Design, MCP Security Taxonomy | — | MCP enforcement | WS4 governance |

---

## Community

- Questions and discussion: [GitHub Discussions](https://github.com/orgs/agentrust-io/discussions)
- Security issues: see [SECURITY.md](.github/SECURITY.md)
- Contributing: see [CONTRIBUTING.md](.github/CONTRIBUTING.md)
