# Deployment (Cloudflare Pages + D1)

## Prerequisites

- Cloudflare account (akaprantikdas@gmail.com)
- The **global API key** `cfk_30U3...` (NOT an API token — this is the Pages global key, used with `X-Auth-Email` + `X-Auth-Key` headers)
- GitHub repo: `sujitbhai7710/ssc-vocab-master`
- Node.js 18+, Python 3.9+ (only for data pipeline)

## One-time setup (already done — for reference)

### 1. Create the Pages project
```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACC/pages/projects" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $GLOBAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"sscpyqs","production_branch":"main"}'
```

### 2. Create the D1 database
See [DATABASE.md](./DATABASE.md). Database UUID: `9e974122-587f-41bc-93b1-fe95b8b1e022`.

### 3. Bind D1 to the Pages project (via wrangler.toml — NOT the API)
The binding is declared in `wrangler.toml`:
```toml
[[d1_databases]]
binding = "DB"
database_name = "ssc-vocab-db"
database_id = "9e974122-587f-41bc-93b1-fe95b8b1e022"
```
⚠️ Setting `deployment_configs.d1_databases` via the API does NOT persist — it must be in `wrangler.toml`. The worker reads it as `ctx.env.DB`.

### 4. Set the JWT_SECRET env var
Generate a secret:
```bash
python3 -c "import secrets;print(secrets.token_urlsafe(48))"
```
Set it on both production + preview:
```bash
JWT_SECRET="your-generated-secret"
curl -X PATCH "https://api.cloudflare.com/client/v4/accounts/$ACC/pages/projects/sscpyqs" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $GLOBAL_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"deployment_configs\":{\"production\":{\"env_vars\":{\"JWT_SECRET\":{\"type\":\"secret_text\",\"value\":\"$JWT_SECRET\"}}},\"preview\":{\"env_vars\":{\"JWT_SECRET\":{\"type\":\"secret_text\",\"value\":\"$JWT_SECRET\"}}}}}"
```

## Routine deploy

```bash
cd ssc-vocab-master
npm install
npm run build          # → dist/ (7,932 pages)
npx wrangler pages deploy ./dist --project-name=sscpyqs --commit-dirty=true
```

Environment vars for the deploy command (the global key + email):
```bash
export CLOUDFLARE_API_KEY="cfk_30U3..."
export CLOUDFLARE_EMAIL="akaprantikdas@gmail.com"
```

The deploy uploads static assets + the Functions bundle (worker code in `functions/`). The D1 binding + JWT_SECRET are already configured on the project.

## ⚠️ Common deployment gotchas

### 1. "error code: 1010" (Cloudflare blocks the request)
The default `Python-urllib` User-Agent is blocked. This affects the data-pipeline AI calls, not the deploy. Fix: add a browser User-Agent header (already done in `scripts/ai_helper.py`).

### 2. D1 binding not reaching the worker (`hasDB: false`)
If the worker throws error 1101 on DB-touching endpoints, the binding isn't active. Confirm:
- It's in `wrangler.toml` (not just set via API)
- You redeployed AFTER adding it to wrangler.toml
- Check with a debug endpoint: `curl https://sscpyqs.pages.dev/api/debug/env` (if present)

### 3. Cloudflare 524 timeout
The proxy kills requests >120s. Keep AI chunks small (3-5 PDF pages per chunk, 20-40 questions per batch).

### 4. Old project name
The site was renamed from `ssc-vocab-master` to `sscpyqs`. The old project (`ssc-vocab-master.pages.dev`) is deleted. The GitHub repo is still named `ssc-vocab-master` (only the Cloudflare project + domain changed).

## Local development

```bash
npm install
npm run dev    # → http://localhost:4321
```

Note: the worker (auth/problematic/progress) won't work locally without `wrangler pages dev` + a local D1. For frontend-only work, `npm run dev` is fine — the auth calls will 401 but pages render.

For full local testing with the worker:
```bash
npx wrangler pages dev ./dist --d1 DB=ssc-vocab-db
```

## URLs

| What | URL |
|------|-----|
| **Live site** | https://sscpyqs.pages.dev |
| **GitHub** | https://github.com/sujitbhai7710/ssc-vocab-master |
| **Cloudflare dashboard** | https://dash.cloudflare.com → Pages → sscpyqs |
| **D1 console** | https://dash.cloudflare.com → Workers & Pages → D1 → ssc-vocab-db |

## Rollback

Each `wrangler pages deploy` creates a deployment with a unique URL (e.g. `https://abc123.sscpyqs.pages.dev`). To rollback, go to the Cloudflare dashboard → sscpyqs → Deployments → promote a previous deployment to production.
