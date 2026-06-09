# agentrust-io

Building AI agents right now is a lot like adopting a very fast, very confident puppy that also happens to have your API keys. It wanders. It chews on things it shouldn't. And the second you look away, it's leaked embarrassing data all over the floor.

So most of us spend our days wrestling agents into submission: chasing what drifts, mopping up what leaks, hoping the next one behaves. Here's a more fun way to live: build your agents with rules up front that you actually know will be enforced. And you can prove they were.

In some settings, that's a quirk you can mop up. In the enterprise, and anywhere regulated or sovereign, it's a breach. And the risk is mutating: the next leak may not be a careless agent at all, but a rogue one under a borrowed identity, indistinguishable from legitimate traffic. The risk is also increasing as new models grow increasingly capable of infiltration.

This leaves the builder with questions no current tooling can answer: Is this agent governed as it was built? Would I detect drift, or an identity operating in its place? Can I prove either to a party with no reason to trust me?

agentrust-io is the open trust layer built to answer them: replacing "we have guardrails that will probably catch issues and observability that will probably flag it after the fact" with evidence the builder can verify directly, and any auditor, customer, or regulator can independently confirm, without trusting the operator.

**This is not another agent framework.** agentrust-io doesn't replace the tools or standards teams already build with: it binds them into verifiable evidence. It comprises standards the ecosystem is already adopting: **MCP** and **A2A** for the agent and tool-call surface, **AGT** (Agent Governance Toolkit) for runtime policy, **SPIFFE** for workload identity, **SLSA** and **AIBOM/SBOM** for supply-chain and model provenance, **Cedar** for policy, and **RATS/EAT** for hardware attestation, aligned to NIST SP 800-207 and addresses all OWASP Agentic AI Top 10.

The specifications, SDKs, and conformance tests are free and open. Begin in software; advance to hardware-backed and post-quantum assurance as requirements demand.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/agentrust-io/agent-manifest/blob/main/LICENSE)
[![AAIF](https://img.shields.io/badge/Targeting-AAIF_%2F_Linux_Foundation-6366f1)](https://agenticai.foundation)
[![CC Summit](https://img.shields.io/badge/Launching-CC_Summit_Jun_23_2026-7c3aed)](https://confidentialcomputingsummit.com)

## Projects

| Project | Description | License | Status |
|---------|-------------|---------|--------|
| [agent-manifest](https://github.com/agentrust-io/agent-manifest) | Agent Manifest SDK: cryptographically bind all 10 artifacts defining an agent at deployment. Python + TypeScript. | Apache 2.0 | Developer Preview, launching CC Summit Jun 23 |
| [cmcp](https://github.com/agentrust-io/cmcp) | cMCP: Confidential MCP Runtime. Hardware-attested policy enforcement for MCP tool calls inside a TEE. | MIT | Developer Preview, launching CC Summit Jun 23 |
| [trace-spec](https://github.com/agentrust-io/trace-spec) | TRACE: Trust Runtime Attestation and Compliance Evidence. Open EAT/JWT attestation standard. | CC BY 4.0 | Private, targeting AAIF submission Jul 2026 |
| [trace-registry](https://github.com/agentrust-io/trace-registry) | Append-only public Merkle registry mirror for TRACE claim anchors. | CC BY 4.0 | Private |
| [trace-tests](https://github.com/agentrust-io/trace-tests) | TRACE compliance test suite for certification. | Apache 2.0 | Private |
| [examples](https://github.com/agentrust-io/examples) | Integration examples across enterprise software vendors, financial services, insurance, healthcare, and sovereign operators. | MIT | Private |

## Principles

These projects are developed in the open. We intend to propose them to recognized open standards bodies; we're inviting the ecosystem to shape them:

- **TRACE**: we intend to submit it as an open standard. The standards home is under evaluation (the Agentic AI Foundation under the Linux Foundation, or CoSAI under OASIS Open); we're inviting founding co-editors now.
- **Agent Manifest**: we intend to submit it through CoSAI under OASIS Open, building on CoSAI Workstream 4.
- **AGT (Agent Governance Toolkit)**: the runtime governance engine this stack builds on, created by Imran Siddique (Chief Platform Officer, OPAQUE) while at Microsoft and released under the MIT license: [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit).

---

## Participate

agentrust-io is built as an open coalition, not a single-vendor stack; we're inviting the ecosystem to shape it before v1.0.

**Founding partners & co-editors.** Take a named seat on the specifications, contribute a hardware-root or platform annex, and help set conformance and governance. The charter is built for co-ownership.
- **Confirmed founding partner:** Technology Innovation Institute (TII).
- **Invited:** Anthropic, OpenAI, Google, Microsoft, NVIDIA, Intel, AMD, Block, and ServiceNow; and the standards homes we're proposing into (AAIF / Linux Foundation, CoSAI / OASIS Open). Co-editor slots are open.

**Contributors & implementers.** You don't need a seat to build with us:
- If you build an agent framework or governance tooling (LangChain, CrewAI, LlamaIndex, Haystack, PydanticAI, Dify, Cisco AI Defense, or anything else in the ecosystem), bring an adapter.
- Bring your platform's attestation root (TEE, GPU, TPM, or managed runtime) as a provider.
- Pilot cMCP at your MCP tool-call boundary; run the conformance suite and tell us where it bends.

**Sovereign & regulated deployments.** The stack is built so agents can run on regulated, proprietary, and sovereign data: hardware-rooted, post-quantum-ready, verifiable without trusting any single operator or jurisdiction. If you're advancing sovereign AI governance, we want you at the table.

To get involved, open a [GitHub Discussion](https://github.com/orgs/agentrust-io/discussions) or contact the maintainers.

---

## Zero-Trust Framework Alignment

agentrust-io is our proposed **reference architecture for zero-trust agentic AI.** The Anthropic *Zero-Trust for AI Agents* eBook (May 2026) adapts NIST SP 800-207 to agentic systems, calling for continuous verification at six layers: agent identity and authentication, supply chain security, MCP and tool security, policy enforcement and governance, multi-agent coordination, and detection and response. This section maps each layer to the agentrust-io stack and names the gaps honestly.

The core argument in that document: traditional perimeter security fails for AI agents because a signed JWT proves *who called an API*, not *what agent made the call*, *which system prompt was active*, *which model version ran*, or *under which policy it was operating*. That is the problem this org was built to solve.

### Agent Identity: closing the attestation gap

The PDF frames agent identity as an authentication problem. The sharper framing: it is an **[attestation gap](https://github.com/agentrust-io/agent-manifest)**. Authentication proves who called. Attestation proves what ran and under what configuration.

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

The signing key is hardware-sealed in a TEE. Hardware provider auto-selects: `SEV-SNP -> TDX -> TPM -> software`. `OPAQUEProvider` is explicit opt-in via `OPAQUE_ATTESTATION_URL` and is never auto-detected. `GPUCCProvider` (NVIDIA H100/H200/Blackwell, CC mode) is planned for v0.2.

A verifier holding the manifest and attestation report can prove, without trusting the operator, that a specific agent ran specific code under specific policy. Agent identity and user identity are cryptographically separate credentials: SPIFFE SVIDs for workload identity, Ed25519 (or post-quantum ML-DSA-65 at Level 3) for the manifest signature.

Four conformance levels address the full deployment range:

| Level | Name | Requirements | Use case |
|---|---|---|---|
| 0 | Software-only | All artifact bindings, Ed25519, transparency log | Development, staging |
| 1 | TEE-attested | + TEE attestation, `audit_key_sealed: true` | Enterprise production, EU AI Act Art. 15 |
| 2 | Full stack | + All 10 artifacts, HITL approvals, Phase 2 cMCP, 180-day log retention | Regulated industries, DORA Art. 9 |
| 3 | Post-quantum | + ML-DSA-65 (NIST FIPS 204), ML-KEM-768, SHAKE-256 | Sovereign, classified, long-horizon financial |

### Supply Chain Security

Agent Manifest artifact #9 binds container digest, SLSA provenance level, and SBOMs into the signed manifest. A supply chain attack that swaps the container invalidates the TEE measurement, which invalidates the manifest signature. Hardware attestation makes this structurally detectable, not just policy-prohibited.

**TRACE** includes `build_provenance` as a first-class field (SLSA Provenance v1.0) and an `AIBOM` field (SPDX 3.0 / CycloneDX 1.7) capturing the model weights digest. The model component inventory is bound into a hardware-attested record and cannot be swapped after signing.

Every agentrust-io repository carries OpenSSF Scorecard badges, CodeQL SAST, Dependabot, pip-audit on every PR, and bandit security linting. The tooling in this org practices what it recommends.

### MCP and Tool Security

The Anthropic eBook cites specific MCP attacks: the Invariant Labs GitHub compromise via MCP integration, the Zenity AgentFlayer 0-click attack, the Postmark MCP npm backdoor. These are not hypothetical threats.

**cMCP (Confidential MCP Runtime)** is a direct response. Every MCP tool call is intercepted, evaluated against a Cedar policy bundle, and enforced by a policy engine running inside a TEE. The policy bundle hash is measured into the hardware attestation report before any code runs.

| Threat | Software governance | cMCP |
|---|---|---|
| Admin replaces Cedar policy on disk | Undetected: hash chain runs in compromised OS | Policy hash measured by hardware before code runs |
| Supply chain CVE flips allow/deny signal | Undetected: evaluator in attacker's address space | Evaluator in isolated enclave memory |
| Admin regenerates audit log post-breach | Undetected: any party with signing key can reconstruct | Signing key hardware-sealed, new valid signatures structurally impossible |

Every cMCP tool call produces a GatewayClaim (a TRACE Profile) containing the runtime platform measurement, policy bundle hash, and hardware-sealed confirmation key. Tool call authorization is independently auditable and tamper-evident.

### Policy Enforcement and Governance

The eBook calls for policy at four layers (model, agent, tool, request) with fleet management, centralized policy management, audit logging, and compliance monitoring.

**cMCP** handles tool-level and request-level policy with Cedar inside a TEE. Cedar is designed for per-request evaluation; this is not a batch audit but runtime enforcement on every call.

**[TRACE](https://github.com/agentrust-io/trace-spec)** defines the governance record format: what a compliance artifact should contain, how it is cryptographically bound, and how it anchors in a transparency log. TRACE composes existing standards rather than replacing them:

| Primitive | Role in TRACE |
|---|---|
| RATS / EAT (RFC 9711) | Wire envelope and claim model |
| SLSA Provenance v1.0 | Build-time provenance |
| SPIFFE SVID | Workload identity |
| SCITT | Append-only transparency anchoring |
| EAR (draft-ietf-rats-ar4si) | Verifier appraisal output |
| MCP / A2A | Agent tool-call transcript surface |
| AIBOM (SPDX 3.0 / CycloneDX 1.7) | Model component inventory |

**[TRACE Registry](https://github.com/agentrust-io/trace-registry)** is the public append-only Merkle registry of TRACE claim anchors. The GitHub mirror exists so any party can verify anchors independently. Git's immutable commit history is the tamper-evident proof.

**AGT (Agent Governance Toolkit)** ([microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit), created by Imran Siddique (Chief Platform Officer, OPAQUE) while at Microsoft and released under the MIT license) provides the runtime governance layer: trust score decay (a score at deployment is meaningless six months later), the VADP delegation protocol (scope-narrowing agent-to-agent delegation with verifiable credentials), and a fleet daemon for multi-agent orchestration.

### Multi-Agent Coordination Governance

The prize is obvious: connect agents directly to your most sensitive data and systems: the regulated records, the proprietary models, the production controls, because that is where the value of AI actually lives. It is also exactly what you cannot risk today.

If you have built and run agents, you already know two things to be true: they **drift**, and they **leak**. Anyone who says otherwise hasn't shipped one. Take the best case: a *good* agent leaks only **1% of the time** and watch what a fleet does to it. The odds that **at least one** of `n` agents leaks is one minus the odds they *all* stay clean: `1 - (1 - 0.01)^n`:

| Agents | Chance at least one leaks |
|---|---|
| 1 | 1% |
| 100 | **63%** |
| 1,000 | **99.99% — effectively certain** |

Multi-agent architecture compounds it: an orchestrator delegates to sub-agents, scope widens down the chain, and no one can prove which agent did what.

This is the layer the **Anthropic *Zero-Trust for AI Agents*** framework calls for: authentication of agent-to-agent communication, RBAC for agent hierarchies, consensus for high-stakes decisions; and where the stack enforces it:

- **Agent Manifest artifact #8 (A2A delegation)** binds the full agent-to-agent trust chain into the signed manifest. A delegated scope can never exceed the orchestrator's own attested permissions; orchestrator spoofing and scope laundering are structurally prevented. AGT's VADP supplies the mechanism: scope-narrowing delegation with verifiable credentials.
- **TRACE** records each agent's actions as a hashed, counted `tool_transcript`, so the full interaction graph of a multi-agent run can be reconstructed and proven after the fact.

Once every agent carries attested proof of *what it is* and emits verifiable evidence of *what it did*. 

### Detection and Response

**Current coverage:** TRACE provides the immutable audit chain from which anomalies could be detected. AGT's GovernanceEventSink SPI is a pluggable event sink, so anomaly detection can be wired in without vendor coupling. Trust score decay in AGT is a passive form of behavioral posture management.

**Gaps:** There is no dedicated behavioral anomaly detection or agent quarantine tooling in the current repos. Automated response (quarantine procedures, rollback) is on the AGT roadmap but not shipped. The eBook's recommendation for sleeper agent detection through behavioral analysis has no direct counterpart here yet. TRACE provides the audit foundation; detection is not included.

---

## Standards Coverage

| Standard | Agent Manifest | TRACE | cMCP | AGT |
|---|---|---|---|---|
| NIST SP 800-207 (Zero Trust) | Identity, policy layers | Governance records | Tool-level ZT enforcement | Fleet policy, observability |
| OWASP Agentic AI Top 10 (2026) | Addresses all 10 ASI categories with deterministic, attestable controls | Evidence chain | MCP call enforcement | Runtime governance |
| NIST AI RMF 1.0 | GOVERN, MAP, MEASURE, MANAGE | MEASURE, MANAGE | GOVERN (tool policy) | Full RMF lifecycle |
| EU AI Act Art. 13-15 | Transparency (Art. 13), HITL (Art. 14), supports Art. 15 (cybersecurity) at Level 1 | Compliance evidence | Enforcement evidence | Governance lifecycle |
| DORA Art. 9 | Attestation + 180-day log retention (Level 2) | Immutable audit chain | Per-call audit records | Risk management |
| MITRE ATL | Supply chain, model identity, prompt constraints | Verifiable evidence | Policy enforcement | Detection foundation |
| SLSA | Level 2 build provenance | `build_provenance` field | SLSA-aware claims | Supply chain |
| CoSAI WS1 | Secure-by-Design Principles, MCP Security Taxonomy | | MCP enforcement | WS4 governance |

---

## Community

- Questions and discussion: [GitHub Discussions](https://github.com/orgs/agentrust-io/discussions)
- Security issues: see [SECURITY.md](SECURITY.md)
- Contributing: see [CONTRIBUTING.md](CONTRIBUTING.md)
