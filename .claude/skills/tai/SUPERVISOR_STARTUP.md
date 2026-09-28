# Supervisor Startup / Rebinding

目的: コンテキスト圧縮、セッション再開、担当交代の後でも、会話上の自己申告ではなく外部状態から
Supervisor（現場監督）の役割と現在形を再構成する。

> Role memory is not authority. Rebind from external state before acting.

## 1. 毎便の冒頭で行う

新しいTask/Report/Gateを扱う前、またはコンテキスト圧縮・再接続・セッション交代の後は、
書込み・push・Gate操作より先にこの手順を実行する。

1. プラットフォームが提供する方法で**自分自身の現在のセッションID**を取得する。
   チャット本文、前ターンの自己申告、セッション名の記憶を根拠にしない。
2. この案件で承認された**Role Binding Source**を読み直す。
3. 自分のセッションIDと、Role Binding Sourceが示すSupervisor IDを一致確認する。
4. Gitの現在形をfetch後の実体から読み直す。
5. Task / Report / Gate / 実行中処理の状態と矛盾がないことを確認してから役割を再開する。

IDを取得できない、bindingが空・不明、IDが一致しない、複数の正本が矛盾する場合は
**Supervisorとしての副作用を開始しない**。自己判断でIDを書き換えたり、自分をSupervisorに任命しない。
「role binding unverified」としてUSER / Ownerへ返す。

## 2. Role Binding Source

Role Binding Sourceはデプロイ時にOwnerが明示する。

### repo-bound profile

案件運用で `.ai/config.yaml` の `supervisor_session` をSupervisorの役割バインド正本とする場合:

- `git fetch origin` 後、承認された基準refの `.ai/config.yaml` を読み直す。
- `supervisor_session` と自分のセッションIDが完全一致する場合だけSupervisorとして進む。
- 不一致時は、チャット上で「自分は現場監督です」と宣言されていても進まない。
- ID更新は交代手順として別の承認済み操作で行い、照合失敗を解消するために自分で書き換えない。

### environment-bound profile

公開同梱の通知実装は `SUPERVISOR_SESSION` を `.ai/config.yaml` より優先して宛先解決する。
この**通知ルーティング規則だけでは役割の権限を証明しない**。

環境変数をRole Binding Sourceとして採用するデプロイでは、その方針をOwnerが明示し、
自分のセッションIDと環境変数を比較する。configにもIDがあり両者が異なる場合は、
明示された優先規則と交代記録を確認できるまで停止する。

通知先、Role Binding Source、Task発行権限は別の概念として扱う。

## 3. Gitから「現在形」を再取得する

次はread-onlyの参考コマンド。環境の許可に合わせて同等の方法で取得する。

```bash
git fetch origin
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git status --short
git show origin/main:.ai/config.yaml
git show origin/main:.ai/task.md
git show origin/main:.ai/report.md
```

必要に応じてRecovery State、savepoint、起動キット、archive、対象Task/Reportの固定SHAも読む。
作業ツリーやチャットの記憶より、承認された固定refとGit上の実体を優先する。

最低限、以下を確認する。

- 期待するrepository / branch / main HEADである。
- shallow等で必要履歴が欠けていない。
- 現在のTask ID / revision / status、Report到着状況、承認待ちGateが分かる。
- 前任またはWorkerの実行中操作を完了扱いにしていない。
- 未commit変更、未push変更、origin/mainとの差分を「完了」という自己申告だけで無視していない。

## 4. fail closed

以下ではpush、merge、Task搬入、Gate実行、Worker再起動を行わない。

- Role Binding Sourceと自己IDが不一致。
- Git実体と引継ぎ文書が矛盾する。
- chatの「完了」「push済み」等とGitの状態が食い違う。
- 実行中処理・外部副作用の完了が不明。
- 必要な固定SHAや文書を取得できない。

これは「記憶が正しいか」を検査する手順ではなく、**記憶を権限・完了証拠として使わない**手順である。

## 5. 汎用Coreへの対応

他エンジン・他チャネルでも同じ原則を使う。

```text
self-reported role
       X
       |
external role binding + durable state
       |
       v
re-established role -> bounded action
```

各Adapterは、Role Binding Source、自分のruntime identityの取得方法、現在形の確認先、
不一致時の停止方法を明示する。
