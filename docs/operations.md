# 運用規約 — 文書の保全と独立検証

本書は[Core](protocol.md)のGitアダプター向け手順。
コマンド中の `<...>` は実値に置き換える。実行前に権限と対象を確認する。

## 1. Task原文を残す

`.ai/task.md` は現在の実行窓口。保存物は `.ai/archive/T-XXX_task_rN.md`。
保存するのはWorkerへ渡した発行commitの `.ai/task.md` であり、プレースホルダーや草稿ではない。
Architectのチャット原文は起草元として区別する。Supervisorがファイル化・保存・搬入した
発行正本の完全SHA、起草元の参照、固定前の整形記録をStateまたは既存の引継ぎ文書へ残す。
`status: active` を `completed` に変える等、保存時のfrontmatter追記・本文整形をしない。
完了・取消・失効はState / Decisionへ別に記録する。

通常はSupervisorがGate時、窓口をプレースホルダーへ戻す前に複写する。
ただし、**Gateに達する前の差戻し・revision更新・取消でも、旧版を消す前に保存する**。
全発行revisionを保存し、同じファイル名の異なる内容を上書きしない。
発行からGateまでの間も、固定commit等で原文を取得可能に保つ。
配布 `.gitattributes` のarchive規則を導入し、保存TaskへのGit改行変換・clean filterを無効にする。
独自のattributes設定がある場合は優先順位を確認し、commit後のblobも原文ハッシュと照合する。

```bash
python scripts/task_archive.py
python scripts/task_archive.py --expected-sha256 <発行側で確定した64桁のSHA256>
```

既定入力は作業ツリーの窓口なので、先に発行commitのblobと一致することを確認する。
作業ツリーの改行変換や後続編集で異なる場合は停止し、発行commitから取得した正本を使う。
最初のコマンドは現在の窓口と保存物の同一性を保証するだけで、発行者の原意は保証しない。
2つ目は独立に渡された原文のハッシュとも比較する。ハッシュを転送後の同じファイルから
作り直しても、上流で発生した改変は検出できない。
期待ハッシュの対象が「起草元」か「発行正本」かを明記する。承認済み整形で両者が異なるとき、
同じハッシュで双方を検証したとは扱わない。archive照合の対象は発行正本のバイト列である。

ヘルパーはPython 3.9以上の標準ライブラリのみを使う。Taskを読み、原文を保ったまま
保存する。同一内容での再実行は成功扱い、異なる内容との衝突・不正なID・不正なrevision・
プレースホルダー・期待ハッシュ不一致はエラー。既存ファイルへの上書きは行わない。
同一ディレクトリ内の一時ファイルとhard linkによる排他的公開を使うため、
hard link非対応のストレージではエラーで停止する。単一の権限ある書き手を前提とし、
敵対的な共有ファイルシステムへの防御や分散トランザクションは提供しない。

ヘルパー自身はリセット、Git操作、Gate承認、Agent起動をしない。
既定のClaude headless WorkerにPython実行許可があるとは限らない。Supervisor側の
許可された環境で実行するか、同じ原則を満たす手動複写・照合を行う。

## 2. Gateでの一体処理

ブリッジと共有作業ツリーを同時に操作しない。ブリッジを停止し、Workerの終了、
作業ツリーの状態、承認対象の固定SHAを確認する。実装の統合とcleanupは別commitでよい。
ただし**Taskのarchive作成とtask/report窓口のリセットは同じcleanup commitにする**。
以下の `--no-ff` は同梱Gitアダプターの既定例であり、Core共通の要件ではない。
案件で承認済みのff統合を使っている場合、今回の照合を理由に無断で方式を変えない。
いずれも承認対象・Reportの到達可能性・cleanup先端を照合する。

1. Reportと全変更を検証し、必要なcommit / push Gateの承認を得る。
2. 承認済みのReport先端SHAをローカルmainへ `--no-ff` で統合する。
3. Task原文をarchiveし、Reportを再取得できる固定参照と判断をStateへ記録する。
4. `.ai/task.md` と `.ai/report.md` を配布時の `status: none` の窓口に戻す。
5. archive・リセット・State更新を一つのcleanup commitへ含め、push Gateに従って反映する。

```bash
git merge --no-ff <承認済みReport先端の完全SHA>
python scripts/task_archive.py
# ここで文書編集機能によりStateを更新し、task/reportをプレースホルダーへ戻す。
git add .ai/archive/T-001_task_r1.md .ai/task.md .ai/report.md .ai/state.md
git diff --cached --stat
git diff --cached -- .ai/task.md .ai/report.md .ai/state.md
git commit -m "tai: archive T-001 r1 and reset handoff windows"
# push Gate通過後だけ実行する。
git push origin main
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

最後の2つの完全SHAが期待するcleanup commitと一致してから次Taskを搬入する。
既存手順の「merge commitだけの照合」では、cleanup未反映を見落とす。
途中失敗では次Taskを開始せず、archiveと窓口の実体を照合して復旧する。
差戻し時の旧revision保存は、新版への差替えと同じcommitに含める。

## 3. Reportは保存先を選べるが、失ってよいわけではない

Report commitが保持対象のmain履歴へ統合されていれば、その履歴を保存先として使える。
Architectのチャットだけに依存する必要も、Reportを別archiveへ二重保存する義務もない。
リポジトリ外の保存先を使う場合も、後任から取得可能な固定版を保持する。
状態文書には固定参照・保持条件を残す。窓口のプレースホルダー復帰と履歴の消失は別である。
Gitへ統合済みなら `<Report先端の完全SHA>:.ai/report.md` を参照として記録できる。
参照先commitを到達可能に保ち、アクセス権も維持する。

未統合ブランチは次revisionで書き換わる可能性がある。Reportを回収・保全する前に
ブランチを上書き・削除しない。必要なら別の文書ストアや追加archiveへ保全する。
リセット後の `origin/main:.ai/report.md` はプレースホルダーであり、過去Reportの取得先ではない。

## 4. diffの正本はSupervisorの独立取得

Workerの全文diff貼付は任意。省略する場合は省略したことと範囲をReportに明記する。
SupervisorはReport、実装commit、分岐元、変更範囲をGitから独立に取得してArchitectへ渡す。
Workerの貼付だけを完全な差分の証拠としない。

```bash
git fetch origin
git rev-parse origin/claude/T-001
git show <Report先端の完全SHA>:.ai/report.md
git show --stat --format="%h %s" <実装commit>
git show --format="%h %s" <実装commit> -- <対象パス>
```

`git show` 1回は原則1commitの表示であり、複数commitのTask全体とは限らない。
Task全体は承認対象の分岐元と実装先端を固定して、全変更パスと差分を取得する。

```bash
git diff --name-status <分岐元の完全SHA> <実装先端の完全SHA> -- .
git diff --stat <分岐元の完全SHA> <実装先端の完全SHA> -- .
git diff --no-ext-diff --binary <分岐元の完全SHA> <実装先端の完全SHA> -- .
```

Reportのみのcommitも別途確認し、Task改変や無関係なファイル混入がないか確認する。
バイナリやsubmodule、外部成果物はdiffだけで検証完了としない。
大きいdiffは省略表示で済ませず、固定版のファイルとして保存して参照・サイズ・SHA256を渡す。
分割して渡すなら対象範囲と総数を明示する。取得不能・検証不能はそのまま報告する。

**証拠のツール出力はそのまま貼付または固定ファイルで渡し、手書き転記・再生成しない。**
要約や解釈は原出力と別欄にする。SHA・行数・検算値・定義行も同様に扱う。
機密を除く必要がある場合は伏字等の処理と対象範囲を明記し、無加工の原証拠は許可された場所に保持する。
Workerによるコマンド置換等の逸脱もReportで申告する。自己申告は逸脱の事前許可を意味しない。

## 5. commit表示と個人情報

標準表示は上記の `--format="%h %s"` を使い、Authorやcommit本文のtrailerを表示しない。
これはGit履歴の作者情報を削除する操作でも、個人情報の完全な除去でもない。
件名・パス・diff本文に含まれるメール等は別途検査する。
検査対象（commitメタデータ、差分、成果物）を分けて件数を報告する。

## 6. ローカルmainの同期

Gate後に別の作業環境へ取り込む標準は次とする。

```bash
git fetch origin
git merge --ff-only origin/main
```

これは既に統合済みのorigin/mainとの**同期**であり、Task枝を `--no-ff` で統合する操作とは別。
共有作業ツリーのWorker / Bridgeと排他し、main上・意図した作業状態で実行する。
分岐時は停止し、勝手にreset・rebase・force-pushで解消しない。

fetchは既定でFETCH_HEADを書き換える。名前付きrefを指定するmergeは、FETCH_HEADへの
依存を避ける。ただしrefや作業ツリーのあらゆる並行更新との競合が消えるわけではない。
厳密な再現性が必要なら、fetch後に `git rev-parse origin/main` で得た完全SHAを記録し、
それを対象にmerge・照合する。過去のpull失敗の原因は観測だけで断定しない。

## 7. 発行テンプレートと原文照合

Git Taskの必須frontmatterは既存の5項目を維持し、`status: active` をテンプレートに含める。
Architectが完成形で出すことを原則とする。Supervisorの補完は、発行正本の固定前で、
明示的な発行指示と事前に認められた整形規則がある場合の未記入status補完などに限定する。
`status: none` や停止指示をactiveへ変更しない。補った箇所と根拠は搬入記録へ残す。
YAML体裁を整える場合も本文・値の意味を変えない。その他の不足値や曖昧さは差し戻す。
固定後に意味や内容を訂正・追加する場合はArchitectがrevisionを上げる。
過去に差異を受容してrevisionを変えなかった判断は、元の版と判断記録を保全し、遡及改変しない。

文書便・原文貼付型Taskでは、Architectが定義・閾値などの期待行を明示して照合させる。
たとえば、許可された環境で次を実行する。

```bash
grep -nF -x -- '閾値: 0.95' <成果物パス>
```

これはTaskから成果物への部分照合。**Architect原文からTask窓口への照合**とは分ける。
上流も含めた完全一致が要る場合、発行者がUTF-8等のエンコーディング、改行、末尾改行を
確定したファイルを渡し、その全バイトのSHA256を独立の発行記録で通知する。
受け手は正規化せず比較する。ハッシュを同じファイルに埋め込む自己参照方式は使わない。
本文ブロック単位のハッシュは、境界・符号化の規約を定めてから導入する将来拡張とする。

## 8. Workerのシェル能力

コマンドは実行環境に合わせて記す。制限されたheadless環境では、許可済みのコマンドを
一つずつ提示し、`for` / `case` / 環境変数前置き / リダイレクト等を当然に使えると仮定しない。
`git`、`python`、`grep`、`wc`、`sha256sum`、`ls`等も**実際に許可・導入されている場合だけ**使う。
`sha256sum`の代わりに `shasum -a 256` が必要な環境もある。

Pythonによる整形・繰り返しはPython実行自体が許可され、処理内容がTaskの権限内の場合に限る。
シェル制約を迂回するためのPython利用や、無差別な権限緩和はしない。
公開リポジトリ同梱ブリッジの起動allowlistにはPython・grep・wc・sha256sumは含まれない。
これは案件ローカルの実効許可一覧についての断定ではない。settingsと起動引数の実体を別途照合する。
このリリースはそれらを自動追加しない。必要な能力は発行前に検査し、権限不足なら
`blocked` Reportを返して停止する。対話実行や別Workerへの変更は明示的に承認された手順に限り、
SupervisorやBridgeが自動で権限・モデルを切り替えない。応答者のいないheadlessで質問待ちしない。

## 9. 運用提案の採否

| 提案 | 0.2での扱い |
|---|---|
| Taskのmain上archive | 採用。原文不変、全発行revision、差戻し・取消も保全 |
| 全文diffの独立取得 | 採用。複数commitではTask全範囲を追加確認 |
| 作者情報を出さないcommit表示 | 採用。個人情報除去の保証とは区別 |
| fetch + merge --ff-only | 採用。FETCH_HEAD依存の回避と一般的排他を区別 |
| statusをテンプレートに含める | 維持・徹底。公開v0.1.0のテンプレートにも既に存在 |
| 原文経路の崩れ検出 | 期待行＋独立ハッシュ。認証・全文一致・部分一致を区別 |
| 制約対応の素のコマンド | 環境依存の推奨。許可の検査とblocked処理が前提 |

## Gitの仕様参照

- [git-fetch](https://git-scm.com/docs/git-fetch): FETCH_HEADとrefの更新。
- [git-show](https://git-scm.com/docs/git-show) / [pretty-formats](https://git-scm.com/docs/pretty-formats): 表示対象と書式。
- [git-diff](https://git-scm.com/docs/git-diff): 2地点間の差分。
- [git-merge](https://git-scm.com/docs/git-merge): ff-onlyとno-ffの違い。
