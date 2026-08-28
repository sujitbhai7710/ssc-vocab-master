// functions/api/admin/settings.ts — GET (admin) + PATCH (admin) signup_enabled
import { Env, getUser, requireAdmin, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireAdmin(user);
  if (guard instanceof Response) return guard;
  const setting = await ctx.env.DB.prepare("SELECT value FROM settings WHERE key = 'signup_enabled'").first<{ value: string }>();
  const uc = await ctx.env.DB.prepare('SELECT COUNT(*) as c FROM users').first<{ c: number }>();
  return json({ signupEnabled: setting ? setting.value !== 'false' : true, userCount: uc?.c ?? 0 }, 200);
};

export const onRequestPatch: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireAdmin(user);
  if (guard instanceof Response) return guard;
  let body: { signupEnabled?: boolean };
  try { body = await ctx.request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }
  const val = body.signupEnabled ? 'true' : 'false';
  await ctx.env.DB.prepare("INSERT INTO settings (key, value) VALUES ('signup_enabled', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value").bind(val).run();
  return json({ signupEnabled: body.signupEnabled }, 200);
};
