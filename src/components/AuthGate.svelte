<script lang="ts">
  // src/components/AuthGate.svelte
  // Client-side route guard. Renders a loading state, then either the slot
  // (if logged in) or redirects to /login (if not). Public pages bypass.
  import { onMount } from 'svelte';
  import { loadSession, isPublicPath, getUser } from '../lib/auth';

  let { pathname = '/', publicPage = false }: { pathname?: string; publicPage?: boolean } = $props();
  let state = $state<'loading' | 'ok' | 'redirecting'>('loading');

  onMount(async () => {
    await loadSession();
    if (publicPage || isPublicPath(pathname)) {
      state = 'ok';
      return;
    }
    if (getUser()) {
      state = 'ok';
    } else {
      state = 'redirecting';
      const next = encodeURIComponent(pathname || '/');
      window.location.href = `/login?next=${next}`;
    }
  });
</script>

{#if state === 'loading'}
  <div class="flex items-center justify-center py-20">
    <div class="flex flex-col items-center gap-3 text-zinc-500">
      <div class="h-8 w-8 rounded-full border-2 border-orange-400 border-t-transparent animate-spin"></div>
      <p class="text-xs">Loading…</p>
    </div>
  </div>
{:else if state === 'redirecting'}
  <div class="flex items-center justify-center py-20">
    <p class="text-sm text-zinc-500">Redirecting to login…</p>
  </div>
{:else}
  <slot />
{/if}
