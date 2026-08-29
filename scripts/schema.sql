-- SSC Vocab Master — D1 schema
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
INSERT OR IGNORE INTO settings (key, value) VALUES ('signup_enabled', 'true');

CREATE TABLE IF NOT EXISTS problematic (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  item_type TEXT NOT NULL,
  item_key TEXT NOT NULL,
  sub_type TEXT,
  created_at INTEGER NOT NULL,
  UNIQUE(user_id, item_type, item_key)
);
CREATE INDEX IF NOT EXISTS idx_prob_user ON problematic(user_id);
CREATE INDEX IF NOT EXISTS idx_prob_user_type ON problematic(user_id, item_type);

CREATE TABLE IF NOT EXISTS progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  page_type TEXT NOT NULL,
  read_till INTEGER NOT NULL DEFAULT 0,
  completed TEXT,
  updated_at INTEGER NOT NULL,
  UNIQUE(user_id, page_type)
);
CREATE INDEX IF NOT EXISTS idx_prog_user ON progress(user_id);

-- ===== Mock Test tables (added in mock-test feature) =====
-- Saved custom test configurations (user can build & reuse these)
CREATE TABLE IF NOT EXISTS test_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  config TEXT NOT NULL,         -- JSON: { categories: [{type, min, max}], single_per_item, timer_minutes, shuffle }
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_testcfg_user ON test_configs(user_id);

-- Each test attempt (auto-generated or from a saved config)
CREATE TABLE IF NOT EXISTS test_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  config TEXT NOT NULL,         -- JSON snapshot of the config used (so old attempts remain accurate)
  question_ids TEXT NOT NULL,   -- JSON array of question refs: [{type, id, itemKey, category}]
  total INTEGER NOT NULL,
  started_at INTEGER NOT NULL,
  finished_at INTEGER,          -- NULL until submitted
  score INTEGER,                -- correct count (NULL until submitted)
  timer_minutes INTEGER         -- allotted duration (NULL = untimed)
);
CREATE INDEX IF NOT EXISTS idx_testatt_user ON test_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_testatt_user_finished ON test_attempts(user_id, finished_at);

-- Per-question results for each attempt
CREATE TABLE IF NOT EXISTS test_results (
  attempt_id INTEGER NOT NULL,
  question_idx INTEGER NOT NULL,    -- 0-based position in the test
  question_type TEXT NOT NULL,      -- 'vocab' | 'grammar' | 'narration' | 'voice'
  question_id TEXT NOT NULL,        -- numeric id (vocab) or string id (grammar/narration/voice)
  item_key TEXT,                    -- the underlying word/rule-id (for auto-problematic)
  category TEXT NOT NULL,           -- test category: 'syn-ant' | 'idiom' | 'spelling' | 'homonym' | 'ows' | 'grammar' | 'narration' | 'voice'
  selected_idx INTEGER,             -- NULL if not answered
  correct_idx INTEGER NOT NULL,
  is_correct INTEGER NOT NULL,      -- 0 or 1
  time_ms INTEGER,
  PRIMARY KEY (attempt_id, question_idx)
);
CREATE INDEX IF NOT EXISTS idx_testres_attempt ON test_results(attempt_id);
