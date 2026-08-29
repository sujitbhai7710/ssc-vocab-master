# SSC PYQs — Project Documentation

This folder contains everything a new developer (or AI agent) needs to understand, run, extend, and deploy the SSC PYQs platform. **Read [`PROJECT_GUIDE.md`](./PROJECT_GUIDE.md) first** — it's the single source of truth consolidating 8 sessions of work, then dive into the specific guide you need.

## 📁 What's here

| File | Purpose |
|------|---------|
| **[PROJECT_GUIDE.md](./PROJECT_GUIDE.md)** | **START HERE.** Single source of truth — consolidates everything from 8 sessions. Critical context, project structure, common pitfalls, how to extend. |
| **[README.md](./README.md)** | Project overview, tech stack, quick-start, feature list. |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | How the Astro frontend + Svelte islands + Pages Functions worker + D1 database fit together. Data flow diagrams. |
| **[DATABASE.md](./DATABASE.md)** | Cloudflare D1 schema (9 tables), how to create + migrate, how bindings work. |
| **[DATA_PIPELINE.md](./DATA_PIPELINE.md)** | How the grammar data (167 rules, 3,208 MCQs, narration, voice) was generated from the 3 PDFs + 23 PYQ text files using AI. Reproducible steps. |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | How to deploy to Cloudflare Pages + D1 from scratch. All the gotchas (global key vs API token, wrangler.toml bindings, env vars). |
| **[AUTH_SECURITY.md](./AUTH_SECURITY.md)** | How the login system works (PBKDF2 + JWT + httpOnly cookies), route gating, admin controls, security model. |
| **[CHANGELOG.md](./CHANGELOG.md)** | What changed across each of the 8 development sessions (chronological). |
| **[FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md)** | Mock test spec — now fully implemented (all 5 features marked ✅). Kept as implementation reference. |

## 🚀 TL;DR for a new agent

1. **Read [`PROJECT_GUIDE.md`](./PROJECT_GUIDE.md)** — it has everything you need
2. **Live site:** https://sscpyqs.pages.dev
3. **GitHub:** https://github.com/sujitbhai7710/ssc-vocab-master
4. **Stack:** Astro 5 + Svelte 5 + Tailwind 3 → Cloudflare Pages (static) + Pages Functions (worker) + Cloudflare D1 (SQLite)
5. **Two data domains:** static content in `public/data/*.json` (read-only, CDN-cached) vs user data in D1 (read-write, auth-required). Don't confuse them.
6. **First user to sign up becomes admin** (then signups can be disabled from `/admin`)
7. **Only `/`, `/login`, `/signup` are public** — everything else requires login
8. **`stem` vs `sent` semantics vary by qtype** — see PROJECT_GUIDE.md §6.2 (this is the #1 source of MCQ display bugs)
9. **To deploy:** `npm run build && npx wrangler pages deploy ./dist --project-name=sscpyqs` (uses `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL` env vars)
10. **Always run `npm run build` before declaring done** — wrangler bundler is stricter than tsc

## 🔑 Credentials & secrets

- **Cloudflare account:** akaprantikdas@gmail.com (account ID `448154c5d61fdb71ea8a752b5bcb3b3d`)
- **Cloudflare global key:** `cfk_30U3...` (used for Pages deploy + D1 management via X-Auth-Email/X-Auth-Key headers — NOT a Bearer token)
- **GitHub PAT:** `ghp_TBl9...` (push access to the repo — remove from git config after pushing)
- **Justwoker AI keys:** 2 keys for the data pipeline (see `scripts/.env.example`)
- **JWT_SECRET:** stored as a Cloudflare Pages env var (set via dashboard/API, never in code)

⚠️ **Never commit secrets.** The `.gitignore` blocks `.env`, `jwt_secret.txt`, and `.wrangler/`. The `scripts/ai_helper.py` reads keys from env vars only. After pushing with a GitHub PAT, immediately `git remote set-url origin` to remove it.
