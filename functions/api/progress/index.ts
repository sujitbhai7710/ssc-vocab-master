// functions/api/progress/index.ts
// GET  -> { progress: { page_type: { read_till, completed:[...], updated_at } } }
// POST { page_type, read_till }              -> set read_till (back-compat)
// POST { page_type, range: [from, to] }      -> add indices from..to to completed set
// POST { page_type, reset_completed: true }  -> clear completed
import { Env, getUser, requireUser, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;
  const rows = await ctx.env.DB.prepare('SELECT page_type, read_till, completed, updated_at FROM progress WHERE user_id = ?').bind(uid).all<{
    page_type: string; read_till: number; completed: string | null; updated_at: number;
  }>();
  const map: Record<string, { read_till: number; completed: number[]; updated_at: number }> = {};
  for (const r of rows.results || []) {
    let completed: number[] = [];
    try { completed = r.completed ? JSON.parse(r.completed) : []; } catch { completed = []; }
    map[r.page_type] = { read_till: r.read_till, completed, updated_at: r.updated_at };
  }
  return json({ progress: map }, 200);
};

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;
  let body: { page_type?: string; read_till?: number; range?: [number, number]; reset_completed?: boolean };
  try { body = await ctx.request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }
  const pageType = (body.page_type || '').trim();
  if (!pageType) return json({ error: 'page_type required' }, 400);
  const now = Date.now();

  // Fetch existing row
  const existing = await ctx.env.DB.prepare('SELECT read_till, completed FROM progress WHERE user_id = ? AND page_type = ?').bind(uid, pageType).first<{ read_till: number; completed: string | null }>();
  let readTill = existing?.read_till ?? 0;
  let completed: number[] = [];
  try { completed = existing?.completed ? JSON.parse(existing.completed) : []; } catch { completed = []; }

  if (body.reset_completed) {
    completed = [];
  } else if (body.range && Array.isArray(body.range) && body.range.length === 2) {
    const [from, to] = body.range.map(Number);
    if (Number.isFinite(from) && Number.isFinite(to) && from >= 1 && to >= from) {
      const set = new Set(completed);
      for (let i = from; i <= to; i++) set.add(i);
      completed = Array.from(set).sort((a, b) => a - b);
      // also bump read_till if this range extends it
      if (to > readTill) readTill = to;
    }
  } else if (typeof body.read_till === 'number' && Number.isFinite(body.read_till)) {
    readTill = Math.max(0, Math.min(body.read_till, 100000));
    // when setting read_till, also mark 1..read_till as completed (unified progress)
    const set = new Set(completed);
    for (let i = 1; i <= readTill; i++) set.add(i);
    completed = Array.from(set).sort((a, b) => a - b);
  } else {
    return json({ error: 'Provide read_till or range [from,to]' }, 400);
  }

  const completedJson = JSON.stringify(completed);
  await ctx.env.DB.prepare(
    'INSERT INTO progress (user_id, page_type, read_till, completed, updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, page_type) DO UPDATE SET read_till = excluded.read_till, completed = excluded.completed, updated_at = excluded.updated_at'
  ).bind(uid, pageType, readTill, completedJson, now).run();
  return json({ ok: true, page_type: pageType, read_till: readTill, completed }, 200);
};
