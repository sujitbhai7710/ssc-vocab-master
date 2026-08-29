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
