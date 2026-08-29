<script lang="ts">
  // src/components/AuthBar.svelte
  // Compact user menu: circular avatar (initial) only in the header to save space.
  // Click → dropdown with email, Problems, Admin (if admin), Logout.
  import { onMount } from 'svelte';
  import { loadSession, getUser, logout, onAuthChange, type SessionUser } from '../lib/auth';

  let user = $state<SessionUser | null>(null);
  let open = $state(false);

  onMount(async () => {
    await loadSession();
    user = getUser();
    onAuthChange((u) => (user = u));
    // close dropdown on outside click / escape
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (!open) return;
      if (e instanceof KeyboardEvent && e.key !== 'Escape') return;
      open = false;
    };
    document.addEventListener('click', close);
    document.addEventListener('keydown', close);
    return () => {
      document.removeEventListener('click', close);
      document.removeEventListener('keydown', close);
    };
  });

  function toggle(e: MouseEvent) {
    e.stopPropagation();
    open = !open;
  }

  async function handleLogout() {
    await logout();
    user = null;
    window.location.href = '/';
  }
</script>

<div class="relative shrink-0">
  {#if user}
    <button
      onclick={toggle}
      class="h-8 w-8 rounded-full bg-gradient-to-br from-orange-500 to-rose-500 text-white flex items-center justify-center text-xs font-bold uppercase shadow-sm hover:shadow-md transition-shadow ring-2 ring-white dark:ring-zinc-900"
      title={user.email}
      aria-label="Account menu"
    >
      {user.email.charAt(0)}
    </button>
    {#if open}
      <div class="absolute right-0 mt-1 w-60 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-xl py-1 z-50" onclick={(e) => e.stopPropagation()}>
        <div class="px-3 py-2 border-b border-zinc-100 dark:border-zinc-800">
          <div class="text-[10px] uppercase font-semibold text-zinc-400 tracking-wide">Signed in</div>
          <div class="text-sm font-medium truncate flex items-center gap-1.5">
            {user.email}
            {#if user.role === 'admin'}<span class="text-[9px] font-bold text-amber-600 border border-amber-300 rounded px-1 py-0.5">ADMIN</span>{/if}
          </div>
        </div>
        <a href="/problems" class="block px-3 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
          Problematic list
        </a>
        {#if user.role === 'admin'}
          <a href="/admin" class="block px-3 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Admin dashboard
          </a>
        {/if}
        <button onclick={handleLogout} class="w-full text-left px-3 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-2 text-rose-600 dark:text-rose-400">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></svg>
          Log out
        </button>
      </div>
    {/if}
  {:else}
    <a href="/login" title="Log in" class="h-8 w-8 rounded-full border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center justify-center text-zinc-500 hover:text-orange-600 transition-colors">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/></svg>
    </a>
  {/if}
</div>
