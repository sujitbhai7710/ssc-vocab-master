// functions/api/auth/login.ts
import { Env, verifyPassword, makeToken, setSessionCookie, json } from '../../_lib/auth';

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  let body: { email?: string; password?: string };
  try {
    body = await ctx.request.json();
  } catch {
    return json({ error: 'Invalid JSON' }, 400);
  }
  const email = (body.email || '').trim().toLowerCase();
  const password = body.password || '';
  if (!email || !password) return json({ error: 'Email and password required' }, 400);

  const row = await ctx.env.DB.prepare('SELECT id, email, password_hash, salt, role FROM users WHERE email = ?').bind(email).first<{
    id: number; email: string; password_hash: string; salt: string; role: 'admin' | 'user';
  }>();
  if (!row) return json({ error: 'Invalid email or password' }, 401);

  const ok = await verifyPassword(password, row.salt, row.password_hash);
  if (!ok) return json({ error: 'Invalid email or password' }, 401);

  const token = await makeToken({ id: row.id, email: row.email, role: row.role }, ctx.env.JWT_SECRET);
  return json({ user: { id: row.id, email: row.email, role: row.role } }, 200, { 'Set-Cookie': setSessionCookie(token) });
};
