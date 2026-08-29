// functions/api/auth/signup.ts
import { Env, hashPassword, makeToken, setSessionCookie, json } from '../../_lib/auth';

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  let body: { email?: string; password?: string };
  try {
    body = await ctx.request.json();
  } catch {
    return json({ error: 'Invalid JSON' }, 400);
  }
  const email = (body.email || '').trim().toLowerCase();
  const password = body.password || '';
  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: 'Valid email required' }, 400);
  if (password.length < 6) return json({ error: 'Password must be at least 6 characters' }, 400);

  // Check signup enabled (unless DB empty -> first user becomes admin regardless)
  const userCount = await ctx.env.DB.prepare('SELECT COUNT(*) as c FROM users').first<{ c: number }>();
  const isEmpty = !userCount || userCount.c === 0;
  if (!isEmpty) {
    const setting = await ctx.env.DB.prepare("SELECT value FROM settings WHERE key = 'signup_enabled'").first<{ value: string }>();
    if (setting && setting.value === 'false') {
      return json({ error: 'New signups are currently disabled by the admin.' }, 403);
    }
  }

  // Existing email?
  const existing = await ctx.env.DB.prepare('SELECT id FROM users WHERE email = ?').bind(email).first();
  if (existing) return json({ error: 'An account with this email already exists.' }, 409);

  const { hash, salt } = await hashPassword(password);
  const role = isEmpty ? 'admin' : 'user'; // FIRST user becomes admin
  const now = Date.now();
  const res = await ctx.env.DB.prepare(
    'INSERT INTO users (email, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?) RETURNING id'
  ).bind(email, hash, salt, role, now).first<{ id: number }>();
  if (!res) return json({ error: 'Failed to create user' }, 500);

  const token = await makeToken({ id: res.id, email, role: role as 'admin' | 'user' }, ctx.env.JWT_SECRET);
  return json({ user: { id: res.id, email, role } }, 200, { 'Set-Cookie': setSessionCookie(token) });
};
