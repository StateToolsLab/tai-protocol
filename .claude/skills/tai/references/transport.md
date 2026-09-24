# tai — Transport Reference（Claude Code / Gitアダプター）

Coreは運搬・エンジン非依存。本書と同梱shellスクリプトはClaude Code専用である。
以下の構成は公開v0.1.0の実装を維持するもので、他エンジンへの接続実装ではない。
2026-08に記録されたクラウド権限制約は歴史的な観測であり、現環境で導入前に確認する。

## 1. モデルと能力

既存 `bridge-poll.sh` はTaskの任意 `model` を `--model` へ渡し、省略時 `sonnet` を使う。
Architectのモデルは固定しない。モデル変更は権限を広げない。
簡易パーサーとの互換性のため値にinline commentや引用符を付けない。
必要な能力、書込み範囲、シェル許可、対話の要否を発行前に検査する。

## 2. 手動フォールバック

USERがTaskを文書として保存・照合してSupervisorへ渡し、Workerを手動起動できる。
モデル・Task IDは実値に置き換える。

```bash
claude --model sonnet "Read .claude/skills/tai/SKILL.md and .ai/task.md. Take the Worker role, execute only the issued task, then write .ai/report.md and commit/push to claude/T-001. Do not integrate main or create a PR."
```

権限・Task Start承認を先に確認する。`status: none` は実行しない。
Taskに対話実行指定がある場合、headlessへ渡さない。
共有作業ツリーで実行したWorkerはpush後にmainへ戻る。専用worktreeは独自の終了規約に従う。

通知のみのフォールバックは次の既存形式を維持する。

```text
[handoff] report.md updated task_id=T-001 revision=1 branch=claude/T-001 commit=<短縮7桁>
```

通知先はSupervisor。受け手がfetchして固定版のReportを取得する。
通知は承認でもReport保全でもない。ArchitectへのReport返送は既存経路を維持する。
自動返送アダプターを使う場合も、本文または固定参照の保持と取得可能性を別途保証する。

## 3. 通知ブリッジ

```bash
bash .claude/skills/tai/scripts/notify-architect.sh .ai/report.md
```

宛先は `SUPERVISOR_SESSION`、なければ `.ai/config.yaml` の `supervisor_session`。
同梱実装はfrontmatterから1行を作り、`claude -p --cloud` で送信する。
失敗時は手動転送用の通知行を表示する。自動再送・評価・Report本文配送は行わない。
ライブのセッションIDや認証情報を公開リポジトリへ保存しない。

## 4. Task搬入

従来のクラウド構成では `claude/architect` をcarrierにする。
前便の統合・cleanup・pushと旧Task / Reportの保全が済んでから、現在のorigin/mainを起点にする。

```bash
git fetch origin
git checkout -B claude/architect origin/main
# 発行済みTaskを原文のまま配置し、照合してcommitする。
git push origin claude/architect
```

過去のcarrierが残りnon-fast-forwardになる場合、安易な `push -f` は使わない。
旧版保全と他の書き手の不在を確認し、承認したremote先端SHAを明示した
`--force-with-lease=refs/heads/claude/architect:<期待する旧SHA>` を用いる。
許可されなければ停止し、USERへ返す。未知の変更を上書きしない。

Carrierのmainへのfast-forwardは従来どおりローカル側が行う。
この例外は認可されたTaskの運搬に限定し、実装のmain統合Gateと混同しない。
Carrierに想定外のファイルが含まれないかSupervisorが確認する。

## 5. ポーリングブリッジ

```bash
bash .claude/skills/tai/scripts/bridge-poll.sh 30
bash .claude/skills/tai/scripts/bridge-poll.sh 30 --no-autostart
```

1リポジトリ1プロセス。端末から起動し、他のセッションから重複起動しない。
初回は現在のoriginを処理済みとして記録するため、Task搬入前に起動する。
`--no-autostart` はTask搬入の自動取り込み・Worker起動を無効にし、Report通知を残す。
Task Startがconfirm、能力検査が未完了、Task原文が未保全ならこのモードまたは手動運用にする。

同梱Bridgeは次だけを実装する。

- carrier更新を検知し、mainへff-only merge / pushしてClaude Workerを起動する。
- `claude/T-*` のReport更新を検知し、既存通知スクリプトを呼ぶ。
- `.ai/.bridge-state` に処理済み位置を記録する。

共有作業ツリーの直列運用であり、並行Worker、全Gateの強制、予算管理、汎用ルーティング、
包括的な冪等性や自動archiveは実装していない。Supervisor / USERが運用で補完する。
復旧時は「処理済み」と「実行成功」を同一視せず、Task・Report・外部副作用を確認する。

既存allowlistは編集と列挙済みのGit・診断コマンド等に限定される。
Python・grep・wc・sha256sumは既定で含まれない。許可設定を推測せず、
[operations.md](../../../../docs/operations.md)の能力検査に従う。
`--dangerously-skip-permissions` による回避はしない。

Gate操作やローカルmain同期の間はBridgeとWorkerを停止・排他する。
同期は `git fetch origin` の後に `git merge --ff-only origin/main`。
Task枝の統合は別の承認済み `--no-ff` 操作である。
