// functions/api/test/configs/index.ts
// GET    /api/test/configs         -> list user's saved configs
// POST   /api/test/configs         -> save a new config { name, config }
// PATCH  /api/test/configs?id=X    -> update name/config
// DELETE /api/test/configs?id=X    -> delete a saved config
import { Env, getUser, requireUser, json } from '../../../_lib/auth';
import { validateConfig } from '../../../_lib/test-engine';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  const rows = await ctx.env.DB.prepare(
    'SELECT id, name, config, created_at, updated_at FROM test_configs WHERE user_id = ? ORDER BY updated_at DESC'
  ).bind(uid).all<{ id: number; name: string; config: string; created_at: number; updated_at: number }>();

  const configs = (rows.results || []).map(r => {
    let cfg: any = {};
    try { cfg = JSON.parse(r.config); } catch {}
    return { id: r.id, name: r.name, config: cfg, created_at: r.created_at, updated_at: r.updated_at };
  });
  return json({ configs }, 200);
};

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  let body: { name?: string; config?: any };
  try { body = await ctx.request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }
  const name = (body.name || '').trim();
  if (!name) return json({ error: 'name required' }, 400);
  if (name.length > 100) return json({ error: 'name too long (max 100)' }, 400);

  const validation = validateConfig(body.config);
  if (!validation.ok) return json({ error: validation.error }, 400);
  const config = validation.config!;
  config.name = name;
  config.source = 'custom';

  const now = Date.now();
  const ins = await ctx.env.DB.prepare(
    'INSERT INTO test_configs (user_id, name, config, created_at, updated_at) VALUES (?, ?, ?, ?, ?) RETURNING id'
  ).bind(uid, name, JSON.stringify(config), now, now).first<{ id: number }>();

  if (!ins) return json({ error: 'Failed to save config' }, 500);
  return json({ ok: true, id: ins.id, name, config }, 200);
};

export const onRequestPatch: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  const url = new URL(ctx.request.url);
  const id = parseInt(url.searchParams.get('id') || '', 10);
  if (!Number.isFinite(id)) return json({ error: 'id required' }, 400);

  const existing = await ctx.env.DB.prepare('SELECT user_id FROM test_configs WHERE id = ?').bind(id).first<{ user_id: number }>();
  if (!existing) return json({ error: 'Config not found' }, 404);
  if (existing.user_id !== uid) return json({ error: 'Not your config' }, 403);

  let body: { name?: string; config?: any };
  try { body = await ctx.request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }

  const updates: string[] = [];
  const binds: any[] = [];
  if (body.name !== undefined) {
    const name = (body.name || '').trim();
    if (!name) return json({ error: 'name cannot be empty' }, 400);
    if (name.length > 100) return json({ error: 'name too long (max 100)' }, 400);
    updates.push('name = ?');
    binds.push(name);
  }
  if (body.config !== undefined) {
    const validation = validateConfig(body.config);
    if (!validation.ok) return json({ error: validation.error }, 400);
    const config = validation.config!;
    if (body.name) config.name = body.name.trim();
    config.source = 'custom';
    updates.push('config = ?');
    binds.push(JSON.stringify(config));
  }
  if (updates.length === 0) return json({ error: 'Nothing to update' }, 400);
  updates.push('updated_at = ?');
  binds.push(Date.now());
  binds.push(id);

  await ctx.env.DB.prepare(`UPDATE test_configs SET ${updates.join(', ')} WHERE id = ?`).bind(...binds).run();
  return json({ ok: true }, 200);
};

export const onRequestDelete: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  const url = new URL(ctx.request.url);
  const id = parseInt(url.searchParams.get('id') || '', 10);
  if (!Number.isFinite(id)) return json({ error: 'id required' }, 400);

  const existing = await ctx.env.DB.prepare('SELECT user_id FROM test_configs WHERE id = ?').bind(id).first<{ user_id: number }>();
  if (!existing) return json({ error: 'Config not found' }, 404);
  if (existing.user_id !== uid) return json({ error: 'Not your config' }, 403);

  await ctx.env.DB.prepare('DELETE FROM test_configs WHERE id = ?').bind(id).run();
  return json({ ok: true }, 200);
};
