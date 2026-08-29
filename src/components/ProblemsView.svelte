<script lang="ts">
  // src/components/ProblemsView.svelte
  // Shows all problematic items for the current user, grouped by category.
  // Each category links to the source page /word/[word] or the rule section.
  import { onMount, onDestroy } from 'svelte';
  import { isLoggedIn, loadSession, onAuthChange, listProblematic, removeProblematic, type ProblematicItem } from '../lib/auth';

  let items = $state<ProblematicItem[]>([]);
  let loading = $state(true);
  let activeTab = $state('vocab');

  const tabs = [
    { key: 'vocab', label: 'Vocab (Syn/Ant)', itemType: 'vocab' },
    { key: 'root', label: 'Root Words', itemType: 'root' },
    { key: 'grammar-rule', label: 'Grammar Rules', itemType: 'grammar-rule' },
    { key: 'grammar-mcq', label: 'Grammar MCQs', itemType: 'grammar-mcq' },
    { key: 'narration', label: 'Narration', itemType: 'narration' },
    { key: 'voice', label: 'Voice', itemType: 'voice' },
  ];

  let loggedIn = $state(false);
  let unsub: (() => void) | null = null;

  async function refresh() {
    if (!isLoggedIn()) { loading = false; return; }
    loading = true;
    try {
      items = await listProblematic();
    } catch {} finally {
      loading = false;
    }
  }

  onMount(async () => {
    await loadSession();
    loggedIn = isLoggedIn();
    // React to late session resolution (e.g. AuthBar loads session after us)
    unsub = onAuthChange((u) => {
      const now = !!u;
      if (now !== loggedIn) {
        loggedIn = now;
        if (now) refresh();
      }
    });
    await refresh();
  });

  onDestroy(() => { unsub?.(); });

  const byType = $derived.by(() => {
    const map: Record<string, ProblematicItem[]> = {};
    for (const it of items) {
      (map[it.item_type] = map[it.item_type] || []).push(it);
    }
    return map;
  });

  function linkFor(it: ProblematicItem): string {
    if (it.item_type === 'vocab') return `/word/${it.item_key.toLowerCase()}`;
    if (it.item_type === 'root') return `/roots`;
    if (it.item_type === 'grammar-rule') return `/grammar-rules`;
    if (it.item_type === 'grammar-mcq') return `/grammar-rules`;
    if (it.item_type === 'narration') return `/narration`;
    if (it.item_type === 'voice') return `/voice`;
    return '/';
  }
  async function remove(it: ProblematicItem) {
    await removeProblematic(it.item_type, it.item_key);
    items = items.filter((x) => !(x.item_type === it.item_type && x.item_key === it.item_key));
  }
</script>

<div class="space-y-4">
  <div>
    <div class="text-[11px] uppercase font-semibold tracking-wide text-rose-600">Your list</div>
    <h2 class="text-2xl font-bold tracking-tight mt-1">Problematic Items</h2>
    <p class="text-sm text-zinc-500 mt-1">Words/rules you've marked for revision. In future mock tests, questions you get wrong will auto-add here.</p>
  </div>

  {#if loading}
    <div class="space-y-2">{#each Array(5) as _}<div class="h-14 rounded-lg bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}</div>
  {:else if !loggedIn}
    <div class="text-center py-12 border-2 border-dashed rounded-lg">
      <p class="text-sm text-zinc-500">Please log in to see your problematic items.</p>
      <a href="/login" class="inline-block mt-3 text-sm text-orange-600 hover:underline">Log in</a>
    </div>
  {:else}
    <!-- tabs -->
    <div class="flex items-center gap-1.5 flex-wrap border-b border-zinc-200 dark:border-zinc-700">
      {#each tabs as t}
        {@const count = (byType[t.itemType] || []).length}
        <button
          onclick={() => (activeTab = t.key)}
          class={`text-xs h-9 px-3 rounded-t-md border-b-2 transition-colors ${activeTab === t.key ? 'border-rose-500 text-rose-600 font-semibold' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}
        >
          {t.label} <span class="text-[10px] tabular-nums">({count})</span>
        </button>
      {/each}
    </div>

    {#each tabs as t}
      {@const list = byType[t.itemType] || []}
      {#if activeTab === t.key}
        {#if list.length === 0}
          <div class="text-center py-12 border-2 border-dashed rounded-lg">
            <p class="text-sm text-zinc-500">No problematic {t.label.toLowerCase()} yet.</p>
            <p class="text-xs text-zinc-400 mt-1">Click the heart button on any {t.label.toLowerCase().includes('grammar') ? 'rule' : 'word/rule'} to add it here.</p>
          </div>
        {:else}
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {#each list as it (it.item_key)}
              <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 flex items-center gap-2 group">
                <a href={linkFor(it)} class="flex-1 min-w-0">
                  <div class="text-sm font-medium truncate capitalize">{it.item_key}</div>
                  <div class="text-[10px] text-zinc-500">{it.sub_type || it.item_type}</div>
                </a>
                <button onclick={() => remove(it)} class="shrink-0 h-7 w-7 rounded-md text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 flex items-center justify-center" title="Remove">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                </button>
              </div>
            {/each}
          </div>
        {/if}
      {/if}
    {/each}
  {/if}
</div>
