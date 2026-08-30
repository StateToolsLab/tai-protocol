# tai — Transport Reference（Claude Code 固有）

SKILL.md の規約は運搬手段に依存しない。Claude Code 固有の手順はここに閉じ込める。

---

## 1. モデル

役割は三層（Architect ＝ Claude チャットのスレッド群 ／ 現場監督 ＝ Code クラウドセッション ／
Worker ＝ Claude Code）。定義と責務境界は SKILL.md §0。

| 役割 | 既定モデル | 理由 |
|---|---|---|
| Architect | Opus | 設計判断、Thread Tree の保持、Gate 判定 |
| Worker | **Sonnet** | task.md に閉じた実装作業。文脈を持たないため |

### task ごとの指定

task.md frontmatter の `model` は任意フィールドで、**省略時は `sonnet`**。

```yaml
model: opus      # この task だけ opus で回す
```

Worker を `sonnet` 以外にするのは、task.md 単体では解けない設計判断が実装中に必要だと
Architect が事前に分かっている場合だけ。その場合は task.md 本文にモデル指定の理由を一行書く。

この値は Worker 起動時に `--model` として渡す。Worker 自身がこの値を解釈する必要はない。

```bash
claude --model opus "Read .ai/task.md, ..."
```

---

## 2. 手動運搬（フォールバック）

Bridge を使わず、USER が自分で運ぶ最小構成。導入直後の動作確認や、Bridge 停止時の
最終フォールバックとして常に利用可能。

```text
Architect（チャット）
    │  task.md 本文を書く → USER が現場監督に貼る → 現場監督が反映（§4）
    ▼
Worker（ローカル Claude Code）
    │  実装 → report.md を書く → commit → push（claude/<task_id>）
    ▼
USER が手動で通知を渡す（下記）
```

### Worker の起動

```bash
claude --model <task.md の model 値> "Read .ai/task.md, execute the task, then write .ai/report.md and commit/push to claude/<task_id>."
```

`model` が無ければ `sonnet`。

- Worker は `claude/<task_id>` ブランチを作って作業する。
- **main を触らない**（SKILL.md §4 の責務境界）。merge / `gh pr create` を実行しない。
- `.ai/task.md` の `status: none` を見たら、何も実装せず Architect に確認する。
- **push が済んだら `git checkout main` で作業ツリーを戻しておく。**
  ローカル Worker は共有の作業ツリーで動くため、`claude/<task_id>` に居たまま終わると、
  次の手番の操作がそのブランチ上で行われてしまう。これはブランチを切り替えるだけで
  main の内容を変更しないので、§4 の「main を触らない」には抵触しない。

### 手動フォールバック通知

Bridge の有無に関わらず、USER が現場監督セッションに次の 1 行を渡せばループは成立する。

```text
[handoff] report.md updated task_id=T-001 revision=1 branch=claude/T-001 commit=<短縮7桁>
```

本文は貼らない。受け手は通知を受けたら自分で `git fetch` して report.md を読む。
この経路は**常に利用可能な最終フォールバック**として残す。

---

## 3. Bridge

Bridge はローカルで動かす（クラウドセッションの VM 内には claude.ai 認証が無く、
セッション間でメッセージを送れないため。docs/concept.md §5 参照）。

```bash
scripts/notify-architect.sh [report.md のパス]   # 省略時 .ai/report.md
```

通知の宛先は**現場監督セッション**。環境変数 `SUPERVISOR_SESSION`、無ければ `.ai/config.yaml` の
`supervisor_session` の順で解決し、report.md の frontmatter から
`[handoff] report.md updated task_id=... revision=... branch=... commit=...` を組み立てて
`claude -p --cloud` で 1 回だけ送信する。判断・再送はしない。失敗時（`ok:false` や実行失敗）は
通知行を stdout に出し、現場監督セッションへ手で貼るよう促して exit 1。

## 4. Architect の task.md は claude/architect 経由で運ぶ

Architect（チャット）はリポジトリに書けないため、USER が task.md を現場監督セッションに貼り、
現場監督がリポジトリへ反映する。現場監督（Code クラウドセッション）は main へ直接 push できないので、
`claude/architect` ブランチ経由で運ぶ。

```bash
git fetch origin
git checkout -B claude/architect origin/main
# .ai/task.md を書いて commit
git push -f origin claude/architect
```

背景：クラウドセッションは `claude/*` ブランチにしか push できない（main への push・origin の
ブランチ削除は拒否される。docs/concept.md §5 参照）。

**main への取り込み（fast-forward）と push はローカル側（USER または bridge-poll.sh）の責務**である。

## 5. bridge-poll.sh

```bash
bash .claude/skills/tai/scripts/bridge-poll.sh [間隔秒（既定 30）] [--no-autostart]
```

責務は 3 つのみ：(a) `claude/architect` の更新検知 → main へ ff-only merge + push +
Worker 起動、(b) `claude/T-*` の report.md 更新検知 → `notify-architect.sh` 呼び出し、
(c) 処理済み位置を `.ai/.bridge-state` に記録（再起動後の重複防止）。判断・評価・再送はしない。
`--no-autostart` は Task Start Gate = confirm 運用時に (a) を無効化するフラグ。
実行には `SUPERVISOR_SESSION` 環境変数または `.ai/config.yaml` の `supervisor_session` が
必要（`notify-architect.sh` が参照）。停止は Ctrl-C。

Worker は `-p` の headless セッションとして起動され、`--allowedTools
"Edit,Write,Read,Glob,Grep,Bash(git *)"` により編集と git のみが許可される（`--dangerously-
skip-permissions` は使わない）。`-p` は対話的な許可付与ができないため、この起動時フラグが無いと
全書き込みが拒否されて停止する。

headless 起動が失敗する場合は、Desktop の対話セッションで Worker を手動起動するフォールバックとする。