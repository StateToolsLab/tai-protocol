# TAI — Concept and Design Philosophy

**Task–Architect Interchange.** A handoff protocol for AI-delegated development that automates the transport of work — and deliberately refuses to automate the exchange itself.

---

## 1. The Thesis

Delegating implementation to AI agents creates a paradox: the more completely you delegate, the less you understand what was built. Fully autonomous pipelines optimize away the moments where a human absorbs what is happening — and with them, the ability to steer, audit, and take responsibility for the result.

TAI resolves the paradox by drawing a hard line through the loop. Everything mechanical is automated: file transport, branch plumbing, notifications, conformance checks. Two actions are deliberately kept in human hands:

1. **Handing the task down** — the user pastes the Architect's `task.md` to the Supervisor.
2. **Handing the report up** — the user carries the Worker's `report.md` back to the Architect.

These are not gaps waiting for a better platform API. They are the protocol's load-bearing feature. Each handoff is the moment where the decision-maker sees, in full, what is being ordered and what came back. Remove them, and delegation degrades into dispatch.

> **The protocol automates the transport, never the interchange.**

## 2. Three Layers

```
USER ⇄ Architect (chat threads) ── task.md ──▶ Supervisor (cloud session) ──▶ Worker
                 ▲                                                              │
                 └────────────────────────── report.md ─────────────────────────┘
```

**Architect — the control tower.** The Architect is not an agent or a service; it is the user's chat threads themselves. Design intent, past decisions, the living tree of branches and stable points — all of it lives in conversation. The Architect writes `task.md`, evaluates `report.md`, and decides when to stop and ask the human. It cannot write to the repository, and that inability is purifying: a layer that can only think and instruct never quietly becomes an executor.

**Supervisor — the hands.** A Claude Code cloud session that performs mechanical repository work: pushing the task onto its carrier branch, running conformance checks on incoming reports (file scope, commit separation, frontmatter, a clean main). It does not judge, does not evaluate, does not draft tasks. The moment a supervisor starts having opinions, the architecture has silently duplicated its brain — the single most guarded failure mode in this design.

**Worker — the implementer.** Stateless by design. `task.md` is its entire input; `report.md` is its entire output. Context that must survive across tasks travels through the Architect, not through worker memory.

The separation of concerns, in one line each:

| Element | Role |
|---|---|
| Thread | intelligence / state |
| File (`task.md` / `report.md`) | message |
| Git | carrier |
| Supervisor | hands |
| Bridge | transport — a one-line "it arrived" notification, never the content |

## 3. The Name

**TAI** is the Task–Architect Interchange: tasks flow down, reports flow up, and the protocol exists to keep that exchange honest.

The name is also 泰 — hexagram 11 of the I Ching. Its figure places Earth (☷) above and Heaven (☰) below: the reverse of their "proper" stations. Precisely because each is out of place, Heaven's force rises, Earth's force descends, and the two streams must pass through one another. The classical commentary reads 上下交而其志同 — *"the upper and the lower interchange, and their wills become one."* The acronym happens to preserve the hexagram's word order: **T**ask (earth, the ground of work) before **A**rchitect (heaven, the seat of intent).

泰 has a shadow twin: 否 (hexagram 12), Heaven above and Earth below. Everything in its correct place, nothing exchanged, all passage blocked. A fully automated pipeline — reports flowing into the control tower without a human hand between them — is 否: correct-looking, efficient, and closed. The protocol's final rule (see §6) forbids building it.

*The project's development codename was **pastel**, after the record-keeping protagonist of Fortune Quest — a nod to a system whose whole job is keeping the written record of tasks and reports.*

## 4. What Exists, and What Is New

None of TAI's raw ingredients are novel, and the protocol does not pretend otherwise:

- **Hierarchical manager–worker agents** — a planner agent assigning implementation tasks to executor agents — are a documented, mainstream pattern.
- **File-based human-in-the-loop pauses** — agents halting on a designated file or approval gate — are standard practice.
- **In-repo workflow contracts** — versioning agent policy as Markdown alongside the code — are an emerging convention.

What is new is the **placement** and the **prohibitions**:

1. **The Architect is the chat.** Not an orchestrator process, not a long-running agent — the user's own threaded conversations are the top layer. The system's memory is the dialogue itself.
2. **A scribe layer that is forbidden to think.** The Supervisor's charter is a closed list of mechanical duties. Judgment anywhere below the Architect is a protocol violation, not a feature request.
3. **The manual handoffs are protected.** Automating the two remaining human actions is explicitly prohibited, even where it is technically possible. HITL practice treats human touchpoints as review checkpoints; TAI treats two of them as the product.

The protocol is also **model-agnostic at the top**. The Architect role has been exercised end-to-end by both Claude and ChatGPT: full task cycles with correct `task.md` formatting, consistent stopping at `next_task: confirm` across consecutive rounds, correct discrimination between commit and push gates, and detection of revision-mismatched reports as "not yet arrived." The Architect is a role defined by the protocol, not a capability of one vendor's model.

## 5. Measured Constraints (as of 2026-08)

TAI's shape is partly the product of platform behavior, verified by experiment rather than assumed:

| Observation | Design consequence |
|---|---|
| Cloud session VMs carry no chat credentials; a session cannot message another session | The Bridge (notification transport) runs locally |
| Chat cannot write to the repository (no working write path from the thread side) | A scribe layer — the Supervisor — is required at all |
| Cloud sessions can push only to `claude/*` branches; main is rejected | Architect-originated tasks travel via a dedicated carrier branch, fast-forwarded into main locally |
| An expired cloud session revives on CLI message delivery, without UI interaction | The Supervisor needs no keep-alive; it can sleep between handoffs |

These are observations of a moving platform, dated deliberately. If the platform changes, the affected choices should be re-derived from the thesis — not preserved out of habit.

## 6. What TAI Is Not

- **Not an orchestrator.** There is no central engine dispatching agents. The Architect converses; everything else reacts.
- **Not a state store.** The thread tree is never mirrored into a database. The "current position" map inside `task.md` is a projection of the Architect's context, not a source to restore from.
- **Not a content-aware pipe.** The Bridge sends a single line — task id, revision, branch, commit — and never the report body. It reads frontmatter, not meaning.
- **Not a place for a second brain.** The Supervisor checks conformance and moves files. Evaluation, recommendation, and task drafting belong to the Architect alone.
- **Not to be completed.** The two manual handoffs will not be automated by browser automation, unofficial APIs, or any future convenience. If the exchange ever leaves human hands, the protocol has not been finished — it has been broken.

---

*TAI is part of the StateToolsLab protocol family. Where [SAI](https://github.com/StateToolsLab/sai-protocol) fixes **what to touch** and SPP governs **how to touch it safely**, TAI defines **who decides, and how the work changes hands.***
