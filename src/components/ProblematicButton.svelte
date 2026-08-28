<script lang="ts">
  // src/components/ProblematicButton.svelte
  // Toggle an item as problematic for the current user. Needs login.
  import { onMount } from 'svelte';
  import { isLoggedIn, listProblematic, addProblematic, removeProblematic } from '../lib/auth';

  let {
    itemType,
    itemKey,
    subType = '',
    label = 'Mark problematic',
  }: { itemType: string; itemKey: string; subType?: string; label?: string } = $props();

  let marked = $state(false);
  let busy = $state(false);
  let loaded = $state(false);

  onMount(async () => {
    if (!isLoggedIn()) { loaded = true; return; }
    try {
      const items = await listProblematic(itemType);
      marked = items.some((i) => i.item_key === itemKey);
    } catch {} finally {
      loaded = true;
    }
  });

  async function toggle() {
    if (busy) return;
    if (!isLoggedIn()) {
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    busy = true;
    try {
      if (marked) {
        await removeProblematic(itemType, itemKey);
        marked = false;
      } else {
        await addProblematic(itemType, itemKey, subType);
        marked = true;
      }
    } finally {
      busy = false;
    }
  }
</script>

{#if loaded}
  <button
    onclick={toggle}
    disabled={busy}
    title={marked ? 'Remove from problematic' : label}
    class={`flex items-center gap-1.5 h-8 px-2.5 rounded-md text-xs font-medium border transition-colors ${marked ? 'bg-rose-500 text-white border-rose-500' : 'border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:text-rose-600 dark:hover:text-rose-400'}`}
  >
    {#if busy}
      <span class="h-3 w-3 rounded-full border-2 border-current border-t-transparent animate-spin"></span>
    {:else}
      <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill={marked ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
    {/if}
    {marked ? 'Problematic' : label}
  </button>
{/if}
