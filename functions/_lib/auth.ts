// functions/_lib/auth.ts — shared crypto + session helpers for Pages Functions
// Uses Web Crypto API (available in Workers). No external deps.

export interface Env {
  DB: D1Database;
  JWT_SECRET: string;
}

export interface SessionUser {
  id: number;
  email: string;
  role: 'admin' | 'user';
}

const COOKIE_NAME = 'svm_session';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365; // 1 year (stay logged in forever)
const PBKDF2_ITER = 100000;

const enc = new TextEncoder();
const dec = new TextDecoder();

function b64encode(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s);
}
function b64decode(str: string): Uint8Array {
  const s = atob(str);
  const bytes = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) bytes[i] = s.charCodeAt(i);
  return bytes;
}
function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
}
function randomHex(nBytes: number): string {
  const b = new Uint8Array(nBytes);
  crypto.getRandomValues(b);
  return bytesToHex(b);
}

// ---- Password hashing (PBKDF2-SHA256) ----
export async function hashPassword(password: string): Promise<{ hash: string; salt: string }> {
  const salt = randomHex(16);
  const key = await deriveKey(password, salt);
  const hashBuf = await crypto.subtle.exportKey('raw', key);
  return { hash: b64encode(hashBuf), salt };
}
export async function verifyPassword(password: string, salt: string, expectedHash: string): Promise<boolean> {
  try {
    const key = await deriveKey(password, salt);
    const hashBuf = await crypto.subtle.exportKey('raw', key);
    const actual = b64encode(hashBuf);
    return timingSafeEqual(actual, expectedHash);
  } catch {
    return false;
  }
}
async function deriveKey(password: string, salt: string): Promise<CryptoKey> {
  const keyMaterial = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits', 'deriveKey']);
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: enc.encode(salt), iterations: PBKDF2_ITER, hash: 'SHA-256' },
    keyMaterial,
    { name: 'HMAC', hash: 'SHA-256', length: 256 },
    true,
    ['sign']
  );
}
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// ---- JWT (HS256) ----
async function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);
}
export async function makeToken(user: SessionUser, secret: string): Promise<string> {
  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = { sub: user.id, email: user.email, role: user.role, iat: Math.floor(Date.now() / 1000) };
  const h = b64url(enc.encode(JSON.stringify(header)));
  const p = b64url(enc.encode(JSON.stringify(payload)));
  const data = `${h}.${p}`;
  const key = await hmacKey(secret);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(data));
  const s = b64url(sig);
  return `${data}.${s}`;
}
function b64url(buf: ArrayBuffer | Uint8Array): string {
  return b64encode(buf).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}
function b64urlDecode(str: string): Uint8Array {
  return b64decode(str.replace(/-/g, '+').replace(/_/g, '/'));
}
export async function verifyToken(token: string, secret: string): Promise<SessionUser | null> {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const data = `${parts[0]}.${parts[1]}`;
  const key = await hmacKey(secret);
  let valid = false;
  try {
    valid = await crypto.subtle.verify('HMAC', key, b64urlDecode(parts[2]), enc.encode(data));
  } catch {
    return null;
  }
  if (!valid) return null;
  try {
    const payload = JSON.parse(dec.decode(b64urlDecode(parts[1])));
    return { id: payload.sub, email: payload.email, role: payload.role };
  } catch {
    return null;
  }
}

// ---- Cookie helpers ----
export function setSessionCookie(token: string): string {
  const flags = `HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${COOKIE_MAX_AGE}`;
  return `${COOKIE_NAME}=${token}; ${flags}`;
}
export function clearSessionCookie(): string {
  return `${COOKIE_NAME}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`;
}
export function readSessionCookie(req: Request): string | null {
  const c = req.headers.get('Cookie') || '';
  const m = c.match(/(?:^|;\s*)svm_session=([^;]+)/);
  return m ? m[1] : null;
}

// ---- Request auth ----
export async function getUser(req: Request, env: Env): Promise<SessionUser | null> {
  const tok = readSessionCookie(req);
  if (!tok) return null;
  return verifyToken(tok, env.JWT_SECRET);
}
export function json(data: unknown, status = 200, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  });
}
export function requireUser(user: SessionUser | null): SessionUser | Response {
  if (!user) return json({ error: 'Not authenticated' }, 401);
  return user;
}
export function requireAdmin(user: SessionUser | null): SessionUser | Response {
  if (!user) return json({ error: 'Not authenticated' }, 401);
  if (user.role !== 'admin') return json({ error: 'Admin only' }, 403);
  return user;
}
