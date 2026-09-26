---
name: tai
description: 文書制約型handoff規約のClaude Code / Gitアダプター。Architect・Supervisor・Workerの責務、task.md / report.md、Gate、原文保存、独立検証、担当交代を定める。
---

# tai — Task–Architect Interchange 0.2

[Core](../../../docs/protocol.md)が共通規約。本書は既存Claude Code / Git経路の運用を定める。
Coreとアダプターを併せて導入する。詳細は `references/protocol.md` と `references/transport.md`。

## 0. 役割

ArchitectはTask全文の起草・内容と版の確定・発行指示、Report評価・Gate判定を担う。
Supervisorは受け取った完成済み本文のファイル化・保存・搬入と機械チェック、承認済みGit操作を担う。
SupervisorはTaskを材料から起案せず、内容の評価・推奨・変更をしない。
Owner / USERは環境・接続・既定値・許可を承認する。書込み担当と内容の権限を混同しない。
WorkerはTaskに限って実装し、Reportと証拠を残す。
これらは固定のモデルやセッションではない。Claude Codeはこのアダプターの実装例である。

Architect・Supervisorも交代できる。ただし有効なPolicy、Taskの版、採用判断、Report参照、
実行中処理、承認待ちを永続Stateから再取得し、実体と照合してから着任する。
Taskの現在位置だけを完全な復旧状態とみなさない。前任の会話を唯一の記憶にしない。
必要事項を満たす既存savepoint・起動キットを使ってよい。起動照合で必要なGit履歴・固定SHAを
取得できるかも確認し、shallow等による欠損時は権限内で補ってから再開する。
前任の承認済みGateは対象版と根拠を照合して引き継ぎ、交代だけを理由に再実行しない。

Supervisorの責務は次に限定する。

1. Architectの完成済み本文と発行指示を受け、版・権限・書式を確認し `.ai/task.md` として
   ファイル化・保存・commit・搬入する。固定前の限定的な整形はoperationsの規則に従い記録する。
   発行正本固定後は原文を変更しない。内容の不足・未承認差異はArchitectへ差し戻す。
2. Reportを固定SHAから取得し、変更範囲、実装とReportのcommit分離、Task不変、
   frontmatter、mainと作業ツリーの状態を確認する。全文diffを独立取得する。
3. 承認済みの統合・公開操作を中継または権限内で実行する。
4. Gate時にTask・Report両原文をarchiveし、両窓口resetと同じcleanup commitにする（17-J）。
   各原文との一致、ID・revision、固定参照と判断の保全を確認し、保存失敗時はresetしない。

承認待ちを自己解決しない。何を待つかを表示して停止する。
世代交代時は本書・references・Recovery Stateを読み、旧実行を照合する。
通知先は環境変数 `SUPERVISOR_SESSION` を優先し、実セッションIDを配布物へcommitしない。

## 1. 手番と順序

```text
Architectが全文起草・内容確定・発行指示
      -> USERまたは認可されたTransportが搬送
      -> Supervisorがファイル化・保存・照合・commit・搬入
      -> Bridgeが承認済み手順で起動 -> Workerの実行 -> Report保存・返送
      -> Supervisorの独立確認 -> Architectの採否・Gate
      -> State更新・archive・reset -> 次Taskまたは停止
```

発行・実行の手番ではTaskとReportを同時に起案しない。Gate後の機械的resetは別の管理操作。
WorkerはTaskを書き換えず、ArchitectはReportを書き換えない。
Workerは次Taskを発行しない。自動handoffでもこの役割境界を維持する。
既存Bridgeの起動先は固定のClaude Codeであり、Supervisorが複数Workerを選ぶ処理ではない。
起動の事前承認と起動コマンドの実行者は別。詳細は[接続定義](../../../docs/worker-connection.md)。

前Taskのmain統合・archive・reset・originへの反映が完了するまで次Taskを搬入しない。
このアダプターは単一窓口・共有作業ツリーの直列実行。Bridgeは1リポジトリ1プロセスとし、
Workerや別の運用セッションと作業ツリーを同時操作しない。
Bridgeは初回に既存のorigin状態を処理済みとして記録するため、Task搬入前に起動する。
承認・原文保存・事前検査が未完了なら `--no-autostart` または手動運用とする。

通知後は作業ツリーの古いReportではなく、fetch後の先端を固定して読む。

```bash
git fetch origin
git rev-parse origin/claude/T-001
git show <上で得た完全SHA>:.ai/report.md
```

枝が既に削除されていればStateのReport固定参照から読む。
reset後の `origin/main:.ai/report.md` を過去Reportの代わりにしない。

## 2. TaskのGitワイヤ形式

テンプレート: `templates/task.md`。

```yaml
task_id: T-001
revision: 1
status: active
commit: auto
push: confirm
model: sonnet
```

必須は最初の5項目。任意model以外のfrontmatterを追加しない。
Task IDはリポジトリ単位の `T-NNN`、revisionは正の整数でArchitectだけが増やす。
`status: active` は実行対象、`none` は未使用窓口。
`model` 省略時のsonnetは既存ブリッジの既定であり、Coreの制約ではない。
簡易パーサーとの互換性のため、値は引用符・inline comment・複合YAMLなしの単純な1行とする。

目的、範囲、出典、権限、Policy版、受入条件、停止条件、実効Gate、上限、返送先は本文に書く。
`## 現在位置` は自由記述で、永続Stateの参照を添える。
IDは発行直前にorigin/mainと台帳・archiveを照合し、過去会話の次番号を盲信しない。
同じID・revisionの原文を差し替えない。旧revisionを保存してからArchitectが再発行する。
`status: none` を実行しない。headlessではTask無しを通知して終了し、対話質問を待たない。

## 3. ReportのGitワイヤ形式

テンプレート: `templates/report.md`。

```yaml
task_id: T-001
revision: 1
status: completed
branch: claude/T-001
commit: 4f2a9c1
```

5項目とも必須。statusは `completed` / `blocked` / `failed` / `none`。
commitは実装先端の短縮7桁、実装がなければ分岐元main HEAD。
**実装を先にcommitし、Reportは別commitにする。** Report自身のSHAをcommit欄へ書かない。
保存先の固定参照にはReportを含む先端の完全SHAを別途記録する。

ID・revisionは受領Taskと一致させる。Workerだけでrevisionを増やす旧例外は廃止。
不一致のReportは保存して照合するが、現在Taskの結果として採用しない。
訂正が必要ならArchitectが新revisionを発行する。旧Reportを失わないよう先に保全する。

実施内容、検証結果、未検証範囲、成果物、実際の副作用、未解決事項を記載する。
Workerによる全文diffの重複添付は任意で、省略時は自己申告する（16-S）。
SupervisorはTask全範囲を独立取得し、report・diff・本文をツール出力のまま全量返送する（16-U）。
手書き再生成、要約表記や「既報告どおり」等による省略・置換をしない。
長文は欠落のない固定ファイル・分割で渡す。判断の説明は原文と別に添え、代替にしない。
Reportのcompletedは受入承認ではない。

## 4. Gate

Owner承認済みPolicyが上位の正本。`.ai/config.yaml` は既定値。
Architectは委譲範囲内で枝・Taskごとの実効値を解決し、本文とStateに記録する。

| Gate | 対象 | confirm時 |
|---|---|---|
| task_start | Worker開始 | 起動前に承認を待つ。Bridgeはno-autostart |
| next_task | 次Task発行 | 評価を報告して停止。Taskを起案・搬入しない |
| branching | 技術的分岐 | 方針に従って停止。新しい価値判断は別途裁定 |
| commit | ローカルmain統合 | mergeせず承認を待つ |
| push | main公開・PR作成・共有先への反映 | 反映せず承認を待つ |

commit / pushは `auto` / `confirm` / `disabled`。
Workerの責務は専用の `claude/<task_id>` へのcommit / pushまで。main統合・PR作成はしない。
既存の専用枝への配送例外は維持するが、Ownerがそのリポジトリへの配送を認可していることが前提。
同名プレフィックスだけで任意の共有先への公開権限を得るものではない。

権限不足・対話承認不能・能力不足に当たったheadless Workerは、blocked Reportを保存して停止する。
Reportも保存できなければTransportが失敗として扱い、次工程を開始しない。
承認を迂回せず、応答者のいない質問待ちをしない。

Gate完了は文言でなく、fetch後のorigin/main完全SHAが期待するcleanup先端と一致することで確認する。
Task枝の統合だけでなくarchiveとresetまで反映されたことを確認して次へ進む。

## 5. 重複・復旧

起動キーは `(task_id, revision)`、通知キーは `(task_id, revision, commit)`。
通知のcommitはReportのfrontmatterから取り、観測したReport先端SHAで置き換えない。
処理済みキーと実行所有者はセッション外にも保存する。
既存Bridgeの `.ai/.bridge-state` だけで、あらゆる二重起動・副作用の冪等性が保証されるとはしない。
同じTaskを別carrier commitで再搬入する前に台帳と実体を照合する。
不明な実行を勝手にリトライせず、Workerが動いていないか確認する。

## 6. Archive・Stable Point

発行正本はWorkerへ渡したcommitの `.ai/task.md`。その原文を `.ai/archive/T-XXX_task_rN.md` に保存する。
Architectのチャット本文を再構成して保存物の代わりにしない。発行commitの完全SHAを引継ぎ文書に残す。
Reportも `.ai/archive/T-XXX_report_rN.md` へ原文のまま保存する（17-J）。
Nは対象Taskと一致するReportのrevision。Report固定commitのSHAは実装commit欄とは分けて記録する。
Gate時はTask archive・Report archive・両窓口resetを同じcleanup commitにする。
Git履歴や既存返送先への保存だけでは、このReport archiveを代替しない。
差戻し・取消・新版差替え前も旧Taskと返送済み旧Reportを保全し、既存原文を上書きしない。
両原文の一致・保存が確認できるまでresetしない。未着Reportを再構成して補わない。
原文のstatusを完了状態へ書き換えない。採否はState / Decisionに記録する。

```bash
python scripts/task_archive.py --report .ai/report.md
```

ヘルパーは保存と照合のみ。Gate承認・Git操作・窓口resetは行わない。

Stable Pointは採用判断であってcommitではない。判断と根拠・成果物版を永続化する。
目的変更、未委譲の価値判断、Stable Point破棄、無許可の不可逆変更では裁定を要求する。
詳細と操作手順は [operations.md](../../../docs/operations.md) を参照。

## 7. 保守

このskillやBridgeの保守は通常の実装Taskと分け、明示的な保守権限で行う。
`.claude/` を編集できないheadless環境で保護を迂回しない。対話実行または承認済みの直接編集を使う。
モデルやプラットフォームの観測上の制約を、他のエンジンにも共通する原則としない。
