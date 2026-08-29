<script lang="ts">
  // src/components/RootsView.svelte
  // Root word families — rebuilt from comprehensive roots.json (1,451 families,
  // 4,245 words from ALL enriched sources: syn/ant stems+options, OWS, idioms, etc.)
  //
  // Each root family card shows:
  //  - Root name (e.g. "LEG") + meaning + Bengali meaning
  //  - Number of words in the family
  //  - Collapsible list of words, each with: word, POS, meaning, Bengali, mnemonic,
  //    frequency badge, pronunciation button, and a link to the word's detail page
  import { loadRoots, type RootFamily } from '../lib/vocab-data';
  import ProblematicButton from './ProblematicButton.svelte';
  import PronounceButton from './PronounceButton.svelte';
  import WordLinkButton from './WordLinkButton.svelte';

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
  const PAGE_SIZE = 20;

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    let result = roots.filter((r) => {
      if (!q) return true;
      if (r.root.toLowerCase().includes(q)) return true;
      if (r.rm.toLowerCase().includes(q)) return true;
      if (r.rbn.includes(q)) return true;
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

  // Track which roots are expanded (show full word list)
  let expandedRoots = $state<Set<string>>(new Set());

  function toggleRoot(root: string) {
    const next = new Set(expandedRoots);
    if (next.has(root)) next.delete(root);
    else next.add(root);
    expandedRoots = next;
  }

  function handleQuery(v: string) {
    query = v;
    page = 1;
  }
</script>

<div class="space-y-4">
  <!-- Search & filter bar (NOT sticky — scrolls with page) -->
  <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
        <input
          type="search"
          value={query}
          oninput={(e) => handleQuery((e.target as HTMLInputElement).value)}
          placeholder="Search roots, meanings, or words..."
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
        {@const expanded = expandedRoots.has(fam.root)}
        {@const visibleWords = expanded ? fam.words : fam.words.slice(0, 5)}
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl overflow-hidden">
          <!-- Root header -->
          <div class="px-5 pt-4 pb-3 bg-gradient-to-br from-rose-50 to-pink-50 dark:from-rose-950/30 dark:to-pink-950/30 border-b border-rose-200 dark:border-rose-800">
            <div class="flex items-start justify-between gap-3 flex-wrap">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <h3 class="text-2xl font-bold tracking-tight text-rose-900 dark:text-rose-200 break-words">{fam.root}</h3>
                  <PronounceButton word={fam.root} size="sm" />
                </div>
                <p class="text-sm text-zinc-700 dark:text-zinc-300 mt-1 leading-relaxed">
                  <span class="font-medium">{fam.rm}</span>
                  {#if fam.rbn}
                    <span class="mx-2 text-zinc-400">·</span>
                    <span class="font-bengali" lang="bn">{fam.rbn}</span>
                  {/if}
                </p>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <ProblematicButton itemType="root" itemKey={fam.root} subType={fam.rm} label="Mark root" />
                <div class="text-right">
                  <div class="text-2xl font-bold tabular-nums text-rose-700 dark:text-rose-300">{fam.words.length}</div>
                  <div class="text-[10px] text-zinc-500">words</div>
                </div>
              </div>
            </div>
          </div>
          <!-- Word list -->
          <ul class="divide-y divide-zinc-100 dark:divide-zinc-800">
            {#each visibleWords as w}
              <li class="px-5 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                <div class="flex items-start justify-between gap-3 flex-wrap">
                  <div class="min-w-0 flex-1">
                    <div class="flex items-baseline gap-2 flex-wrap">
                      <span class="text-base font-semibold text-zinc-900 dark:text-zinc-100 capitalize break-words">{w.w}</span>
                      {#if w.pos}
                        <span class="text-[10px] italic text-zinc-500">{w.pos}</span>
                      {/if}
                      <!-- Pronunciation + word-link buttons -->
                      <PronounceButton word={w.w} size="xs" />
                      <WordLinkButton word={w.w} size="xs" />
                      {#if w.n > 0}
                        <span class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 tabular-nums">{w.n}× in PYQ</span>
                      {/if}
                    </div>
                    {#if w.mean}
                      <div class="text-sm text-zinc-700 dark:text-zinc-300 mt-0.5 leading-relaxed">{w.mean}</div>
                    {/if}
                    {#if w.bn}
                      <div class="text-xs text-zinc-600 dark:text-zinc-400 font-bengali mt-0.5" lang="bn">{w.bn}</div>
                    {/if}
                    {#if w.mn}
                      <div class="text-[11px] text-amber-700 dark:text-amber-400 italic mt-1 break-words">
                        💡 {w.mn}
                      </div>
                    {/if}
                  </div>
                </div>
              </li>
            {/each}
          </ul>
          {#if fam.words.length > 5}
            <button
              onclick={() => toggleRoot(fam.root)}
              class="w-full px-5 py-2.5 text-xs font-medium text-rose-700 dark:text-rose-300 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors border-t border-rose-100 dark:border-rose-900/50 flex items-center justify-center gap-1.5"
            >
              {expanded ? 'Show less' : `Show all ${fam.words.length} words`}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="transition-transform {expanded ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
            </button>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  {#if totalPages > 1}
    <div class="flex items-center justify-center gap-2 pt-2">
      <button disabled={currentPage === 1} onclick={() => (page = currentPage - 1)} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Previous</button>
      <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
      <button disabled={currentPage === totalPages} onclick={() => (page = currentPage + 1)} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Next</button>
    </div>
  {/if}
</div>
