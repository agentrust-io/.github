# agentrust-io — Technical One-Pager

> **The open, verifiable trust layer for agentic AI.**
> Developer preview / open RFC · public launch at the **Confidential Computing Summit, June 23 2026** · [github.com/agentrust-io](https://github.com/agentrust-io)

## The attestation gap

Anthropic's [*Zero-Trust for AI Agents*](https://claude.com/blog/zero-trust-for-ai-agents) (May 2026) named the problem and pointed the direction: agent identity has to be **cryptographically rooted** — a label is trivial to forge — and perimeter tokens alone can't secure an autonomous agent. Here's the gap that leaves: a signed JWT proves *who* called an API, not *what* agent made the call, *which* system prompt was active, *which* model version ran, or *under which* policy. **agentrust-io is the open implementation built to close it.** It lets agents run on regulated, proprietary, and sovereign data with evidence the builder can verify directly — and any auditor, customer, or regulator can independently confirm, without trusting the operator. It replaces "guardrails that will *probably* catch it, and observability that will *probably* flag it after the fact" with independently verifiable proof.

## Built on proven foundations

agentrust-io stands on two things that already exist and work.

**1 · Policy — the Agent Governance Toolkit (AGT).** Created by Imran Siddique (now OPAQUE's Chief Platform Officer) at Microsoft and open-sourced under MIT: 4,250+ stars, 590+ forks since its April 2026 public launch; 10/10 OWASP Agentic Top 10 coverage; ships trust-score decay, scope-chain delegation (monotonic narrowing), and a multi-agent fleet daemon; now being considered by AAIF for standardization.

**2 · Enforcement — a confidential runtime, pluggable by design.** The policy bundle is sealed and measured inside a TEE on the confidential-computing silicon you already operate — Intel TDX, AMD SEV-SNP, NVIDIA CC, or TPM. The OPAQUE Confidential AI is the hardware-rooted, managed reference implementation; an operator can bring its own.

agentrust-io doesn't reinvent governance — it makes AGT's policy **provable** by binding it to a hardware-attested confidential runtime. A policy decision isn't just enforced; it's evidenced.

## How it works

Three components, composing standards you already trust (MCP, A2A, SPIFFE, SLSA, Cedar, RATS/EAT; aligned to NIST SP 800-207):

| Component | Role |
|---|---|
| **Agent Manifest** — deploy-time integrity | The agent's complete signed definition — far more than identity. Binds the 10 artifacts (system prompt, policy bundle, tool manifest, model identity, RAG corpus, memory baseline, decision trace, A2A delegation, supply-chain provenance, HITL approvals) into one hardware-attestable document, so a modified agent can't pass as the one you approved. |
| **cMCP** — Confidential MCP Runtime | Runs inside the confidential runtime. Every MCP tool call is evaluated against a Cedar policy bundle inside a TEE; the policy-bundle hash is measured into the hardware attestation report before any code runs. A swapped policy or a CVE in the evaluator is structurally detectable — not just prohibited. |
| **TRACE** — the portable record | The signed envelope that binds every other standard's evidence into one verifiable record (see below). |

The stack runs at one of four conformance levels (L0–L3): software-only → TEE-attested → full-stack / regulated (DORA, EU AI Act) → post-quantum (ML-DSA-65) for sovereign and classified deployments.

## TRACE — the envelope that ties it together

TRACE (Trust Runtime Attestation and Compliance Evidence) is the portable governance record at the center of the stack: a single attestation envelope (EAT/JWT, per the IETF RATS model) that **carries the other standards' evidence** — build provenance (SLSA), workload identity (SPIFFE SVID), model inventory (AIBOM), a cryptographic bill of materials (CBOM — the crypto libraries and algorithms in use), and the agent's tool-call transcript — cryptographically bound and anchored in an append-only transparency log. One verifiable record that proves **what an agent was** and **what it did**, reconstructable after the fact and confirmable by a party with no reason to trust the operator. Open spec; we intend to submit it to AAIF.

## About OPAQUE

OPAQUE is the Confidential AI company. Born from UC Berkeley's RISELab (now the Sky Compute Lab), OPAQUE lets organizations run AI models, agents, and workflows on their most sensitive data with hardware-rooted isolation and verifiable evidence that approved governance policies were enforced. Founded by Dr. Ion Stoica (co-founder of Databricks; co-director, UC Berkeley Sky Compute Lab), Dr. Raluca Ada Popa (ACM Grace Hopper Award winner; Senior Staff Research Scientist at Google DeepMind, where she leads AGI security research), and Rishabh Poddar (CTO). Aaron Fulkerson is Chief Executive Officer, and Imran Siddique, creator of the open-source Agent Governance Toolkit (AGT), is Chief Platform Officer. OPAQUE created the Confidential Computing Summit, now co-hosted with the Linux Foundation.

---

Questions or to get involved: [GitHub Discussions](https://github.com/orgs/agentrust-io/discussions) · back to the [org overview](README.md).
