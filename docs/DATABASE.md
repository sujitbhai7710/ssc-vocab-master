# Database (Cloudflare D1)

The app uses a single Cloudflare D1 database (`ssc-vocab-db`) for all user-specific data. Static content (vocab, grammar) lives in JSON files, NOT the database.

## Connection details

| Field | Value |
|-------|-------|
| **Database name** | `ssc-vocab-db` |
| **Database UUID** | `9e974122-587f-41bc-93b1-fe95b8b1e022` |
| **Binding name** | `DB` (in `wrangler.toml` → worker accesses via `ctx.env.DB`) |
| **Region** | APAC |
| **Cloudflare account** | akaprantikdas@gmail.com (account ID `448154c5d61fdb71ea8a752b5bcb3b3d`) |

## Schema

Full SQL: [`scripts/schema.sql`](../scripts/schema.sql)

```sql
-- Users (auth)
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,     -- PBKDF2-SHA256, base64
  salt TEXT NOT NULL,              -- 16 random hex bytes
  role TEXT NOT NULL DEFAULT 'user',  -- 'admin' or 'user'
  created_at INTEGER NOT NULL       -- epoch ms
);

-- Settings (key-value, admin-controlled)
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
-- Default row: ('signup_enabled', 'true')

-- Problematic items (user's "marked for revision" list)
CREATE TABLE problematic (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  item_type TEXT NOT NULL,         -- 'vocab' | 'root' | 'grammar-rule' | 'grammar-mcq' | 'narration' | 'voice'
  item_key TEXT NOT NULL,          -- the word/rule-id/section-id
  sub_type TEXT,                   -- e.g. 'syn-ant', topic name
  created_at INTEGER NOT NULL,
  UNIQUE(user_id, item_type, item_key)  -- no duplicates
);

-- Progress (read-till + completed index set, per page_type)
CREATE TABLE progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  page_type TEXT NOT NULL,         -- 'stems' | 'options' | 'ows' | 'idioms' | 'homonyms' | 'spelling' | 'roots' | 'grammar-rules' | 'narration' | 'voice'
  read_till INTEGER NOT NULL DEFAULT 0,
  completed TEXT,                  -- JSON array of completed indices, e.g. "[1,2,3,...,61]"
  updated_at INTEGER NOT NULL,
  UNIQUE(user_id, page_type)
);
```

## Creating the database from scratch

The `cfk_` global key works as `X-Auth-Email` + `X-Auth-Key` headers (NOT Bearer). Use the Cloudflare API:

```bash
ACCOUNT_ID="448154c5d61fdb71ea8a752b5bcb3b3d"
GLOBAL_KEY="cfk_30U3..."  # your global key
EMAIL="akaprantikdas@gmail.com"

# 1. Create the database
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/d1/database" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $GLOBAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"ssc-vocab-db"}'
# → returns UUID; note it.

# 2. Run the schema
DB_UUID="9e974122-..."  # from step 1
SCHEMA=$(cat scripts/schema.sql | python3 -c "import sys,json;print(json.dumps(sys.stdin.read()))")
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/d1/database/$DB_UUID/query" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $GLOBAL_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"sql\":$SCHEMA}"

# 3. Bind to the Pages project (MUST be in wrangler.toml — see below)
# 4. Set JWT_SECRET env var (see DEPLOYMENT.md)
```

## ⚠️ Critical: D1 binding via wrangler.toml

The D1 binding MUST be declared in `wrangler.toml` — setting it via the Cloudflare API (`deployment_configs.d1_databases`) does NOT persist and the worker won't see `ctx.env.DB`.

```toml
# wrangler.toml
name = "sscpyqs"
compatibility_date = "2024-12-01"
pages_build_output_dir = "./dist"

[[d1_databases]]
binding = "DB"
database_name = "ssc-vocab-db"
database_id = "9e974122-587f-41bc-93b1-fe95b8b1e022"
```

Also set `JWT_SECRET` as a Pages env var (production + preview) via the API or dashboard.

## Migrations

The schema was extended once (added `completed TEXT` column to `progress`). To run a migration:

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/d1/database/$DB_UUID/query" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $GLOBAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sql":"ALTER TABLE progress ADD COLUMN completed TEXT;"}'
```

Always update `scripts/schema.sql` to match after a migration.

## Querying the DB (ad-hoc)

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/d1/database/$DB_UUID/query" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $GLOBAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT id, email, role FROM users;"}'
```

## First-user-becomes-admin logic

In `functions/api/auth/signup.ts`:
```ts
const userCount = await ctx.env.DB.prepare('SELECT COUNT(*) as c FROM users').first();
const isEmpty = !userCount || userCount.c === 0;
// ...
const role = isEmpty ? 'admin' : 'user';
```

So the very first signup creates an admin. After that, the admin can disable signups from `/admin` (sets `settings.signup_enabled = 'false'`).

## item_type values (problematic table)

These are the categories used across the app — keep them consistent:

| item_type | What it marks | Set by |
|-----------|---------------|--------|
| `vocab` | A vocab word (syn/ant) | ProblematicButton on word cards |
| `root` | A root word family | ProblematicButton on RootsView |
| `grammar-rule` | A grammar rule | ProblematicButton on GrammarRulesView |
| `grammar-mcq` | An individual grammar MCQ | ProblematicButton on GrammarMCQCard |
| `narration` | A narration section | ProblematicButton on TopicRulesView |
| `voice` | A voice section | ProblematicButton on TopicRulesView |

## Future: mock test tables (not yet created)

The `completed` column in `progress` and the `problematic` table are designed to feed future mock tests. See [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) for the planned `test_attempts` and `test_results` tables.
