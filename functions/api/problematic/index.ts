// functions/api/problematic/index.ts
// GET  ?item_type=vocab           -> list user's problematic of that type (or all)
// POST { item_type, item_key, sub_type } -> add
// DELETE ?item_type=&item_key=     -> remove
import { Env, getUser, requireUser, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;
  const url = new URL(ctx.request.url);
  const itemType = url.searchParams.get('item_type') || '';
  let stmt;
  if (itemType) {
    stmt = ctx.env.DB.prepare('SELECT item_type, item_key, sub_type, created_at FROM problematic WHERE user_id = ? AND item_type = ? ORDER BY created_at DESC').bind(uid, itemType);
  } else {
    stmt = ctx.env.DB.prepare('SELECT item_type, item_key, sub_type, created_at FROM problematic WHERE user_id = ? ORDER BY created_at DESC').bind(uid);
  }
  const rows = await stmt.all<{ item_type: string; item_key: string; sub_type: string | null; created_at: number }>();
  return json({ items: rows.results || [] }, 200);
};

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;
  let body: { item_type?: string; item_key?: string; sub_type?: string };
  try { body = await ctx.request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }
  const itemType = (body.item_type || '').trim();
  const itemKey = (body.item_key || '').trim();
  if (!itemType || !itemKey) return json({ error: 'item_type and item_key required' }, 400);
  const subType = (body.sub_type || '').trim() || null;
  const now = Date.now();
  await ctx.env.DB.prepare(
    'INSERT INTO problematic (user_id, item_type, item_key, sub_type, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, item_type, item_key) DO NOTHING'
  ).bind(uid, itemType, itemKey, subType, now).run();
  return json({ ok: true }, 200);
};

export const onRequestDelete: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;
  const url = new URL(ctx.request.url);
  const itemType = url.searchParams.get('item_type') || '';
  const itemKey = url.searchParams.get('item_key') || '';
  if (!itemType || !itemKey) return json({ error: 'item_type and item_key required' }, 400);
  await ctx.env.DB.prepare('DELETE FROM problematic WHERE user_id = ? AND item_type = ? AND item_key = ?').bind(uid, itemType, itemKey).run();
  return json({ ok: true }, 200);
};
