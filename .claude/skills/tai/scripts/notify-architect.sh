#!/usr/bin/env bash
# notify-architect.sh — report.md 更新を現場監督セッション（Code クラウドセッション）へ 1 行で通知するだけの Bridge 本体。
# 判断・評価・Thread Tree 操作は一切行わない。送信は 1 回だけで、失敗しても再送しない（SKILL.md §15.5）。
set -euo pipefail

report_path="${1:-.ai/report.md}"
config_path=".ai/config.yaml"

# キーが無くても失敗にしない（set -o pipefail 下で grep の不一致が exit 1 になるため || true）
config_field() { { grep -E "^$1:" "$config_path" 2>/dev/null | head -1 | sed -E "s/^$1:[[:space:]]*//"; } || true; }

# 宛先の解決順: 環境変数 SUPERVISOR_SESSION > config の supervisor_session
supervisor_session="${SUPERVISOR_SESSION:-}"
[ -n "$supervisor_session" ] || supervisor_session="$(config_field supervisor_session)"
if [ -z "$supervisor_session" ]; then
  echo "supervisor_session が未設定" >&2
  exit 1
fi

frontmatter="$(sed -n '2,/^---$/p' "$report_path" | sed '$d')"
field() { echo "$frontmatter" | grep -E "^$1:" | head -1 | sed -E "s/^$1:[[:space:]]*//"; }

notification="[handoff] report.md updated task_id=$(field task_id) revision=$(field revision) branch=$(field branch) commit=$(field commit)"

result="$(claude -p "$notification" --cloud "$supervisor_session" --output-format json || echo '{"ok":false}')"

if echo "$result" | grep -q '"ok":[[:space:]]*true'; then
  echo "$notification"
  exit 0
fi

echo "送信失敗。以下を現場監督セッションに手で貼ってください:" >&2
echo "$notification"
exit 1
