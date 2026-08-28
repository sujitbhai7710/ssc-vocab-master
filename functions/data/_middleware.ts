// functions/data/_middleware.ts
// Long-cache all static JSON data files. They are content-stable per deployment,
// so browsers + Cloudflare's edge can cache them for a year (revalidated by URL).
export const onRequest: PagesFunction = async (ctx) => {
  const res = await ctx.next();
  // Only cache successful JSON responses
  if (res.ok) {
    const headers = new Headers(res.headers);
    headers.set('Cache-Control', 'public, max-age=86400, stale-while-revalidate=604800');
    headers.set('CDN-Cache-Control', 'public, max-age=2592000');
    headers.set('Cloudflare-CDN-Cache-Control', 'public, max-age=2592000');
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
  }
  return res;
};
