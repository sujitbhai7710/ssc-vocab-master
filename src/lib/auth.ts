// src/lib/auth.ts — client-side auth + user-data API (problematic, progress)
// Calls the Cloudflare Pages Functions worker (D1-backed).

export interface SessionUser {
  id: number;
  email: string;
  role: 'admin' | 'user';
}

let _user: SessionUser | null = null;
let _loaded = false;
const listeners = new Set<(u: SessionUser | null) => void>();

export function getUser(): SessionUser | null {
  return _user;
}
export function isLoggedIn(): boolean {
  return !!_user;
}
export function onAuthChange(cb: (u: SessionUser | null) => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}
function emit() {
  for (const cb of listeners) cb(_user);
}

// Load session once on app start (cookie is httpOnly, so we ask the server).
export async function loadSession(): Promise<SessionUser | null> {
  if (_loaded) return _user;
  _loaded = true;
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      _user = data.user || null;
    }
  } catch {
    /* network */
  }
  emit();
  return _user;
}

export async function signup(email: string, password: string): Promise<{ ok: boolean; error?: string }> {
  const res = await fetch('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return { ok: false, error: data.error || 'Signup failed' };
  _user = data.user;
  emit();
  return { ok: true };
}

export async function login(email: string, password: string): Promise<{ ok: boolean; error?: string }> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return { ok: false, error: data.error || 'Login failed' };
  _user = data.user;
  emit();
  return { ok: true };
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  _user = null;
  emit();
}

// Public route list — these are accessible WITHOUT login.
// Everything else requires an authenticated session.
export const PUBLIC_PATHS = ['/', '/login', '/signup'];

export function isPublicPath(pathname: string): boolean {
  if (pathname === '/') return true;
  if (pathname === '/login' || pathname === '/signup') return true;
  return false;
}

// ---- Problematic API ----
export interface ProblematicItem {
  item_type: string;
  item_key: string;
  sub_type: string | null;
  created_at: number;
}

export async function listProblematic(itemType?: string): Promise<ProblematicItem[]> {
  const q = itemType ? `?item_type=${encodeURIComponent(itemType)}` : '';
  const res = await fetch(`/api/problematic${q}`, { credentials: 'include' });
  if (!res.ok) return [];
  const data = await res.json();
  return data.items || [];
}
export async function addProblematic(itemType: string, itemKey: string, subType?: string): Promise<boolean> {
  const res = await fetch('/api/problematic', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ item_type: itemType, item_key: itemKey, sub_type: subType }),
  });
  return res.ok;
}
export async function removeProblematic(itemType: string, itemKey: string): Promise<boolean> {
  const res = await fetch(`/api/problematic?item_type=${encodeURIComponent(itemType)}&item_key=${encodeURIComponent(itemKey)}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  return res.ok;
}

// ---- Progress API ----
export interface ProgressEntry {
  read_till: number;
  completed: number[];
  updated_at: number;
}
export interface ProgressMap {
  [pageType: string]: ProgressEntry;
}
export async function loadProgress(): Promise<ProgressMap> {
  const res = await fetch('/api/progress', { credentials: 'include' });
  if (!res.ok) return {};
  const data = await res.json();
  return data.progress || {};
}
export async function saveProgress(pageType: string, readTill: number): Promise<boolean> {
  const res = await fetch('/api/progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ page_type: pageType, read_till: readTill }),
  });
  return res.ok;
}
export async function saveProgressRange(pageType: string, from: number, to: number): Promise<{ ok: boolean; completed?: number[] }> {
  const res = await fetch('/api/progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ page_type: pageType, range: [from, to] }),
  });
  if (!res.ok) return { ok: false };
  const data = await res.json();
  return { ok: true, completed: data.completed };
}
export async function resetProgressCompleted(pageType: string): Promise<boolean> {
  const res = await fetch('/api/progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ page_type: pageType, reset_completed: true }),
  });
  return res.ok;
}
