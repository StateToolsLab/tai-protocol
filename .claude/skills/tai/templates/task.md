---
task_id: T-NNN
revision: 1
status: active
commit: auto
push: confirm
model: sonnet
---

# Task

<Workerへの具体的指示。発行前に全プレースホルダーを実値へ置き換える>

## 目的・変更範囲

<目的、許可する変更パス、禁止事項、期待する成果物>

## 入力・出典

<依頼の参照、発行者、必要資料の固定版、機密区分>

## 権限・停止条件

<Owner承認済みPolicyと版、承認参照、task_start / next_task / branchingの実効値>
<予算・時間・反復上限と確認方法。未対応なら短いTaskと確認Gateに縮退>
<権限不足・目的変更・未委譲の判断で停止。対話実行が必要なら明記>

## 受入条件・原文照合

<テスト、必要証拠、定義や閾値の期待行。全文一致が必要なら独立ハッシュの参照>

## 現在位置

<永続Recovery Stateの固定参照と、このTaskの位置>

## 完了時

実装結果を `.ai/report.md` に報告し、`claude/T-NNN` ブランチへcommit / pushする。
実装とReportは別commitとし、Reportのcommitには実装先端の短縮7桁を記入する。
実装がない場合は分岐元main HEADを記入する。Taskとrevisionを変更しない。
main取り込み・PR作成はしない。共有作業ツリーの場合、push後にmainへ戻る。
全文diffの貼付は任意。省略時は省略範囲と証拠の取得先をReportに明記する。

<!-- modelはこのClaudeアダプターの任意指定。省略時sonnet。inline commentを値に付けない。
     モデルの選択は権限の拡大ではない。発行時はこの説明を取り除く。 -->
