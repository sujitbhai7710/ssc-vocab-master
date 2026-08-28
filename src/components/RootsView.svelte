<script lang="ts">
  // src/components/RootsView.svelte
  import { loadRoots, type RootFamily } from '../lib/vocab-data';
  import ProblematicButton from './ProblematicButton.svelte';

  let roots = $state<RootFamily[]>([]);
  let loading = $state(true);

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        roots = await loadRoots();
      } catch (err) {
        console.error('Failed to load roots:', err);
      } finally {
        loading = false;
      }
    })();
  }

  let query = $state('');
  let sort = $state<'frequency' | 'alphabetical'>('frequency');
  let page = $state(1);
  const PAGE_SIZE = 30;

  // Filtered + sorted
  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    let result = roots.filter((r) => {
      if (!q) return true;
      if (r.root.toLowerCase().includes(q)) return true;
      if (r.rm.toLowerCase().includes(q)) return true;
      if (r.rbn.includes(q)) return true;
      // Search in word list
      for (const w of r.words) {
        if (w.w.toLowerCase().includes(q)) return true;
        if (w.mean.toLowerCase().includes(q)) return true;
      }
      return false;
    });

    const sorted = [...result];
    if (sort === 'frequency') {
      sorted.sort((a, b) => (b.words.length || 0) - (a.words.length || 0) || a.root.localeCompare(b.root));
    } else {
      sorted.sort((a, b) => a.root.localeCompare(b.root));
    }
    return sorted;
  });

  const totalPages = $derived(Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)));
  const currentPage = $derived(Math.min(page, totalPages));
  const pageItems = $derived(filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));

  function handleQuery(v: string) {
    query = v;
    page = 1;
  }

  function selectWord(word: string) {
    if (typeof window !== 'undefined') window.location.href = `/word/${encodeURIComponent(word.toLowerCase())}`;
  }
</script>

<div class="space-y-4">
  <!-- Search & filter bar -->
  <div class="sticky top-1 z-20 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
        <input
          type="search"
          value={query}
          on:input={(e) => handleQuery((e.target as HTMLInputElement).value)}
          placeholder="Search root words, meanings, or word families..."
          class="w-full pl-9 pr-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-400/40"
        />
      </div>
      <select
        bind:value={sort}
        class="h-9 px-3 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-400/40"
      >
        <option value="frequency">Sort: Family size</option>
        <option value="alphabetical">Sort: A→Z</option>
      </select>
    </div>
    <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span>
        <span class="font-semibold text-zinc-900 dark:text-zinc-100">{filtered.length.toLocaleString()}</span>
        root families
        {#if query}
          matching &ldquo;<span class="font-medium text-zinc-900 dark:text-zinc-100">{query}</span>&rdquo;
        {/if}
      </span>
      {#if totalPages > 1}
        <span class="ml-auto">page {currentPage} / {totalPages}</span>
      {/if}
    </div>
  </div>

  {#if loading}
    <div class="space-y-3">
      {#each Array(5) as _}
        <div class="h-48 rounded-xl bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>
      {/each}
    </div>
  {:else if pageItems.length === 0}
    <div class="text-center py-12 border-2 border-dashed rounded-lg">
      <p class="text-sm text-zinc-500">No root families match your search.</p>
    </div>
  {:else}
    <div class="space-y-4">
      {#each pageItems as fam (fam.root)}
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl overflow-hidden">
          <div class="px-5 pt-4 pb-2 bg-gradient-to-br from-rose-50 to-pink-50 dark:from-rose-950/30 dark:to-pink-950/30 border-b border-rose-200 dark:border-rose-800">
            <div class="flex items-baseline justify-between gap-3 flex-wrap">
              <div>
                <h3 class="text-2xl font-bold tracking-tight text-rose-900 dark:text-rose-200">{fam.root}</h3>
                <p class="text-sm text-zinc-700 dark:text-zinc-300 mt-0.5">
                  <span class="font-medium">{fam.rm}</span>
                  {#if fam.rbn}
                    <span class="mx-2 text-zinc-400">·</span>
                    <span class="font-bengali" lang="bn">{fam.rbn}</span>
                  {/if}
                </p>
              </div>
              <ProblematicButton itemType="root" itemKey={fam.root} subType={fam.rm} label="Mark root" />
              <div class="text-right">
                <div class="text-2xl font-bold tabular-nums text-rose-700 dark:text-rose-300">{fam.words.length}</div>
                <div class="text-[10px] text-zinc-500">words in family</div>
              </div>
            </div>
          </div>
          <ul class="divide-y divide-zinc-100 dark:divide-zinc-800">
            {#each fam.words as w}
              <li class="px-5 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                <button
                  on:click={() => selectWord(w.w)}
                  class="text-left w-full"
                >
                  <div class="flex items-baseline justify-between gap-3 flex-wrap">
                    <div class="min-w-0">
                      <div class="flex items-baseline gap-2 flex-wrap">
                        <span class="text-base font-semibold text-zinc-900 dark:text-zinc-100 hover:text-rose-700 dark:hover:text-rose-300 transition-colors">{w.w}</span>
                        {#if w.pos}
                          <span class="text-[10px] italic text-zinc-500">{w.pos}</span>
                        {/if}
                      </div>
                      <div class="text-sm text-zinc-700 dark:text-zinc-300 mt-0.5">{w.mean}</div>
                      {#if w.bn}
                        <div class="text-xs text-zinc-600 dark:text-zinc-400 font-bengali mt-0.5" lang="bn">{w.bn}</div>
                      {/if}
                      {#if w.mn}
                        <div class="text-[11px] text-amber-700 dark:text-amber-400 italic mt-1">
                          💡 {w.mn}
                        </div>
                      {/if}
                    </div>
                    {#if w.n}
                      <div class="shrink-0 text-right">
                        <div class="text-sm font-bold tabular-nums text-rose-700 dark:text-rose-300">{w.n}</div>
                        <div class="text-[10px] text-zinc-500">appearances</div>
                      </div>
                    {/if}
                  </div>
                </button>
              </li>
            {/each}
          </ul>
        </div>
      {/each}
    </div>
  {/if}

  {#if totalPages > 1}
    <div class="flex items-center justify-center gap-2 pt-2">
      <button disabled={currentPage === 1} on:click={() => (page = currentPage - 1)} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Previous</button>
      <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
      <button disabled={currentPage === totalPages} on:click={() => (page = currentPage + 1)} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Next</button>
    </div>
  {/if}
</div>
