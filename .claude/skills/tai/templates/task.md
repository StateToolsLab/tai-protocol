---
task_id: T-NNN
revision: 1
status: active
commit: auto
push: confirm
model: sonnet      # 任意。省略時は sonnet。設計判断が要る task のみ opus
---

# Task

<Worker への具体的指示をここに自然言語で書く。
 命令の意味は本文に持たせる。過剰に構造化しない。>

## 現在位置

<Architect が保持する文脈の、この時点の投影。状態ではなく表示。
 形式は自由。Worker は読み取り専用でパースしない。>

Main
├─ A <枝の名前>            ✔ stable
└─ B <枝の名前>            ◀ このタスク

## 完了時

実装結果を `.ai/report.md` に報告し、`claude/T-NNN` ブランチへ commit / push すること。
実装と report は別 commit とし、report の `commit:` には実装の最終 commit（短縮 7 桁）を書くこと。
main への取り込み・PR 作成は行わないこと。
push 後に作業ツリーを main に戻すこと。