# TAI-Protocol

**Task–Architect Interchange · v0.2.0-rc.1**

A document-constrained handoff protocol for work across humans, agents, models, and tools.

> Replace the participants. Preserve the task, the decisions, and the artifacts.

TAI defines the contract between roles, not a required engine or orchestration service.
A chat, issue, email, API request, or event can initiate work. Before execution, an
authorized issuer turns that input into a durable Task document. Reports, decisions,
and artifact references survive the sessions that produced them.

```text
Chat / Issue / Email / API / Event / Agent / Human
                         |
              Authorized Task document
                         |
         Architect -> Supervisor -> Worker
              ^                       |
              +--- Report + Evidence -+
                         |
              Decision / Gate / State
                         |
                 Next Task or Stop
```

All three roles are replaceable. A role can be performed by a human, an LLM-backed
agent, or an appropriately capable program. One implementation can host multiple
roles, but their authority and records stay distinct. Fully agent-connected workflows
are allowed; bypassing documents or approval policy is not.

## What changed in 0.2

- **Engine and source-channel independence:** Claude Code is an adapter, not the protocol.
- **Document-constrained execution:** input becomes an issued Task before side effects;
  results and approvals are recorded before the next handoff.
- **Replaceable Architect, Supervisor, and Worker:** durable state supports a fresh
  session; conversation history is not the sole source of truth.
- **Transport is not authority:** manual and automated delivery obey the same gates.
- **Input-side assets:** archive each issued Task revision without rewriting its bytes.

Long-lived projects do not require long-lived prompts. Cost reduction is a design
objective, not a guarantee: retrieval, state maintenance, verification, and rework
also cost time and tokens.

## Start here

| Document | Purpose |
|---|---|
| [Concept](docs/concept.md) | Why documents, replaceable roles, and retained human authority |
| [Core protocol](docs/protocol.md) | Normative contract, lifecycle, gates, recovery, security |
| [Operations](docs/operations.md) | Archiving, evidence, integrity, Git and shell procedures |
| [Examples](docs/examples.md) | Manual, mixed-engine, and agent-connected handoffs |
| [Migration](docs/migration-v0.2.md) | Explicit changes from v0.1.0 and compatibility limits |
| [Changelog](CHANGELOG.md) | Release-candidate scope and known limitations |

The normative specification and operational guides are currently in Japanese.

## Minimal adoption — no Claude account required

1. Use [templates/task.md](templates/task.md) to document objective, scope, authority,
   acceptance criteria, source, and stop conditions. Persist it before dispatch.
2. Give a capable Worker only the Task and its explicitly referenced materials.
   Record results with [templates/report.md](templates/report.md).
3. Check evidence, record the decision and current state using
   [templates/state.md](templates/state.md), then issue a new Task or stop.

A filesystem, versioned repository, or other durable document store can implement
this contract. The templates are not an autonomous scheduler or an API integration.

## Existing Claude Code / Git workflow

The `.ai/task.md` and `.ai/report.md` windows, their existing Git frontmatter,
`claude/architect` and `claude/T-*` carrier paths, notification format, and report
return path remain in place. The bundled shell bridge is unchanged in this release.

For a new installation, copy:

```text
docs/                         core and operating rules
templates/                    engine-neutral document templates
.gitattributes                preserve archived Task bytes in Git
scripts/task_archive.py       optional Python 3.9+ archive helper
.claude/skills/tai/            Claude Code / Git adapter and existing bridge
.ai/                          placeholder windows and blank configuration
```

Start the Supervisor with: “Read `.claude/skills/tai/SKILL.md` and take the Supervisor
role.” Configure `SUPERVISOR_SESSION` locally; do not commit live session credentials.
Follow [transport.md](.claude/skills/tai/references/transport.md) before running the
bridge. Use `--no-autostart` whenever Task Start requires confirmation or prerequisites
have not been checked. Automation is not enabled by upgrading the documentation.

At Gate, archive the issued Task **before** resetting the windows:

```bash
python scripts/task_archive.py
```

The helper only copies and verifies. It never resets files, approves work, commits,
pushes, or runs an agent. Archive creation and window reset must be staged in the
same cleanup commit by the authorized operator. See [operations](docs/operations.md).

## Validation

```bash
python -m unittest discover -s tests -v
```

Tests cover archive integrity, overwrite refusal, malformed inputs, and a temporary
Git repository's archive-plus-reset commit. They do not certify external engines,
cloud sessions, permissions, or end-to-end bridge operation.

## Status and license

Experimental **release candidate**, not a claim of production-ready multi-engine
orchestration. Wire compatibility is retained; philosophy and some operating rules
change explicitly. No automatic migration, release, or deployment is implied.

MIT. Part of the StateToolsLab protocol family: SAI concerns what to touch, SPP how
to touch it safely, and TAI who decides and how work changes hands.

---

# TAI-Protocol（日本語）

**エンジンや担当者ではなく、文書を接点に仕事を引き継ぐプロトコル。**

入口はチャットでも、Issueでも、メールでも、APIでも、別のエージェントでもよい。
ただし、実行前に権限を確認し、目的・範囲・受入条件・停止条件をTask文書へ確定する。
実行後もReport・判断・成果物の参照を残し、次の担当者が読み直せる状態にする。

Architect（司令塔）、Supervisor（現場監督）、Worker（実行者）は役割であり、
固定のモデル・サービス・セッションではない。すべてをエージェントで接続してもよい。
**自動化してよいのは接続であって、文書と権限の境界を消してよいわけではない。**

永続するのは、発行Task、採用した判断、現在状態、成果物、検証根拠。
会話全文や同じAIの記憶を必須にしないため、司令塔・現場監督・Workerを交代できる。
その際も、未完了処理と外部への副作用を照合してから再開する。

v0.1.0の「手動2回」は引き続き選べる運用として残す。v0.2では、それを全利用者への
義務とせず、手動・半自動・全自動を同じ文書規約と承認ポリシーの下に置く。
既存ブリッジを汎用化した実装が完成したという意味ではない。

導入・移行・制約は上の各文書を参照。現行案件へはStable Pointで段階的に適用する。
