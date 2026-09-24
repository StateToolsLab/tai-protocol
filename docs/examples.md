# 接続プロファイルの例

以下は[Core](protocol.md)を実装するための参考フローであり、提供済みのAPI連携機能ではない。
どの例もTaskを保存する前に実行を開始しない。接続モードは承認Policyとは別に選ぶ。

## A. 人間が運ぶ最小構成

```text
人間の依頼 -> ArchitectがTask文書を発行・保存
             -> 人間がTaskをWorkerへ渡す
             -> Workerが成果物とReportを保存
             -> Supervisorが証拠を確認
             -> 人間がReportをArchitectへ渡す
             -> 判断とStateを保存 -> 次Taskまたは停止
```

入口がチャット以外でも同じ。人間がWorkerやSupervisorを担ってもよい。
「メールで頼まれたから実行した」ではなく、権限と受入条件を確定してから着手する。

## B. 異なるエンジンを混ぜる

```text
Issue -> 認証・権限・重複検査 -> Task T-001 r1を文書ストアへ
      -> Architect（エンジンA）
      -> Supervisor（検証プログラム）
      -> Worker（エンジンB、または人間）
      -> Report + 成果物の固定参照
      -> Architectが評価 -> Gate -> State更新
```

各役割が共有するのはベンダーの内部メモリではなく文書。
エンジン変更で権限や予算を増やさない。能力不足では別の実装へ明示的に再割当てする。
再割当ての前に旧実行の終了・副作用を照合し、同時に二つのWorkerを所有者にしない。

## C. 全部エージェントで接続する

```text
イベント -> Source Adapter -> 確定Taskを保存
         -> Architect Agent -> Supervisor Agent -> Worker Agent
         -> Reportを保存 -> 独立確認 -> Decisionを保存
         -> 承認済みPolicyの範囲内で次Taskを発行・保存
```

途中に人間のcopy-and-pasteがなくても適合できる。ただし、イベントからの指示を
そのまま実行権限としない。confirm Gate、USERの新しい価値判断、予算上限、
保存失敗、版の衝突に当たったら停止し、裁定要求を文書化する。
全Agentが賛成しても、人間確認を要求するPolicyは上書きできない。

## D. 司令塔も交換する

```text
T-001 r1 -> Report -> 独立確認 -> 採用判断 D-001
         -> 成果物・Report参照・承認待ち・実行状態をStateへ
         -> 旧Architect / Supervisorの手番を閉じる
         -> 新しい担当がStateと参照先の版・権限を照合
         -> 次のTask T-002 r1
```

引継ぎテストでは新担当に旧会話を渡さず、Stateと必要な参照だけを渡す。
受入判断や未回収Reportが再取得できなければ不合格。会話の要約だけでは代用しない。
障害時の交代では、前任が実行中だった操作を完了扱いせず、実体照合から始める。

## アダプター実装時の確認項目

Source Adapterは出典・発行権限・イベントID・Task固定版を対応付ける。
Engine Adapterは必要能力、権限、入力文書、実行所有者、上限、停止、結果保存を対応付ける。
Storage / Transport Adapterは固定参照、保持、アクセス、配送確認、再送を定義する。
対応APIや実装がない場合は手動文書運搬へ戻し、接続済みとは表示しない。
