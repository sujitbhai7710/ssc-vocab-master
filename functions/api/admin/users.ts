// functions/api/admin/users.ts — GET list (admin) ; DELETE by id (admin, can't delete self / last admin)
import { Env, getUser, requireAdmin, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireAdmin(user);
  if (guard instanceof Response) return guard;
  const rows = await ctx.env.DB.prepare('SELECT id, email, role, created_at FROM users ORDER BY created_at ASC').all<{
    id: number; email: string; role: string; created_at: number;
  }>();
  return json({ users: rows.results || [] }, 200);
};

export const onRequestDelete: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireAdmin(user);
  if (guard instanceof Response) return guard;
  const url = new URL(ctx.request.url);
  const id = Number(url.searchParams.get('id'));
  if (!id) return json({ error: 'id required' }, 400);
  if (id === (guard as { id: number }).id) return json({ error: 'You cannot delete your own account.' }, 400);
  // Prevent deleting the last admin
  const target = await ctx.env.DB.prepare('SELECT role FROM users WHERE id = ?').bind(id).first<{ role: string }>();
  if (target && target.role === 'admin') {
    const adminCount = await ctx.env.DB.prepare("SELECT COUNT(*) as c FROM users WHERE role = 'admin'").first<{ c: number }>();
    if (adminCount && adminCount.c <= 1) return json({ error: 'Cannot delete the last admin account.' }, 400);
  }
  await ctx.env.DB.prepare('DELETE FROM users WHERE id = ?').bind(id).run();
  await ctx.env.DB.prepare('DELETE FROM problematic WHERE user_id = ?').bind(id).run();
  await ctx.env.DB.prepare('DELETE FROM progress WHERE user_id = ?').bind(id).run();
  return json({ ok: true }, 200);
};
