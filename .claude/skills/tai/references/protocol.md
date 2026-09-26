# tai — Protocol Reference 0.2

共通の正本は [TAI Core](../../../../docs/protocol.md)。
本書は既存Gitワイヤ形式を使う際のPresetと補足を定める。

## 1. 設計

```text
Document = 実行契約・判断・復旧可能な状態
Role     = 交換可能な責務と権限
Git      = このアダプターのcarrier / 文書ストア
Bridge   = このアダプターの通知・運搬実装
TAI      = 上記の境界規約
```

手動2回は利用可能なプロファイルとして残す。全エージェント接続も許可するが、
文書保存・版照合・Gate・裁定を省略してはならない。
会話ツリーを丸ごと複製する必要はない。再開に必要な状態と判断の文書は残す。

## 2. Autonomy Preset

`.ai/config.yaml` の `default_autonomy` は既定値。Ownerが承認したPolicyに基づき、
Architectが実効値をTask本文とStateへ記録する。未解決・矛盾時は確認して停止する。

| Gate | MANUAL | TASK_BOUNDARY | GIT_BOUNDARY | AUTONOMOUS_UNTIL_ARBITRATION |
|---|---|---|---|---|
| task_start | confirm | auto | auto | auto |
| next_task | confirm | confirm | auto | auto |
| branching | confirm | auto_until_arbitration | auto_until_arbitration | auto_until_arbitration |
| commit | confirm | auto | confirm | auto |
| push | confirm | confirm | confirm | confirm |

TASK_BOUNDARYが既存の導入既定。接続モードを「自動」にしてもPresetは変わらない。
AUTONOMOUS_UNTIL_ARBITRATIONでもpushはこの表ではconfirmであり、名前だけで自動公開しない。
この表は判断規約であり、既存Bridgeが全項目を読み取って強制する実装ではない。
予算・時間・反復の上限と停止経路は別途指定する。

## 3. Stable Pointと裁定

Stable Pointは採用済みの前提。Reportごとに必ず発生するわけではなく、Git commitとも異なる。
採否・根拠・対象版を永続Stateへ記録してから次Taskへ進む。

目的変更、未委譲の価値判断、Stable Point破棄、無許可の不可逆変更、USER固有の意図が
必要なときは、Presetを問わず裁定を求める。技術的な分岐だけなら委譲範囲内で処理できる。

```text
USER ARBITRATION REQUIRED
現在地: <StateとTask版>
完了: <検証済みの結果>
停止理由: <権限・判断・上限等>
決めること: <一文>
選択肢: <案と影響・トレードオフ>
証拠: <固定参照>
```

通知の受領やAgent間の合意を、USER確認の代わりにしない。

## 4. 軽量であるための制約

巨大な中央基盤、専用DB、イベントバス、全会話のJSON化は必須ではない。
採用する場合は必要性と運用負担を説明する。プラットフォームの認証・権限制約を迂回しない。
Supervisorに採否判断をさせたり、Workerに次Taskを作らせたりして責任を曖昧にしない。

旧版の「毎回新規Architect禁止」「状態の文書化禁止」「手動handoff自動化禁止」は
Core原則から外す。代わりに永続文書と権限の境界を必須にする。

## 5. Git補足

Workerに実装commitがない場合、Reportのcommitは分岐元main HEADを使う。
Task ID / revisionを一致させ、Reportだけのrevision増分は行わない。

mainの確認は分岐元・期待する先端・全変更パス・操作結果を照合する。
merge-baseの一致だけから「Workerが一度もmainを操作していない」とは断定しない。

archive・reset・Report保全・独立diff・原文照合・同期コマンドは
[operations.md](../../../../docs/operations.md)を参照。
変更点は[migration-v0.2.md](../../../../docs/migration-v0.2.md)を参照。
