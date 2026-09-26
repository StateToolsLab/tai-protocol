---
task_id: T-NNN
revision: 1
status: completed
branch: claude/T-NNN
commit: <実装先端の短縮7桁>
---

# Worker Report

TaskからIDとrevisionをそのまま写す。結果に応じcompleted / blocked / failedを選ぶ。
実装がない場合のcommitは分岐元main HEAD。Report自身のcommitは含めない。

## 実施内容

<実行担当の識別子、受領Taskの固定参照、変更したもの、実際の副作用>

## 結果・証拠

<受入条件ごとの検証結果、実装commit一覧、分岐元の完全SHA、成果物の固定参照>
<全文diffの貼付を省略した場合、その事実と範囲。Supervisorが独立取得する>
<未検証の項目と理由。未取得の証拠を確認済みにしない>

作業ツリーをmainに戻した: <はい / いいえ / 専用作業領域のため対象外>

## 未解決事項

<残課題、阻害要因、再実行前に照合する副作用。なければ無し>

## Architectへの申し送り

<採否判断に必要な材料。Workerのcompletedは受入承認ではない>
