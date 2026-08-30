---
name: tai
description: AI 委譲開発のための三層 handoff 規約（Architect / 現場監督 / Worker）。task.md / report.md の書式と手番、Autonomy Gate（commit / push / arbitration）、現場監督の責務境界を定める。task.md を実行するとき、report.md を書くとき・評価するとき、現場監督の役割に就くときに使う。handoff, task.md, report.md, supervisor, gate。
---

# tai — Task–Architect Interchange

## 0. 役割

```text
Architect  Claude チャット（ホーム／プロジェクトのスレッド群）。設計・判断・進捗管理。
           Thread Tree の実体はスレッド群とプロジェクト知識。
現場監督    Claude Code クラウドセッション。リポジトリ側の機械的作業のみ。判断しない。
Worker     Claude Code。実装。文脈を持たない。task.md が全入力。
tai        三者が従う規約（書式・手番・Gate）。それ以外は何もしない。
```

**Architect は役割名であり、固定のスレッドではない。** その時々に task.md を書き report を読むスレッドが
Architect の手番を担う。

**tai は Thread Tree を管理しない。** ツリーの Source of Truth は Architect（チャットのスレッド群）の
文脈であり、別ファイル・別 DB に複製しない。task.md の `## 現在位置` は、その時点のツリーを Worker へ
見せるための**投影（表示）** であって状態ではない。

自分がどの役割かは、その回で何を書くかで決まる。

- `.ai/task.md` を書く側 → Architect
- `.ai/task.md` を読んで実装し `.ai/report.md` を書く側 → Worker

### 現場監督の責務境界

実体は claude.ai/code のクラウドセッション（リポジトリ＝対象プロジェクト、ブランチ＝main）。

責務（これ以外を行わない）：

1. USER から貼られた task.md を `claude/architect` へ push する（内容は変更しない。
   templates との書式差異のみ整えてよく、整えた箇所は報告する）
2. Bridge の通知を受けたら `git fetch` し、`origin/claude/<task_id>` の report.md を読んで
   規約適合（変更ファイル範囲・commit 分離・main 無変更・frontmatter・作業ツリー復帰）を
   機械的に確認し、チェック結果と report 本文を表示する
3. 承認後の main 取り込み指示をローカルに中継する（または USER がローカルで直接実行）
4. Phase 完了時の tag 付与等、Architect が明示した Git 操作

禁止（NG12）：

- report の評価・推奨・Stable Point 判定・次 task の起案
- 規約ファイルの自発的編集
- task.md の内容への意見（書式の機械的整形を除く）

### USER 選択待ち時の既定動作

現場監督が USER の選択・承認を要する状態（Stop hook、確認プロンプト等）に遭遇したときの
既定動作を定める。

- **自己解決しない。** 選択肢のどれかを自分で選んで先へ進まない。
- 作業途中の状態は保留のまま維持する（必要なら `git stash` 等で退避する）。
- 何を待っているかを 1 行で表示し、USER の指示があるまで停止する。

根拠：USER 選択待ちを現場監督が自己解決すると、判断しない層が判断したことになり
NG12 に帰着する。

### 現場監督の着任手順

現場監督のセッションが期限切れ・世代交代で新しくなったとき、着任時に次のファイルを読む。

- `SKILL.md`
- `references/protocol.md`
- `references/transport.md`

読了後、`.ai/config.yaml` の `supervisor_session` を自分のセッション ID に更新する。

Architect 由来の task.md を運ぶブランチ `claude/architect` は、**その時点の origin/main から
作り直す**（前回の残骸を土台にしない）。手順の詳細は `references/transport.md` §4 を参照。

根拠：世代交代の直後は、前世代の残したブランチを土台にした起点ミスが起きやすい。

### ローカルセッションの責務境界

ローカルの Claude Code 対話セッションについて、次の三分法を規約化する。

- 常設してよいのはブリッジ（`bridge-poll.sh`）のみ
- 単発の明示操作は可（Gate の実行、診断、対話モード Worker の起動）
- 監視・完了待ち・自動後続は不可

Claude Code セッションは `bridge-poll.sh` を自ら起動してはならない。ブリッジは
リポジトリごとに 1 プロセスとする。

根拠：ブリッジの二重起動は重複通知を生む。

## 1. 手番

1 手番に 1 ファイルだけ書く。両方を同じ手番で書かない。

```text
Architect（チャット）: task.md を書く →（現場監督が claude/architect へ push → main へ反映）
Worker:              task.md を読む → 実装 → report.md を書く → commit → push（claude/<task_id>）
Architect（チャット）: report.md を読む → 評価 → Gate 判定 → 次の task.md または停止
```

task.md を書くのも、report を評価するのも **Architect（チャット）** である。
現場監督は運搬と機械チェックのみを行う（§0）。

- Worker は task.md を**書き換えない**。追記も禁止。伝えたいことは全て report.md に書く。
- Architect は report.md を**書き換えない**。
- Worker は自分で次の task を作らない。1 手番＝1 task。
- 現場監督は通知受領時、`git fetch origin` のうえ `origin/claude/<task_id>` の
  report.md を読む。作業ツリーの report.md を見ない。

  ```bash
  git fetch origin
  git show origin/claude/<task_id>:.ai/report.md
  ```

  理由：作業ツリーは fetch 前の古い状態を指していることがあり、古い report で
  判定する事故を防ぐため。

  report のブランチが既に main へ merge され削除されている場合は、
  `git show origin/main:.ai/report.md` で origin/main から読む（merge 済みフォールバック）。

### サイクルの順序規則

1 往復の順序について次の 2 点を規約化する。

- **main への取り込みと origin への push が完了していることを、次の task を現場監督へ
  搬入する開始条件とする。** 完了前に次の task を搬入すると main と `claude/architect` が
  分岐し、ブリッジの ff-only merge が失敗し続ける。
- **ブリッジは task の搬入より前に起動しておく。** ブリッジは初回起動時に、その時点の
  origin の状態を処理済みとして記録する。搬入後に起動すると、搬入済みの
  `claude/architect` が処理済みとして扱われ Worker が起動しない。

### チャット運搬のペイロード上限

USER がチャットを経由して本文を運ぶ場合（手動 2 アクション）の切り替え規約。

- 一定量を超える本文、または内容の完全性を機械的に検証する必要がある本文
  （スクリプト、規約ファイル本文、長い report）は、チャットへの転記ではなく
  **ローカルファイルとして渡し、`shasum` による sha 照合で完全性を確認する。**
- **base64 での受け渡しは行わない。**
- task.md 本文のように小さく、書式が保たれるものはチャット転記でよい。

根拠：チャット転記（生テキスト・base64 とも）は書式破損を起こしやすく、
base64 は安全フィルタの誤検知も誘発する。

## 2. task.md の書式

`.ai/task.md`（Architect が上書きする）。テンプレートは `templates/task.md`。

```markdown
---
task_id: T-001
revision: 1
status: active
commit: auto
push: confirm
model: sonnet      # 任意。省略時は sonnet
---

# Task

<Worker への具体的指示。命令の意味は自然言語本文に持たせる>

## 現在位置

Main
├─ A 認証基盤
│  ├─ A1 トークン発行      ✔ stable
│  └─ A2 リフレッシュ      ◀ このタスク
└─ B UI                    （未着手）

## 完了時

実装結果を `.ai/report.md` に報告し、`claude/T-001` ブランチへ commit / push すること。
```

frontmatter は上記 5 つ + 任意の `model` だけ。それ以外を増やさない。

| キー | 必須 | 意味 |
|---|---|---|
| `task_id` | 必須 | `T-NNN`。Architect が採番 |
| `revision` | 必須 | 同一 task_id 内で単調増加。差し戻し時に +1 |
| `status` | 必須 | `active` = 実行対象 / `none` = 未使用プレースホルダ |
| `commit` | 必須 | ローカル main への取り込み（merge）の可否（Preset から解決済みの実効値）。§4 参照 |
| `push` | 必須 | origin への反映の可否（同上）。§4 参照 |
| `model` | 任意 | Worker のモデル。**省略時は `sonnet`**。詳細は `references/transport.md` |

`model` は、task.md 単体では解けない設計判断が実装中に必要だと Architect が事前に分かっている
task でだけ `opus` にする。その場合は本文に理由を一行添える。
Worker 起動時に `--model <値>` として渡される想定であり、Worker 自身がこの値を解釈する必要はない。

`status: none` は「まだ task が発行されていない」ことを表す。Worker はこれを見たら
**読み込み失敗ではなくタスク無し**と判断し、何も実装せず Architect に確認する。

`## 現在位置` は Architect のみが書く。Worker は読み取り専用で、パースしない。形式は自由記述。

ブランチ名は `claude/<task_id>` に固定する。frontmatter には持たせない。

### task_id の採番

- **採番は発行直前に突合する。** スレッドの引き継ぎ情報や過去の会話に書かれた「次の番号」は
  その時点のスナップショットであり、採番の根拠にしない。
- 突合は当該リポジトリの `origin/main` に対して行う（`git log origin/main` の merge 履歴、
  または現場監督の機械チェックによる重複検出）。
- **番号空間はリポジトリ単位。** 突合対象は当該リポジトリの `origin/main` のみであり、
  他リポジトリの task 番号とは独立している。

根拠：引き継ぎ情報の「次の番号」はスナップショットであり、発行時点の実態と食い違いうる。

## 3. report.md の書式

`.ai/report.md`（Worker が上書きする）。テンプレートは `templates/report.md`。

```markdown
---
task_id: T-001
revision: 1
status: completed
branch: claude/T-001
commit: 4f2a9c1
---

# Worker Report

## 実施内容
## 結果
## 未解決事項
## Architectへの申し送り
```

- `status`: `completed` / `blocked` / `failed` / `none`（未使用プレースホルダ）
- `branch` と `commit` は必須。Architect が差分を特定し、重複判定キーに使う。
- `commit` は**実装の最終 commit の sha**。report.md 自身の commit は含まない。
- **report.md は実装とは別 commit にする。** 実装を先に commit し、その sha を frontmatter に書いてから
  report.md を別 commit で載せる。同じ commit に入れると `commit` が自分自身を指すことになり書けない。
- `task_id` / `revision` は task.md からそのまま写す。勝手に変えない。
- **同じ実装 commit のまま report を差し替えるときだけ `revision` を +1 する。**
  実装をやり直していないので `commit` が変わらず、`(task_id, revision, commit)`（§5）が
  前回の通知と一致して無視されるため。Worker が `revision` を動かしてよいのはこの場合だけ。
- **Architect は、report.md の `task_id` と `revision` が現在の task.md のものと一致する場合だけ、
  それを現在の task の report として読む。** 一致しなければ **report 未着**とみなす。
  前 task の report を現在の report と取り違えないための判定。
- したがって、**新しい task を発行するときに report.md を書き換える必要はない。**
  前 task の report がそのまま残っていてよい。Worker が実装後に上書きする。
- Worker が判断に迷ったら本文に `User Arbitration Required` と書いてよい。
  **ただし最終判定は Architect が行う。** Worker の申告は材料であって決定ではない。

## 4. Gate

`.ai/config.yaml` の `default_autonomy` は **default 値**であり、Source of Truth は Architect の指示。
Architect は Thread Tree の枝ごとに Policy を変えてよい。Preset の定義は `references/protocol.md`。

```yaml
task_start:  auto | confirm
next_task:   auto | confirm
branching:   auto_until_arbitration | confirm
commit:      auto | confirm | disabled
push:        auto | confirm | disabled
```

| Gate | 判定者 | タイミング | `confirm` の意味 |
|---|---|---|---|
| `task_start` | Architect | task.md を push した直後 | Worker 起動前に USER へ確認 |
| `next_task` | Architect | report 評価後 | 評価サマリを出して停止。task.md を書かない |
| `branching` | Architect | 分岐発生時 | `auto_until_arbitration` は技術的分岐のみ自律処理 |
| `commit` | Architect | ローカル main への merge 時 | merge せず USER へ確認 |
| `push` | Architect | origin へ反映する時 | origin を触らない。USER が操作する |

`task_start` / `next_task` / `branching` は Architect 側の判断なので task.md に載せない。

### commit / push の境界

```text
commit  ＝ ローカル main への取り込み（merge）
push    ＝ origin への反映全般（main の push、PR 作成、マージ）
```

ただし `claude/*` ブランチへの push は Gate 非適用で、従来どおり常に許可する。

境界は Git の操作名ではなく**取り消しにくさ**で引く。ローカルに閉じているうちは `git reset` で
戻せるが、origin へ出たものは他者・他セッションから見えるため取り消しが難しい。
境界の考え方の詳細は `references/protocol.md` §8 を参照。

### 責務境界（重要）

```text
Worker  の責務は claude/<task_id> ブランチへの commit / push まで。
main への取り込み・merge・PR 作成は Worker の責務ではない。
```

- `claude/*` ブランチへの commit / push は、Gate の値に関わらず**常に許可**する。
  これが無いと report.md が運べない。
- **Worker は main を触らない。** `git merge` / `git push origin main` / `gh pr create` を実行しない。
  task.md の `commit: auto` は「Architect が後で main へ取り込んでよい」の意味であって、
  Worker への取り込み指示ではない。
- main への取り込みと PR 作成は Architect が指示し、**Architect または USER が実行**する。
- `commit: disabled` は「ローカル main へ取り込まない」、`push: disabled` は
  「origin へ反映しない」の意味。Worker ブランチへの書き込みを止める設定は無い。

この境界は将来 Worker がクラウドセッションになったとき（Worker から main を触れない）に
そのまま成立させるためのもの。ローカル Worker でも同じ境界を守る。

- **headless で実行中に権限不足・承認不能な操作に当たった場合、対話的に質問せず、
  `status: blocked` の report を書いて終了する。** task.md に対話モード指定がある task を
  headless Worker が受け取った場合も同様に、実装に着手せず即座に `status: blocked` の
  report を書いて終了する。
- **headless 実行中は、承認・選択・追加情報を求める出力をして待機または終了することを
  禁止する。** headless セッションに応答者は存在しない。質問して終了することは
  「report を書かずに往復を途絶させる」ことと同義である。blocked の判定材料
  （何に阻まれたか）は質問ではなく report 本文に書く。report を書いてから終了することが、
  headless Worker の唯一の正常な停止方法である。

### Gate 実行の完了確認

commit / push Gate を実行したときの完了確認と報告の手順を定める。

- **完了を文言で報告しない。** `git fetch origin` の後、`git log -1 --format=%h origin/main`
  で得た origin/main の先端 sha（短縮 7 桁）を示して報告する。
- Architect は、報告された sha が期待する merge commit と一致することを確認してから
  次の手番へ進む。

根拠：完了の文言報告は実態（push 未了等）とズレうる。sha は照合可能な事実である。

## 5. 二重実行防止

| 方向 | 重複判定キー |
|---|---|
| Architect → Worker（起動） | `(task_id, revision)` |
| Worker → Architect（通知） | `(task_id, revision, commit)` |

判定は Architect が自分の文脈で行う。専用の状態ファイルを作らない。
同じ `(task_id, revision)` で Worker を 2 回起動しない。同じキーの通知を 2 回目以降は無視する。

**通知行の commit sha は短縮 7 桁**に統一する。

**Bridge は通知行の全フィールドを report.md の frontmatter からそのまま取る。
自分で観測した commit を使わない。** report.md は実装とは別 commit で載る（§3）ため、
fetch した時点のブランチ先端は report 自身の commit を指しており、frontmatter の `commit` と
一致しない。frontmatter から写すことで、通知キーと report のキーが必ず一致する。

## 6. Stable Point / User Arbitration

要点のみ。判定条件の詳細は `references/protocol.md`。

- **Stable Point ≠ Git Commit。** commit は毎回あるが Stable Point は毎回ではない。
  判定タイミングは「report 受領後、次の task を書いてよいか」。
- **分岐したこと自体は停止条件ではない。** 停止するのは
  *新しい価値判断（human preference）が必要になったとき*だけ。
- 停止するときは `USER ARBITRATION REQUIRED` と明示し、`references/protocol.md` の書式で提示する。
  「どうしますか？」だけの問いかけは禁止。

## 7. 参照

| 参照先 | 内容 |
|---|---|
| `references/protocol.md` | 設計思想、Stable Point、User Arbitration 判定、Preset 定義、停止時 UX 書式、禁止事項、補足規則 |
| `references/transport.md` | Claude Code 固有の運搬手順、既定モデル、Worker の起動方法 |
