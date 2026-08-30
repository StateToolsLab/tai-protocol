#!/usr/bin/env bash
# bridge-poll.sh — ローカルで常駐させるポーリングスクリプト（SKILL.md §15.7）。
#
# 責務は次の 3 つのみ。判断・評価・再送はしない。
#   (a) origin/claude/architect の検知 → main へ ff-only merge + push → Worker 起動
#   (b) origin/claude/T-* の report.md 検知 → notify-architect.sh を呼ぶ
#   (c) 処理済み位置を .ai/.bridge-state に記録（再起動後の重複防止）
#
# Task Start Gate = auto の実装である。confirm 運用時は (a) を無効化するフラグ
# --no-autostart を使う（USER が手動で claude/architect を main へ取り込む運用に切り替わる）。
#
# 使い方: bash bridge-poll.sh [間隔秒（既定 30）] [--no-autostart]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTIFY_SCRIPT="$SCRIPT_DIR/notify-architect.sh"

cd "$(git rev-parse --show-toplevel)" || { echo "[bridge] git リポジトリの外です" >&2; exit 1; }

STATE_FILE=".ai/.bridge-state"
PID_FILE=".ai/.bridge.pid"
INTERVAL=30
NO_AUTOSTART=0

for arg in "$@"; do
  case "$arg" in
    --no-autostart)
      NO_AUTOSTART=1
      ;;
    *[!0-9]*|"")
      echo "[bridge] 不明な引数: $arg" >&2
      echo "使い方: bash bridge-poll.sh [間隔秒] [--no-autostart]" >&2
      exit 1
      ;;
    *)
      INTERVAL="$arg"
      ;;
  esac
done

# --- 多重起動排他 ---------------------------------------------------------
if [ -f "$PID_FILE" ]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
    echo "[bridge] 既に起動しています（pid=$old_pid, $PID_FILE）" >&2
    exit 1
  fi
  echo "[bridge] 古い pidfile を検出（pid=${old_pid:-不明} は生存していません）。上書きします" >&2
fi
echo "$$" > "$PID_FILE"

cleanup_pidfile() {
  rm -f "$PID_FILE"
}

# INT / TERM を区別してログに残す（どちらも停止動作は同じ）。
# 受信したシグナル種別が分かれば、意図的な Ctrl-C 停止と外部要因による
# 停止とを事後に見分けやすくなる。
trap 'echo; echo "[bridge] SIGINT を受信し停止します"; cleanup_pidfile; exit 0' INT
trap 'echo; echo "[bridge] SIGTERM を受信し停止します"; cleanup_pidfile; exit 0' TERM
trap 'cleanup_pidfile' EXIT

# --- state helpers ------------------------------------------------------
state_get() {
  grep -E "^$1=" "$STATE_FILE" 2>/dev/null | tail -1 | cut -d= -f2-
}

state_set() {
  local key="$1" value="$2" tmp
  tmp="${STATE_FILE}.tmp.$$"
  { [ -f "$STATE_FILE" ] && grep -vE "^$key=" "$STATE_FILE"; echo "$key=$value"; } > "$tmp"
  mv "$tmp" "$STATE_FILE"
}

state_has() {
  grep -qE "^$1=" "$STATE_FILE" 2>/dev/null
}

frontmatter_field() {
  # $1=file $2=key
  sed -n '2,/^---$/p' "$1" | sed '$d' | grep -E "^$2:" | head -1 | sed -E "s/^$2:[[:space:]]*//"
}

# --- init: 初回起動時は現在の origin の状態を処理済みとして記録する ------
init_state_if_missing() {
  [ -f "$STATE_FILE" ] && return
  echo "[bridge] 初期化: 現在の origin の状態を処理済みとして記録します（過去の履歴には遡りません）"
  : > "$STATE_FILE"
  local arch_sha
  arch_sha="$(git rev-parse --verify -q origin/claude/architect 2>/dev/null || true)"
  state_set architect_sha "$arch_sha"
  local ref sha
  while IFS= read -r ref; do
    [ -n "$ref" ] || continue
    sha="$(git rev-parse "$ref" 2>/dev/null)" || continue
    state_set "branch_sha:$ref" "$sha"
  done < <(git for-each-ref --format='%(refname:short)' 'refs/remotes/origin/claude/T-*' 2>/dev/null)
}

# --- (a) origin/claude/architect の検知と Worker 起動 --------------------
handle_architect() {
  [ "$NO_AUTOSTART" = "1" ] && return

  git rev-parse --verify -q origin/claude/architect >/dev/null 2>&1 || return

  local new_sha old_sha
  new_sha="$(git rev-parse origin/claude/architect)"
  old_sha="$(state_get architect_sha)"
  [ "$new_sha" = "$old_sha" ] && return

  echo "[bridge] origin/claude/architect 更新検知: ${old_sha:-<none>} -> $new_sha"

  if ! git checkout main >/dev/null 2>&1; then
    echo "[bridge] エラー: git checkout main に失敗。このイベントをスキップします" >&2
    return
  fi

  # ff 失敗ループ抑止:
  # architect_sha は失敗時に更新されないため、放置すると 30 秒ごとに同じ失敗を
  # 再検知してログが流れ続ける（T-018/T-019 境界で実測）。同じ new_sha の失敗は
  # 1 回だけ USER に通知し、以後は静かに再試行だけ行う。main 側が解消されれば
  # merge が通り、失敗状態は自動でクリアされる。
  if ! git merge --ff-only origin/claude/architect >/dev/null 2>&1; then
    local failed_sha
    failed_sha="$(state_get architect_ff_failed)"
    if [ "$new_sha" != "$failed_sha" ]; then
      echo "[bridge] エラー: git merge --ff-only origin/claude/architect に失敗。main と claude/architect が分岐しています。USER の解消（main の push 完了）が必要です。解消まで同一イベントの再通知を抑止します" >&2
      state_set architect_ff_failed "$new_sha"
    fi
    return
  fi
  state_set architect_ff_failed ""

  if ! git push origin main; then
    echo "[bridge] エラー: git push origin main に失敗。このイベントをスキップします" >&2
    return
  fi

  state_set architect_sha "$new_sha"

  local status task_id model
  status="$(frontmatter_field .ai/task.md status)"
  task_id="$(frontmatter_field .ai/task.md task_id)"
  model="$(frontmatter_field .ai/task.md model)"
  [ -n "$model" ] || model="sonnet"

  if [ "$status" != "active" ]; then
    echo "[bridge] .ai/task.md の status=$status のため Worker を起動しません"
    return
  fi

  # 前回 revision の残骸ブランチを土台にした commit 履歴の不整合防止
  # （T-015 r3 で実際に発生）。Worker 起動前に必ず作り直す。
  if git show-ref --verify --quiet "refs/heads/claude/${task_id}"; then
    echo "[bridge] 残存するローカルブランチ claude/${task_id} を削除します"
    git branch -D "claude/${task_id}" >/dev/null 2>&1
  fi

  echo "[bridge] Worker 起動: $task_id ($model)"
  # --dangerously-skip-permissions は使わない。Worker の権限は編集と git に限定する
  # claude/<task_id> は使い捨てブランチ（§5: Architect は revision 単位で判定するため旧内容に
  # 意味は無い）。ローカルを作り直した後の push が旧 revision の残骸で non-fast-forward に
  # なる場合は --force-with-lease で上書きしてよい、と Worker に伝える。
  claude -p "Read .ai/task.md, execute the task, then write .ai/report.md and commit/push to the claude/${task_id} branch. Do not touch main. The claude/${task_id} branch is disposable; if a plain push is rejected as non-fast-forward because of leftover commits from a previous revision, use git push --force-with-lease to overwrite it." --model "$model" --allowedTools "Edit,Write,Read,Glob,Grep,Bash(git *),Bash(uname *),Bash(file *),Bash(bash -n *),Bash(head *),Bash(od *),Bash(printenv *),Bash(cat *),Bash(ls *),Bash(shasum *)"
  echo "[bridge] Worker 終了: $task_id (exit=$?)"

  git checkout main >/dev/null 2>&1
}

# --- (b) origin/claude/T-* の report.md 検知と通知 ------------------------
handle_reports() {
  local ref
  while IFS= read -r ref; do
    [ -n "$ref" ] || continue

    local sha old_sha
    sha="$(git rev-parse "$ref" 2>/dev/null)" || continue
    old_sha="$(state_get "branch_sha:$ref")"
    [ "$sha" = "$old_sha" ] && continue

    if ! git cat-file -e "$sha:.ai/report.md" 2>/dev/null; then
      # report.md がまだ無い commit。次回以降の変化を待つ（state は進めない）
      continue
    fi

    local tmp_report
    tmp_report="$(mktemp)"
    git show "$sha:.ai/report.md" > "$tmp_report"

    local task_id revision commit notify_key
    task_id="$(frontmatter_field "$tmp_report" task_id)"
    revision="$(frontmatter_field "$tmp_report" revision)"
    commit="$(frontmatter_field "$tmp_report" commit)"
    notify_key="notified:${task_id}:${revision}:${commit}"

    if state_has "$notify_key"; then
      rm -f "$tmp_report"
      state_set "branch_sha:$ref" "$sha"
      continue
    fi

    echo "[bridge] report 検知: $ref ($sha)"
    "$NOTIFY_SCRIPT" "$tmp_report" || echo "[bridge] notify-architect.sh が失敗しましたが再送はしません" >&2
    rm -f "$tmp_report"

    state_set "$notify_key" 1
    state_set "branch_sha:$ref" "$sha"
  done < <(git for-each-ref --format='%(refname:short)' 'refs/remotes/origin/claude/T-*' 2>/dev/null)
}

# --- main loop ------------------------------------------------------------
echo "[bridge] 起動: interval=${INTERVAL}s no_autostart=${NO_AUTOSTART} pid=$$"

# DNS 一時失敗等で git fetch が長時間ハングすると、外部要因のシグナルと
# 重なって停止したのか単なる一時失敗か区別しづらくなる。timeout で上限を設け、ハングを防ぐ。
FETCH_TIMEOUT=30

# macOS 標準環境には GNU coreutils の `timeout` が無いことがある（Homebrew
# coreutils 経由なら `gtimeout` として入る）。無ければ timeout なしで実行する。
if command -v timeout >/dev/null 2>&1; then
  TIMEOUT_BIN="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_BIN="gtimeout"
else
  TIMEOUT_BIN=""
fi

run_with_timeout() {
  local secs="$1"; shift
  if [ -n "$TIMEOUT_BIN" ]; then
    "$TIMEOUT_BIN" "$secs" "$@"
  else
    "$@"
  fi
}

run_with_timeout "$FETCH_TIMEOUT" git fetch origin --quiet 2>&1 || echo "[bridge] 初回 fetch に失敗しました" >&2
init_state_if_missing

while true; do
  if run_with_timeout "$FETCH_TIMEOUT" git fetch origin --quiet 2>&1; then
    handle_architect
    handle_reports
  else
    echo "[bridge] git fetch に失敗しました。次回リトライします" >&2
  fi
  sleep "$INTERVAL"
done
