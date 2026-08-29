# SSC PYQs — Project Documentation

This folder contains everything a new developer (or AI agent) needs to understand, run, extend, and deploy the SSC PYQs platform. Read [`README.md`](./README.md) first, then dive into the specific guide you need.

## 📁 What's here

| File | Purpose |
|------|---------|
| **[README.md](./README.md)** | **Start here.** Project overview, tech stack, quick-start, feature list. |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | How the Astro frontend + Svelte islands + Pages Functions worker + D1 database fit together. Data flow diagrams. |
| **[DATABASE.md](./DATABASE.md)** | Cloudflare D1 schema, all tables/columns, how to create + migrate, how bindings work. |
| **[DATA_PIPELINE.md](./DATA_PIPELINE.md)** | How the grammar data (167 rules, 3,208 MCQs, narration, voice) was generated from the 3 PDFs + 23 PYQ text files using AI. Reproducible steps. |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | How to deploy to Cloudflare Pages + D1 from scratch. All the gotchas (global key vs API token, wrangler.toml bindings, env vars). |
| **[AUTH_SECURITY.md](./AUTH_SECURITY.md)** | How the login system works (PBKDF2 + JWT + httpOnly cookies), route gating, admin controls, security model. |
| **[CHANGELOG.md](./CHANGELOG.md)** | What changed across each development session (chronological). |
| **[FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md)** | Planned features (mock tests, custom test series, timer, auto-problematic from wrong answers) + how the DB schema already supports them. |

## 🚀 TL;DR for a new agent

1. **Live site:** https://sscpyqs.pages.dev
2. **GitHub:** https://github.com/sujitbhai7710/ssc-vocab-master
3. **Stack:** Astro 5 + Svelte 5 + Tailwind 3 → Cloudflare Pages (static) + Pages Functions (worker) + Cloudflare D1 (SQLite)
4. **First user to sign up becomes admin** (then signups can be disabled from `/admin`)
5. **Only `/`, `/login`, `/signup` are public** — everything else requires login (route-gated client-side + server-side)
6. **Data is pre-built JSON** in `public/data/` — the frontend fetches it at runtime; the worker (D1) only handles user-specific data (auth, problematic, progress)
7. **To regenerate grammar data:** see `DATA_PIPELINE.md` + `scripts/` (needs a Justwoker AI API key)
8. **To deploy:** `npm run build && npx wrangler pages deploy ./dist --project-name=sscpyqs` (see `DEPLOYMENT.md` for D1 binding setup)

## 🔑 Credentials & secrets

- **Cloudflare account:** akaprantikdas@gmail.com (account ID in `DEPLOYMENT.md`)
- **Cloudflare global key:** `cfk_30U3...` (used for Pages deploy + D1 management via X-Auth-Email/X-Auth-Key headers — NOT a Bearer token)
- **GitHub PAT:** `ghp_TBl9...` (push access to the repo)
- **Justwoker AI keys:** 2 keys for the data pipeline (see `scripts/.env.example`)
- **JWT_SECRET:** stored as a Cloudflare Pages env var (set via dashboard/API, never in code)

⚠️ **Never commit secrets.** The `.gitignore` blocks `.env`, `jwt_secret.txt`, and `.wrangler/`. The `scripts/ai_helper.py` reads keys from env vars only.
