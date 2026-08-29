#!/usr/bin/env bash
# scripts/migrate_mock_test_tables.sh
# Adds the mock test tables (test_configs, test_attempts, test_results) to the live D1 database.
#
# Usage:
#   ACCOUNT_ID="448154c5d61fdb71ea8a752b5bcb3b3d" \
#   DB_UUID="9e974122-587f-41bc-93b1-fe95b8b1e022" \
#   GLOBAL_KEY="cfk_..." \
#   EMAIL="akaprantikdas@gmail.com" \
#   bash scripts/migrate_mock_test_tables.sh
#
# All statements use CREATE TABLE IF NOT EXISTS so this is safe to run multiple times.

set -euo pipefail

: "${ACCOUNT_ID:?ACCOUNT_ID env var required}"
: "${DB_UUID:?DB_UUID env var required}"
: "${GLOBAL_KEY:?GLOBAL_KEY env var required}"
: "${EMAIL:?EMAIL env var required}"

API="https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/d1/database/${DB_UUID}/query"

# We send each statement separately so a partial failure doesn't abort everything.
SQL_STATEMENTS=(
  # Saved custom test configs
  "CREATE TABLE IF NOT EXISTS test_configs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, config TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);"
  "CREATE INDEX IF NOT EXISTS idx_testcfg_user ON test_configs(user_id);"

  # Test attempts (each run of a test)
  "CREATE TABLE IF NOT EXISTS test_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, config TEXT NOT NULL, question_ids TEXT NOT NULL, total INTEGER NOT NULL, started_at INTEGER NOT NULL, finished_at INTEGER, score INTEGER, timer_minutes INTEGER);"
  "CREATE INDEX IF NOT EXISTS idx_testatt_user ON test_attempts(user_id);"
  "CREATE INDEX IF NOT EXISTS idx_testatt_user_finished ON test_attempts(user_id, finished_at);"

  # Per-question results
  "CREATE TABLE IF NOT EXISTS test_results (attempt_id INTEGER NOT NULL, question_idx INTEGER NOT NULL, question_type TEXT NOT NULL, question_id TEXT NOT NULL, item_key TEXT, category TEXT NOT NULL, selected_idx INTEGER, correct_idx INTEGER NOT NULL, is_correct INTEGER NOT NULL, time_ms INTEGER, PRIMARY KEY (attempt_id, question_idx));"
  "CREATE INDEX IF NOT EXISTS idx_testres_attempt ON test_results(attempt_id);"
)

echo "Running ${#SQL_STATEMENTS[@]} statements against D1 database ${DB_UUID}..."

i=0
for stmt in "${SQL_STATEMENTS[@]}"; do
  i=$((i + 1))
  echo "  [${i}/${#SQL_STATEMENTS[@]}] ${stmt:0:80}..."
  ESCAPED=$(python3 -c "import sys, json; print(json.dumps(sys.stdin.read()))" <<< "$stmt")
  RESULT=$(curl -sS -X POST "$API" \
    -H "X-Auth-Email: ${EMAIL}" \
    -H "X-Auth-Key: ${GLOBAL_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"sql\":${ESCAPED}}")
  if echo "$RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); sys.exit(0 if d.get('success') else 1)"; then
    echo "    ✓ OK"
  else
    echo "    ✗ FAILED: $RESULT"
    exit 1
  fi
done

echo ""
echo "✅ All mock test tables created. Schema is now ready for the /api/test/* endpoints."
