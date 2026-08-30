# tai — Protocol Reference

SKILL.md に置かない詳細をここに置く。日常の書式・手番・Gate は SKILL.md を見ること。

---

## 1. 設計思想

```text
Thread = intelligence / state   Architect セッション。Thread Tree はここにしか無い
File   = message                task.md / report.md
Git    = carrier                メッセージを両者から見える場所へ運ぶ
Bridge = transport              「届いた」の 1 行だけを知らせる（Phase 1）
tai = protocol               書式・手番・Gate の規約
```

目的は、すでに成立している「Architect → Worker → Architect」のループから
**人間によるメッセージ運搬だけを除去する**こと。新しい中央オーケストレーターを作ることではない。

### Thread Tree

ツリーの形は固定ではなく、会話の中で流動的に生成・回収・分岐される。

```text
Main
├─ A
│  ├─ A1
│  └─ A2
├─ B
└─ C
```

**この動的構造の Source of Truth は Architect Thread。**
task.md の `## 現在位置` はその投影であり、読み戻して状態を復元する対象ではない。
次の task.md では Architect が自分の文脈から書き直す。差分更新もしない。

---

## 2. Stable Point

> 定義：現在の結果を次工程の前提として採用しても、大きく巻き戻す可能性が十分低い地点。

- 「作業終了」と同義ではない。
- 重要な判定タイミングは **report 受領後、次の task を書いてよいか**。
- ファイルへ永続化しなくてよい。Architect の Thread Tree で管理できているならそれを優先する。

```text
Stable Point ≠ Git Commit
```

report ごとに commit は存在するが、毎回 Stable Point ではない。
commit は「巻き戻し先の候補」として使えるだけで、採用判断は別。

Stable Point を破棄する（＝そこまで巻き戻す）ときは User Arbitration が要る（下記 C）。

---

## 3. User Arbitration

> 既存の目的・設計・Stable Point から合理的に導ける次工程なら自律進行可能。
> 新しい価値判断が必要なら USER へ裁定を要求する。

### 必要になりやすい条件

| | 条件 | 例 |
|---|---|---|
| A | 目的変更 | 作るものの定義が変わる |
| B | 設計上の価値判断 | 性能 vs 安定性、シンプルさ vs 機能性、精度 vs コスト |
| C | Stable Point の破棄 | 採用済みの前提を捨てて作り直す |
| D | 大きな不可逆変更 | 大規模再設計、データ削除、公開、デプロイ |
| E | USER 固有の意図が必要 | 好み、優先順位、外部事情 |

### 分岐と混同しない

```text
実装
├─ コンパイルエラー調査
├─ 修正
└─ 再検証
```

これは自律処理可能。停止条件は Branch の発生ではなく **Decision requiring human preference**。

裁定要求は Architect セッション内で「質問して待機」することで表現する。
別チャネル（Slack 等）への通知は MVP に含めない。

---

## 4. 停止時の提示書式（§25）

「どうしますか？」だけの問いかけは禁止。次を簡潔に提示する。

```markdown
USER ARBITRATION REQUIRED

現在地      : <Thread Tree のどこか>
完了したこと: <直近 report の要点>
停止理由    : <A〜E のどれに該当するか>
決めること  : <一文で>

選択肢
  1. <案>  — <意味・トレードオフ>
  2. <案>  — <意味・トレードオフ>

推奨: <明確なものがあれば。無ければ「無し」と書く>
差分: branch=claude/T-023 commit=4f2a9c1
```

- USER の判断を誘導しすぎない。推奨が無いなら無いと書く。
- **モバイルで読まれる前提。** 長い diff や全文引用を貼らない。
  `branch` / `commit` を示し「Web UI の diff ビューで確認可能」と添える。

---

## 5. Autonomy Preset

`.ai/config.yaml` の `default_autonomy` に Preset 名を書く。
これは default 値であり、Architect は枝ごとに上書きしてよい。

| Gate | MANUAL | TASK_BOUNDARY | GIT_BOUNDARY | AUTONOMOUS_UNTIL_ARBITRATION |
|---|---|---|---|---|
| `task_start` | confirm | auto | auto | auto |
| `next_task` | confirm | **confirm** | auto | auto |
| `branching` | confirm | auto_until_arbitration | auto_until_arbitration | auto_until_arbitration |
| `commit` | confirm | auto | **confirm** | auto |
| `push` | confirm | confirm | confirm | confirm |

- **TASK_BOUNDARY** — task 境界ごとに USER が確認する。導入時の既定。
- **GIT_BOUNDARY** — 実装は自律、main 取り込みで止まる。
- **AUTONOMOUS_UNTIL_ARBITRATION** — 主要な自律モード。裁定が要る地点だけ止まる。

`commit` / `push` の意味は SKILL.md §4 の責務境界を参照。

```text
commit  ＝ ローカル main への取り込み（merge）
push    ＝ origin への反映全般（main の push、PR 作成、マージ）
```

`claude/*` ブランチへの commit / push は Gate 非適用で常に許可する。
Gate が制御するのは、ローカル main への merge と origin への反映だけ。
境界の考え方は §8 を参照。

どの Preset でも User Arbitration は Gate ではなく**イベント**であり、
条件 A〜E に該当したら Policy に関わらず停止する。

---

## 6. 作ってはいけないもの

| | 禁止 |
|---|---|
| NG1 | 巨大なマルチエージェントフレームワーク |
| NG2 | Thread Tree を別 DB / 別ファイルで完全複製する |
| NG3 | Architect とは別の中央意思決定 AI |
| NG4 | 複雑なイベントバス |
| NG5 | Redis / Kafka 等の導入 |
| NG6 | ファイル内容を Bridge 自身が LLM で判断する |
| NG7 | 毎回巨大な JSON メッセージを生成する |
| NG8 | 既存の Architect スレッドの文脈管理を置き換える |
| NG9 | ブラウザ自動操作を Core Transport にする |
| NG10 | Architect を Routine（毎回新規セッション）で実装する |
| NG11 | report.md の本文をセッションキューに流し込む（通知は 1 行） |
| NG12 | 現場監督に判断させない。規約適合の機械チェックを超える評価・推奨・起案を現場監督に負わせた時点で、Architect が二重化し NG3 に帰着する |
| NG13 | チャットへの書き込みを非公式手段（ブラウザ拡張・自動操作・非公開 API 等）で実現しない。NG9 の系。プラットフォームの公式機能を待つ |

常に「この機能は本当に必要か？」を確認し、最小構成を維持する。

---

## 7. 理想状態

通常時、USER は Architect とだけ対話する。

```text
USER → Architect → Worker → Architect → Worker → ...
```

USER が介入するのは、その時点の Autonomy Policy が指定した Gate と、
User Arbitration が発生した地点だけ。

> USER は伝令係ではなく、必要な地点でのみ意思決定者になる

---

## 8. 補足規則

### Gate の境界は取り消しにくさで引く

Gate の境界は Git の操作名（merge / PR）ではなく、**取り消しの難易度**で引く。

```text
ローカルに閉じている  → git reset で戻せる       → commit Gate
origin へ出た        → 戻すには force が要る     → push Gate
```

- **commit Gate** ＝ ローカル main への取り込み（merge）
- **push Gate** ＝ origin への反映全般（main の push、PR 作成、マージ）

`claude/*` ブランチへの push だけは Gate 非適用のまま残す。これは report.md の運搬経路そのもので、
ここを止めるとループが成立しない。取り消しにくさで言えば origin 側だが、Worker 専用ブランチであり
main に影響しないため例外として扱う。

### 実装 commit が存在しない task の report commit

記録のみ等、実装 commit が存在しない task では、report の `commit:` に
Worker ブランチの分岐元 main HEAD（短縮 7 桁）を記入する。`commit:` は必須フィールド
（SKILL.md §3）であり、実装が無いことを理由に空欄にはしない。分岐元 main HEAD を
書くことで、二重実行防止（SKILL.md §5）の判定キー `(task_id, revision, commit)` が
従来どおり一意に定まる。

### 現場監督の「main 無変更」チェックの基準

現場監督が report を確認する際の「main 無変更」チェック（SKILL.md §0 項 2）は、
task.md の反映（`claude/architect` の ff-only merge）による main の前進を「変更」と
みなさない。判定は merge-base 基準で行う。

```bash
git merge-base origin/main origin/claude/<task_id>
```

の結果が、Worker のブランチが分岐した時点の main HEAD と一致していれば、
その後 main が task.md 反映で前進していても「Worker が main を変更した」ことにはならない。
Worker のブランチ上のコミットのみが差分として現れているかどうかで判定する。

### main への取り込み時に task/report をプレースホルダへ戻す

main への取り込み（commit Gate 通過）時、main 上で `.ai/task.md` と `.ai/report.md` を
プレースホルダへ戻す。配布物に前 task の内容を残さないため。取り込み・push・
プレースホルダ戻しの 3 手順は 1 つの定型として扱い、origin/main への反映完了を
次 task 発行の開始条件とする。

### 規約ファイル・スクリプトの保守は tai の適用外（self-hosting の除外）

`.claude/skills/tai/` 配下（規約文書・テンプレート・スクリプト）の保守は、
tai の往復（task.md / report.md）ではなく**直接編集**で行う。Architect が完成版
ファイルを作り、USER がローカルへ配置して sha 照合（SKILL.md §1 のペイロード規約）の
うえ commit / push する。

**理由：self-hosting は利得が構造的に無い。** `.claude/` 配下は headless Worker から
書き込めない（プラットフォームのハード保護）ため、規約 task は必ず対話 Worker となり、
ブリッジによる自動往復の利得が最初から成立しない。tai の適用対象は**実装 task**である。