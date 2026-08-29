# Auth & Security

## Authentication model

The app uses **cookie-based session auth** with a self-contained JWT. No external auth provider.

```
User signs up ──► password hashed (PBKDF2-SHA256, 100k iters) ──► stored in D1
                                                                       │
                  JWT (HS256) signed with JWT_SECRET ◄─── on login ────┘
                            │
                  set as httpOnly cookie (svm_session, 1-year expiry)
                            │
                  sent automatically on every request (credentials: include)
                            │
                  worker verifies JWT ──► ctx.env.DB query as that user
```

## Password security

- **Algorithm:** PBKDF2-SHA256, 100,000 iterations
- **Salt:** 16 random hex bytes per user (stored alongside hash)
- **Storage:** hash is base64-encoded HMAC key material
- **Verification:** constant-time comparison (timing-safe)
- Implemented in `functions/_lib/auth.ts` using the Web Crypto API (no external deps, works in Workers runtime)

```ts
// functions/_lib/auth.ts
const PBKDF2_ITER = 100000;
export async function hashPassword(password: string): Promise<{ hash: string; salt: string }> {
  const salt = randomHex(16);
  const key = await deriveKey(password, salt);
  const hashBuf = await crypto.subtle.exportKey('raw', key);
  return { hash: b64encode(hashBuf), salt };
}
```

## Session cookies

- **Name:** `svm_session`
- **Flags:** `HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=31536000` (1 year)
- **HttpOnly** = JavaScript can't read it (XSS protection)
- **Secure** = HTTPS only
- **SameSite=Lax** = sent on same-site navigations, blocks CSRF
- The cookie contains the JWT; the worker verifies it on every `/api/*` request

**"Stay logged in forever"** — the 1-year Max-Age means the session persists across browser restarts and reboots until the user explicitly logs out (which clears the cookie).

## JWT structure

```json
{
  "sub": 3,                      // user ID
  "email": "user@example.com",
  "role": "admin",               // or "user"
  "iat": 1787947906              // issued at (unix seconds)
}
```
Signed with HS256 using `JWT_SECRET` (a 64-char random string stored as a Cloudflare Pages env var).

## Route gating (two layers)

### Layer 1: Client-side inline script (in `Layout.astro`)
Runs before paint on every non-public page. Probes `/api/auth/me`; if no user, redirects to `/login?next=<path>`.
```js
// only redirects on a definitive no-user response, not on network errors
const r = await fetch('/api/auth/me', { credentials: 'include', cache: 'no-store' });
if (!r.ok) return; // don't redirect on network error
const d = await r.json();
if (!d.user) window.location.replace('/login?next=' + encodeURIComponent(pathname));
```

### Layer 2: Server-side auth (in each worker endpoint)
Every `/api/*` endpoint (except `auth/me`, `auth/signup`, `auth/login`, `auth/signup-status`) calls `getUser()` → `requireUser()` or `requireAdmin()`:
```ts
const user = await getUser(ctx.request, ctx.env);
const guard = requireUser(user);  // returns Response(401) if null
if (guard instanceof Response) return guard;
// user is now typed as SessionUser
```

**Public pages:** `/`, `/login`, `/signup` (marked `publicPage={true}` in their Layout).
**Everything else** requires a valid session.

## Admin controls

### First user = admin
```ts
// functions/api/auth/signup.ts
const isEmpty = userCount.c === 0;
const role = isEmpty ? 'admin' : 'user';
```

### Enable/disable signups
Admin toggles in `/admin` → `PATCH /api/admin/settings { signupEnabled: bool }` → updates `settings.signup_enabled`. New signups are blocked when it's `false` (unless DB is empty).

### Delete users
Admin can delete any user (except self, and can't delete the last admin). Deleting a user also cascades to their `problematic` + `progress` rows.

## ProblematicButton auth race (fixed)

There was a bug where `ProblematicButton` / `ProgressTracker` / `ProblemsView` checked `isLoggedIn()` synchronously in `onMount`, but the session (loaded by `AuthBar` with `client:idle`) hadn't resolved yet → showed "please log in" for logged-in users.

**Fix:** each component now `await loadSession()` in its own `onMount` (cached, no duplicate requests) and subscribes to `onAuthChange` to re-check when the session resolves late.

```ts
// src/components/ProblemsView.svelte
onMount(async () => {
  await loadSession();
  loggedIn = isLoggedIn();
  unsub = onAuthChange((u) => {
    const now = !!u;
    if (now !== loggedIn) { loggedIn = now; if (now) refresh(); }
  });
  await refresh();
});
```

## Security checklist

- ✅ Passwords hashed (PBKDF2, never stored in plaintext)
- ✅ JWT signed with secret (not in code, env var only)
- ✅ Cookies HttpOnly + Secure + SameSite
- ✅ Server-side auth on every user-data endpoint
- ✅ SQL parameterized queries (D1 `.bind()`, no injection)
- ✅ No secrets in git (`.gitignore` blocks `.env`, `jwt_secret.txt`)
- ✅ Login error messages don't leak whether email exists ("Invalid email or password" for both)
- ✅ Admin actions require `role === 'admin'` server-side
- ✅ Can't delete self / last admin (prevents lockout)

## Known limitations

- No password reset / email verification (no email service configured)
- No rate limiting on login (would need Cloudflare WAF or a rate-limit binding)
- JWT_SECRET rotation invalidates all sessions (acceptable — rare)
- The `cfk_` global key has full account access — if it leaks, rotate it in the Cloudflare dashboard immediately
