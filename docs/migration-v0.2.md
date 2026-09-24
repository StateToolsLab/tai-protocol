# v0.1.0 → v0.2.0-rc.1 移行ガイド

基準: 公開mainの `28a632ef89562519d9c82260c75f94658a30cde9`。
本版は互換ワイヤ形式を維持するが、思想・運用まで無変更ではない。
移行はOwnerが承認したStable Pointで行う。稼働中のTaskに遡及適用しない。

## 変えるもの

| v0.1.0 | v0.2 |
|---|---|
| 手動2アクションを恒久的に必須とする | manualプロファイルとして維持。自動接続も文書・権限を守れば許可 |
| Architectの会話が状態の唯一の正本 | 採用した状態と判断を永続化し、別セッションから復旧できる |
| Architectはチャット、Supervisor / WorkerはClaude Code | 共通仕様は役割のみを定義。Claude構成はアダプター |
| 現在位置は復元対象ではない | Taskの現在位置は表示でもよいが、別のRecovery Stateを必ず用意 |
| 毎回新規Architectを禁止 | Stateと実行実体を照合できれば交代・新規起動を許可 |
| 窓口のplaceholder復帰だけを規定 | 復帰・差替え前に発行Taskを原文でarchive |
| ReportだけWorkerがrevisionを増やせる例外 | 廃止。revisionは発行Taskに常に一致し、変更はArchitectが再発行 |
| main無変更をmerge-baseだけで推測 | 変更範囲・分岐元・mainの実体を照合。merge-baseだけで実行履歴を断定しない |

report-only revision増分は「Taskとrevisionが一致しないReportを未着扱い」と矛盾していた。
訂正版が必要なら旧Reportを保全し、Architectが新revisionで訂正Taskを発行する。
Reportを勝手に上書きしても既存ブリッジの重複通知キーでは通知されない場合がある。
手動復旧時も固定SHAで対象を指定し、記録する。

## 変えないもの

Git Taskの5必須キー（task_id / revision / status / commit / push）と任意model、
Reportの5必須キー（task_id / revision / status / branch / commit）、
`.ai/task.md` / `.ai/report.md`、`claude/architect` / `claude/T-*`、通知行、
実装とReportの別commit、既存Report返送経路は維持する。
追加情報は本文・Stateへ置き、既存の簡易frontmatterパーサーに新しい構造を要求しない。

**bridge-poll.sh / notify-architect.shの実装とallowlistは変更しない。**
これらはClaude Code専用、単一窓口・直列処理である。
汎用エージェント起動、外部イベント接続、分散ロック、包括的なGate強制、予算強制は
新たに実装していない。Core準拠には、人間の運用または別の検証済みアダプターで補完する。

## 手順

1. 進行中Taskを完了・保留し、Reportと全Task revisionを保全する。外部副作用を照合する。
2. Bridgeを停止し、Workerが稼働していないことを確認する。
3. `docs/`、`templates/`、`scripts/task_archive.py` と更新済み `.claude/skills/tai/` を導入する。
   `.gitattributes` のarchive規則も既存設定と競合しないよう取り込む。
   新規導入だけ `.ai/` をコピーする。既存案件のtask/report/configを配布物で上書きしない。
4. `templates/state.md` を基に `.ai/state.md` または同等の永続文書を作る。
   現在のPolicy、Task一覧、採用判断、Report参照、承認待ち、次番号を実体と照合して記入する。
5. 手動 / 半自動 / エージェント接続のプロファイルを明示し、Ownerが承認する。
   不明なGateはconfirmとし、`task_start: confirm` では `--no-autostart` を使う。
6. 小さなTaskで発行→実行→Report→独立確認→archive→reset→再開を検証する。
7. 別セッションからStateだけを入口に再取得する引継ぎテストを行う。

過去Taskを回収できる場合はGitの固定commitから回収する。
原文が見つからないTaskを、会話から推測して「発行原文」として作らない。
欠損を記録し、将来分から厳密な運用を始める。

## 必須の受入確認

| 観点 | 合格条件 |
|---|---|
| チャネル | 異なる入力経路でも実行前にTask化・権限確認される |
| 交代 | 新しいArchitect / Supervisor / Workerが前任の会話なしで対象文書を取得できる |
| 原文 | 同一ID・revisionの別内容が拒否され、archive原文が変わらない |
| Gate | 自動通知や自動接続だけではconfirmを通過しない |
| 証拠 | 省略diffを確認済みとせず、全変更を独立取得する |
| 保全 | Reportの固定参照が窓口reset・枝の再利用後にも取得できる |
| 復旧 | 再送・再起動で副作用を重複実行せず、不明状態では停止する |

同梱のunit testはarchive helperと局所的なGit手順を検査する。
上表全体、とくに実エンジン・クラウド・認証・ブリッジのE2E合格を代替しない。

## 切り戻し

進行中実行を停止・照合した上で、以前のskill / 運用へ戻す。
archiveと採用判断は削除しない。旧版が読まない文書として残せる。
自動接続の許可は明示的に撤回し、手動handoffと確認Gateへ戻す。
