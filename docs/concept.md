# TAI — Concept and Design Philosophy

**Task–Architect Interchange · 0.2**

> Long-lived project. Bounded context. Replaceable participants. Durable artifacts.

## 1. The boundary is a document, not a session

TAI's unit of interchange is an issued Task and its returned Report. A role's current
implementation is temporary; authorized intent and accepted results must survive it.
The protocol does not require participants to share a vendor, conversation, or memory.

A document is not merely a transcript generated after work finishes. It constrains
execution beforehand: what is requested, what is allowed, what counts as acceptance,
and where execution must stop. Automated messages can carry document bytes or durable
references. They cannot silently replace this contract with private agent context.

## 2. Separate three choices

**Governance:** who may authorize, accept, change scope, or approve an external effect.
**Coordination:** who issues tasks, checks conformance, tracks dependencies, and routes work.
**Execution:** which person, engine, tool, or service performs a bounded task.

TAI standardizes their boundaries without shipping a required central orchestrator.
A single program may implement them, or several agents may cooperate. The logical
roles and their allowed transitions must remain visible in the record.

## 3. Replace the whole chain

The Architect frames tasks and evaluates results. The Supervisor transports documents
and checks compliance. The Worker executes within the Task. Any of these may be
replaced, including the Architect and Supervisor.

Replacement requires a durable handover: active task revisions, accepted decisions,
authority, artifact versions, outstanding gates, and in-flight execution status.
The successor does not need a predecessor's hidden reasoning or entire conversation.
It does need recorded rationale sufficient to understand which decisions still apply.

“Stateless” here means **no correctness dependency on private session memory**. It does
not mean an agent has no working context, nor that a running process can safely be
killed before its state and external effects have been reconciled.

## 4. Preserve agency, not a particular UI gesture

v0.1.0 protected two manual transfers: Task down, Report up. That remains a useful
manual profile. v0.2 preserves the underlying authority boundary rather than requiring
copy-and-paste in every deployment.

An agent-connected profile can dispatch and return automatically within an explicit
policy. A notification is not approval. Neither automation nor a Task received from
an external channel grants additional authority. Scope changes, required human
preferences, and destructive or public actions stop according to policy.

Human intervention remains possible; it need not be a mandatory transport step.

## 5. Input and output are reusable assets

An archive records the actual issued Task, not a reconstructed summary of the request.
Together, Tasks, Reports, decisions, and artifacts answer what was requested, what
happened, what was accepted, and what can be reused.

Archival does not by itself make a Task a safe template. Extract reusable patterns
only after reviewing the outcome, removing project-specific secrets, and recording
applicability and limitations. Failed and cancelled Tasks remain history, not approved
recipes. Storage growth is not a reason to load every archived document into a prompt.

## 6. Economy is a measurable objective

Persist documents and load only the current state plus relevant evidence. Stable
Points offer a useful boundary for closing work, committing decisions, and rebuilding
context. This can avoid repeatedly replaying an entire conversation, but it also adds
state-maintenance and retrieval work. Measure cost per accepted outcome, human review
time, verification cost, latency, and rework; do not promise automatic token savings.

## 7. What TAI does not require

No specific LLM, source channel, database, message bus, or always-on controller is
required. Git and Claude Code remain one concrete adapter. TAI is not a substitute
for permissions, sandboxing, transaction management, or evaluation of actual results.
An all-agent topology is permitted, but no topology is sufficient for conformance.

## 8. Name and continuity

The name remains **Task–Architect Interchange**. The change is not a new brand but a
broader contract: participants can change while the work remains legible.
The original public baseline is commit
`28a632ef89562519d9c82260c75f94658a30cde9` (v0.1.0). Its platform observations were dated
2026-08. They are historical adapter observations, not permanent Core restrictions.
See [migration-v0.2.md](migration-v0.2.md) for the explicit changes.

日本語の規範仕様: [protocol.md](protocol.md)。
