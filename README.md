# TAI-Protocol

**Task–Architect Interchange**

A handoff protocol for AI-delegated development where the architect stays in the chat, the supervisor stays mechanical, and the handoff stays in human hands.

> The protocol automates the transport, never the interchange.

日本語は下にあります / Japanese follows below.

---

## How It Works

```
USER ⇄ Architect (chat threads)
         │  writes task.md          ← you paste it down   【manual action 1】
         ▼
      Supervisor (Claude Code cloud session)
         │  pushes to carrier branch; local bridge fast-forwards main
         ▼
      Worker (Claude Code, headless)
         │  implements; writes report.md → claude/T-xxx
         ▼
      Bridge (local, one-line notification) → Supervisor conformance check
         │                                   ← you carry the report up 【manual action 2】
         ▼
USER ⇄ Architect (evaluates, decides, writes the next task)
```

Three layers, strictly separated:

- **Architect** — your chat threads. Designs, judges, holds the thread tree. Cannot write to the repository.
- **Supervisor** — a cloud Code session. Mechanical repository work and conformance checks only. Never judges.
- **Worker** — stateless implementer. `task.md` in, `report.md` out.

The two manual actions are the protocol's core feature, not a limitation. See [docs/concept.md](docs/concept.md) for why.

## Getting Started

**What to copy into your repository:**

```
.claude/skills/tai/     the skill: SKILL.md, references/, templates/, scripts/
.ai/                    message directory: task.md / report.md placeholders,
                        config.yaml (blank), .gitignore
```

**Claude-side setup:**

1. Create a Claude project for your repository. Add the repo to project knowledge via the GitHub integration (this lets the Architect read the protocol files and your code).
2. Start a cloud Code session on the repository (branch: main) at claude.ai/code. This session is your Supervisor. Send it one line: *"Read `.claude/skills/tai/SKILL.md` and take the Supervisor role."*
3. Record the session ID: set the `SUPERVISOR_SESSION` environment variable on the machine that runs the bridge (takes priority), or fill `supervisor_session` in `.ai/config.yaml`.

**Run the bridge** (local, one process per repository, from a terminal — never from inside a Code session):

```bash
bash .claude/skills/tai/scripts/bridge-poll.sh 30        # poll every 30s
bash .claude/skills/tai/scripts/bridge-poll.sh 30 --no-autostart   # notify only; you start Workers manually
```

On macOS, run it under `caffeinate -i` to prevent sleep. The bridge fast-forwards Architect tasks into main, starts headless Workers, and sends one-line arrival notifications. It never reads report contents.

Then open a chat thread, have the Architect write your first `task.md`, and paste it to the Supervisor. The loop is running.

Note: the skill body (SKILL.md, references, templates) is currently in Japanese. The protocol itself is language-agnostic — an English translation is planned.

## Things You Will Hit First

**Headless Workers cannot edit `.claude/`.** Tasks that touch the skill's own files (or anything under `.claude/`) must run in an interactive Worker — a session where you can answer the edit-approval prompts. Mark such tasks explicitly; a headless Worker receiving one should return a blocked report immediately.

**Integrate main before the next task.** One cycle ends only when the task branch is merged to local main (`--no-ff`), pushed to origin, and `.ai/task.md` / `report.md` are reset to placeholders. Skipping the reset works for a while and then quietly poisons a future cycle — treat the three steps as one routine. The next task must not be issued until origin/main reflects the last one.

**Windows notes.** Set LF normalization via `.gitattributes` (`core.autocrlf=true` is the primary hazard). Run the scripts from Git Bash, not PowerShell — PowerShell lacks `sed` and `&&` chaining. When writing your own task instructions, label PowerShell and Git Bash commands distinctly.

## Model-Agnostic Architect

The Architect is a role, not a model. It has been exercised end-to-end by both Claude and ChatGPT: correct `task.md` formatting, consistent stops at `next_task: confirm`, correct commit/push gate discrimination, and detection of revision-mismatched reports. Any chat-side LLM that can follow the protocol can hold the seat.

## What TAI Is Not

- Not an orchestrator — there is no central engine; the Architect converses, everything else reacts.
- Not a state store — the thread tree is never mirrored into a database.
- Not a content-aware pipe — the bridge sends one line, never the report body.
- Not to be completed — the two manual handoffs will not be automated. Ever.

Full version in [docs/concept.md](docs/concept.md).

## Repository Contents

```
tai-protocol/
├── README.md
├── LICENSE                      MIT
├── docs/
│   └── concept.md               Design philosophy: thesis, layers, the name, constraints
├── .claude/
│   └── skills/
│       └── tai/
│           ├── SKILL.md         Daily rules + Supervisor charter
│           ├── references/
│           │   ├── protocol.md  Full handoff protocol (gates, arbitration, cycle order)
│           │   └── transport.md Carrier-branch and bridge mechanics
│           ├── templates/
│           │   ├── task.md
│           │   └── report.md
│           └── scripts/
│               ├── notify-architect.sh   One-line notification sender
│               └── bridge-poll.sh        Local polling bridge
└── .ai/
    ├── task.md                  Placeholder
    ├── report.md                Placeholder
    ├── config.yaml              supervisor_session (blank; env var takes priority)
    └── .gitignore               Excludes .bridge-state
```

*Naming note: the skill directory is `tai`; the repository is `tai-protocol`.*

## Related Protocols

Part of the StateToolsLab protocol family:

- [SAI](https://github.com/StateToolsLab/sai-protocol) — **what to touch**: stable structural anchor IDs
- SPP — **how to touch it safely**: structured patch process
- TAI — **who decides, and how the work changes hands**

## Status

Experimental. The protocol may change. Constraints in `docs/concept.md` §5 are dated platform observations (2026-08) and will be re-derived if the platform moves.

## License

MIT

---
---

# TAI-Protocol（日本語）

**Task–Architect Interchange**

AI に実装を委譲する開発のための handoff プロトコル。Architect はチャットに、Supervisor は機械的作業に、そして handoff は人間の手に留まる。

> このプロトコルが自動化するのは運搬であって、交わりではない。

---

## 仕組み

```
USER ⇄ Architect（チャットのスレッド群）
         │  task.md を書く         ← あなたが貼って渡す 【手動アクション 1】
         ▼
      Supervisor（Claude Code クラウドセッション）
         │  運搬ブランチへ push。ローカルのブリッジが main へ fast-forward
         ▼
      Worker（Claude Code、headless）
         │  実装し、report.md を claude/T-xxx へ
         ▼
      Bridge（ローカル、1行通知）→ Supervisor が規約適合チェック
         │                        ← あなたが report を持ち帰る 【手動アクション 2】
         ▼
USER ⇄ Architect（評価・判断・次の task）
```

三層は厳密に分離されます。

- **Architect** — あなたのチャットスレッド群。設計・判断・Thread Tree の保持。リポジトリには書けない
- **Supervisor** — クラウド Code セッション。機械的なリポジトリ作業と規約チェックのみ。判断しない
- **Worker** — 文脈を持たない実装者。`task.md` が入力のすべて、`report.md` が出力のすべて

手動2アクションは制約ではなく、このプロトコルの中核機能です。理由は [docs/concept.md](docs/concept.md) に。

## 導入

**リポジトリにコピーするもの:**

```
.claude/skills/tai/     skill 本体: SKILL.md、references/、templates/、scripts/
.ai/                    メッセージ置き場: task.md / report.md のプレースホルダ、
                        config.yaml（空欄）、.gitignore
```

**Claude 側のセットアップ:**

1. リポジトリ用の Claude プロジェクトを作成し、GitHub 連携でリポジトリをプロジェクト知識に追加する（Architect が規約ファイルとコードを読めるようにする）
2. claude.ai/code でリポジトリ（ブランチ: main）のクラウド Code セッションを開始する。これが Supervisor。最初に一行送る: *「`.claude/skills/tai/SKILL.md` を読み、Supervisor の役割に就くこと」*
3. セッション ID を記録する。ブリッジを動かすマシンで環境変数 `SUPERVISOR_SESSION` を設定する（こちらが優先）か、`.ai/config.yaml` の `supervisor_session` に記入する

**ブリッジの起動**（ローカル、リポジトリごとに1プロセス、ターミナルから。Code セッション内から起動しないこと）:

```bash
bash .claude/skills/tai/scripts/bridge-poll.sh 30        # 30秒間隔でポーリング
bash .claude/skills/tai/scripts/bridge-poll.sh 30 --no-autostart   # 通知のみ。Worker は手動起動
```

macOS では `caffeinate -i` 配下で実行してスリープを防ぐこと。ブリッジは Architect の task を main へ fast-forward し、headless Worker を起動し、到着を1行で通知します。report の中身は読みません。

あとはチャットのスレッドを開き、Architect に最初の `task.md` を書かせて、Supervisor に貼るだけです。ループが回り始めます。

注: skill 本体(SKILL.md / references / templates)は現在日本語です。プロトコル自体は言語非依存です。

## 最初に踏む石

**headless Worker は `.claude/` を編集できません。** skill 自身のファイル（および `.claude/` 配下すべて）に触れる task は、編集承認プロンプトに応答できる対話モードの Worker で実行してください。該当 task には明示のマークを付けること。headless Worker がこれを受け取った場合は、着手前に即座に blocked report を返すのが規約です。

**次の task の前に main を取り込むこと。** 1サイクルの終わりは、task ブランチのローカル main への merge（`--no-ff`）、origin への push、そして `.ai/task.md` / `report.md` のプレースホルダ戻しが揃った時点です。プレースホルダ戻しの省略はしばらく動いてしまい、後のサイクルを静かに汚染します——3手順を1つの定型として扱ってください。origin/main に前の task が反映されるまで、次の task を発行してはいけません。

**Windows の要点。** `.gitattributes` で LF 正規化を設定すること（`core.autocrlf=true` が最大の危険源）。スクリプトは PowerShell ではなく Git Bash から実行すること——PowerShell には `sed` も `&&` 連結もありません。自分で task の指示を書く際は、PowerShell 用と Git Bash 用のコマンドを明確に区別して表記してください。

## Architect はモデル非依存

Architect はモデルではなく役割です。Claude と ChatGPT の双方で一連の往復を完遂済み: `task.md` の書式遵守、`next_task: confirm` での一貫した停止、commit / push Gate の正確な使い分け、revision 不一致 report の検出まで確認されています。プロトコルに従えるチャット側 LLM であれば、この席に就けます。

## TAI ではないもの

- オーケストレーターではない — 中央エンジンは存在しない。Architect が対話し、他はそれに反応する
- 状態ストアではない — Thread Tree をデータベースに複製しない
- 内容を読むパイプではない — ブリッジが送るのは1行であり、report 本文は決して流さない
- 完成させるものではない — 手動2アクションは今後も自動化しない

完全版は [docs/concept.md](docs/concept.md) に。

## リポジトリ構成

英語版のツリーを参照してください（構成は同一です）。

*名称について: skill ディレクトリ名は `tai`、リポジトリ名は `tai-protocol` です。*

## 関連プロトコル

StateToolsLab プロトコル群の一員です。

- [SAI](https://github.com/StateToolsLab/sai-protocol) — **何を触るか**: 安定した構造アンカー ID
- SPP — **どう安全に触るか**: 構造化されたパッチ手順
- TAI — **誰が決め、どう手渡すか**

## ステータス

実験段階。プロトコルは変更される可能性があります。`docs/concept.md` §5 の制約は日付付きのプラットフォーム観測値（2026-08）であり、プラットフォームが変われば設計を再導出します。

## ライセンス

MIT
