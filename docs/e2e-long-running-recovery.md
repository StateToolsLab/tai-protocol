# E2E Scenario — Controller Ends While Worker Continues

## 位置づけ

tai-protocol未導入の長時間研究ワークフローで発生した実例をもとにした試験シナリオ。
これはtai-protocolの合格事例ではなく、既存の文書・証跡運用で復旧できた一方、
継続制御に不足があった事例である。

原因としてコンテキスト圧縮は**確認されていない**。
「圧縮による役割喪失の証明」として扱わず、長時間Taskにおける
controller/session終了とWorker稼働の分離、および外部状態からの復旧事例として扱う。

## 観測された故障モード

- 管理側は未完了Taskを保持したまま、新規依頼待ちに見える最終応答を返してturnを終了した。
- 管理側のruntime状態はidle / turn completedだったが、正式なGate完了・差戻し・USER停止はなかった。
- Worker側の同一セッションでは処理が継続していた。
- 固定依頼、途中成果物、受入記録、進捗台帳、再開手順は外部ファイルに残っていた。
- USERと親の進行タスクが外部記録とWorker状態を照合し、重複起動せず復旧した。

したがって、次を同一視してはならない。

```text
conversation turn completed
controller idle
Task completed
Worker stopped
Gate accepted
```

これらは別の状態である。

## 設計への示唆（未採用提案）

以下はField Reportからの提案であり、Coreの新規MUSTとして自動昇格しない。

1. **Startup / Role Rebindingを復帰入口にする。**
   圧縮通知の有無に依存せず、再接続・中断・交代時に外部状態を読む。
2. **現在地を短く再構成できる入口を持つ。**
   objective、authority、Task/revision、Stable Point、in-flight execution、
   next action、stop conditions、evidence refsを確認できるようにする。
   既存文書が満たせば新しいstate fileは不要。
3. **会話終了をTask完了と扱わない。**
   turn completed / idleだけでTask・Worker・Gateを終了扱いにしない。
4. **復旧時は再起動より照合を先にする。**
   requested / in-flight / completed / acceptedを区別し、外部副作用と成果物を確認する。
5. **役割・権限・継続義務を再確立できない場合は理由付きblockedにする。**
   自己任命や推測で続けず、未完了Taskを「何をしましょうか？」で見失わない。

## 再現可能なE2E試験

```text
Taskを固定して発行
↓
Workerが時間のかかる処理を開始
↓
途中Report / Evidenceを保存し、一部結果を受入
↓
controller側の会話を中断・交代、または前会話を参照できない状態にする
↓
Workerは処理を継続
↓
Startup / Role Rebindingから外部状態を再取得
↓
Role Binding + Task + Stable Point + in-flight execution + evidenceを照合
↓
requested / running / completed / accepted / not-started を区別
↓
権限一致なら重複実行せず残工程を継続
不一致・不明なら理由付きで停止
```

### 受入条件候補

- 前任の会話全文なしで現在地を復元できる。
- Role Binding Sourceで権限を確認し、自己申告を根拠にしない。
- Workerを二重起動しない。
- 実行中Workerをcontrollerのturn終了だけで停止扱いにしない。
- 未受入結果を受入済みと扱わない。
- Task ID / revision / acceptance criteriaを勝手に変更しない。
- turn completed / idleをTask完了の根拠にしない。
- 復旧判断と、その根拠となる固定参照を記録する。
- Worker状態が不明なら自動リトライせず停止する。

## 圧縮試験との区別

圧縮そのものを観測・制御できない環境では、
「前任会話なしでのcontroller交代」を再現可能試験として使う。
自然発生した圧縮事例は別途Field Reportとして扱い、原因を推測で確定しない。

## 関連規約

- [Core protocol](protocol.md): Role Binding、Recovery State、in-flight execution、重複防止。
- [Supervisor startup](../.claude/skills/tai/SUPERVISOR_STARTUP.md): 外部状態からの再バインド。
- [Field reconciliation](field-reconciliation.md): 実運用からの観測と採否境界。
