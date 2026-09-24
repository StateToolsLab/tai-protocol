# Worker接続定義 — 固定構成を先に明文化する

本書は接続設定の整理と将来拡張の案。**新しい設定リーダーやルーターは実装していない。**
公開同梱実装と案件ローカル環境を区別する。Coreの責務は[protocol.md](protocol.md)を参照。

## 1. 現在の同梱実装

| 項目 | 公開同梱実装の所在・動作 |
|---|---|
| 起動エンジン・モード | `bridge-poll.sh` 内の `claude -p`。Claude Code / headless固定 |
| モデル | Taskの任意 `model` を読み、空なら `sonnet`、起動時 `--model` へ渡す |
| 起動許可ツール | 同スクリプトの `--allowedTools`。環境側の承認・設定も別途照合する |
| Task搬入 | Supervisorが `claude/architect` へ配置。Bridgeがmainへff・pushして起動 |
| Report | Workerが `claude/T-*` にcommit/push。Bridgeが通知し、Supervisorが取得・機械チェック |
| Supervisor通知先 | `SUPERVISOR_SESSION`、未設定なら `.ai/config.yaml` の `supervisor_session` |

参照実装: [bridge-poll.sh](../.claude/skills/tai/scripts/bridge-poll.sh)、
[notify-architect.sh](../.claude/skills/tai/scripts/notify-architect.sh)、
[config.yaml](../.ai/config.yaml)、[transport.md](../.claude/skills/tai/references/transport.md)。
この表は公開候補のコードについての記述であり、案件ローカルの同名ファイルを照合した結果ではない。

現状は既存の固定設定が接続定義を兼ねており、Supervisorが複数候補からWorkerを選ぶわけではない。
Architectは承認された範囲でTaskのmodel等を指定し、USERが環境・許可・既定値を承認する。
Bridgeは起動を実行するだけで、独立した許可主体ではない。起動条件を満たさなければ停止する。

## 2. 最小の整理

新しい登録台帳を必須にせず、既存の設定と起動スクリプトへの固定参照を一つの文書にまとめる。
記録するのはエンジン、既定モデル、headless/対話、実行環境、実効許可の参照、Report返送先、
承認者と承認範囲、参照元の版、確認日、未確認事項。実行中セッションIDや秘密そのものは分けて扱う。

次の `worker` ブロックは将来の集約案であり、**現在の `.ai/config.yaml` には追加していない**。
同梱Bridgeはこのブロックを読まない。貼り付けても設定は切り替わらない。

```yaml
worker:
  engine: claude-code
  model_default: sonnet
  mode: headless
  permissions_ref: "<承認済み設定と起動引数の固定参照>"
  report_dest: "claude/<task_id>:.ai/report.md"
```

採用する場合は読取実装・既存値との優先順位・失敗時の停止・互換性テストを併せて追加する。
モデルはTask指定を既定値の上書きとして扱う案だが、上位の権限や利用制限を広げてはならない。
`.claude/settings.json` を使う案件では起動オプションと併せて実体を採取する。
公開同梱allowlistから案件側の実効許可や優先順位を推測しない。未確認値は未確認のまま残す。

## 3. 複数候補を使う段階で追加するもの

名前付きWorkerプロファイルとTaskからの参照、選定規則、接続アダプター、割当記録が必要になる。
これは新機能であり、現行Git frontmatterへ未対応の `worker` キーを今すぐ追加しない。

選定条件はArchitectが委譲範囲内で定め、SupervisorまたはDispatcherが承認済み規則を適用する。
候補なし・規則の曖昧さ・権限不足では差し戻す。未許可のエンジン・モデル・送付先へ自動切替しない。
登録は実行権限そのものではない。割当記録にはTask版、プロファイル版、選定規則版、実行IDを残す。
再割当て時は旧実行・外部副作用を照合し、二重起動を防ぐ。Task原文は書き換えない。

## 4. 導入前の確認

実環境の起動コード、モデル読取経路、settingsと起動引数、USERの承認範囲を照合する。
Supervisor交代時には通知先の環境変数とconfigの実効値を確認する。configだけ直しても
環境変数が旧宛先を指していれば切り替わらない。同梱例はライブIDの公開commitを推奨しない。

起動成功やexit=0は、Reportの到着・版一致・受入合格・Gate完了を意味しない。
ブリッジ再起動でも未完了Taskと実際の実行状態を先に照合し、完了不明の作業を自動再実行しない。
