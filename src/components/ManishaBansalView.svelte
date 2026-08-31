<script lang="ts">
  // src/components/ManishaBansalView.svelte
  // Manisha Bansal's 120 Grammar Rules — accordion-style display matching
  // the Penacia grammar site layout, using our light theme colors.
  // Each rule expands to show: explanation, usage notes, examples, trick.
  // Includes: search, category filter, problematic button, progress tracking.
  import { onMount, onDestroy } from 'svelte';
  import { isLoggedIn, loadSession, onAuthChange, addProblematic, removeProblematic, listProblematic, type ProblematicItem } from '../lib/auth';
  import ProblematicButton from './ProblematicButton.svelte';
  import ProgressTracker from './ProgressTracker.svelte';

  interface UsageNote { term: string; desc: string; }
  interface Rule {
    num: number;
    title: string;
    cat: string;
    explain: string;
    usage?: UsageNote[];
    examples?: string[];
    trick?: string;
  }

  let rules = $state<Rule[]>([]);
  let loading = $state(true);
  let query = $state('');
  let catFilter = $state('all');
  let page = $state(1);
  let expandedRule = $state<number | null>(null);
  const PAGE_SIZE = 15;

  // Problematic tracking
  let loggedIn = $state(false);
  let problematicSet = $state<Set<string>>(new Set());
  let unsub: (() => void) | null = null;

  const categories = [
    { key: 'all', label: 'All' },
    { key: 'pronouns', label: 'Pronouns' },
    { key: 'determiners', label: 'Determiners' },
    { key: 'conjunctions', label: 'Conjunctions' },
    { key: 'modals', label: 'Modals' },
    { key: 'prepositions', label: 'Prepositions' },
    { key: 'tenses', label: 'Tenses' },
    { key: 'agreement', label: 'Agreement' },
    { key: 'confusables', label: 'Confusables' },
    { key: 'style', label: 'Style' },
  ];

  const catColors: Record<string, string> = {
    pronouns: 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800',
    determiners: 'bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950/40 dark:text-violet-200 dark:border-violet-800',
    conjunctions: 'bg-orange-100 text-orange-900 border-orange-300 dark:bg-orange-950/40 dark:text-orange-200 dark:border-orange-800',
    modals: 'bg-pink-100 text-pink-900 border-pink-300 dark:bg-pink-950/40 dark:text-pink-200 dark:border-pink-800',
    prepositions: 'bg-teal-100 text-teal-900 border-teal-300 dark:bg-teal-950/40 dark:text-teal-200 dark:border-teal-800',
    tenses: 'bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800',
    agreement: 'bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800',
    confusables: 'bg-rose-100 text-rose-900 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800',
    style: 'bg-zinc-100 text-zinc-900 border-zinc-300 dark:bg-zinc-800/40 dark:text-zinc-200 dark:border-zinc-700',
  };

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        const res = await fetch('/data/manisha/rules.json');
        if (res.ok) rules = await res.json();
      } catch (e) { console.error('Failed to load manisha rules:', e); }
      finally { loading = false; }
    })();
  }

  async function refreshProblematic() {
    if (!isLoggedIn()) return;
    try {
      const items = await listProblematic('manisha-rule');
      problematicSet = new Set(items.map(i => i.item_key));
    } catch {}
  }

  onMount(async () => {
    await loadSession();
    loggedIn = isLoggedIn();
    unsub = onAuthChange((u) => {
      const now = !!u;
      if (now !== loggedIn) { loggedIn = now; if (now) refreshProblematic(); }
    });
    if (loggedIn) await refreshProblematic();
  });
  onDestroy(() => { unsub?.(); });

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    let result = rules.filter((r) => {
      if (catFilter !== 'all' && r.cat !== catFilter) return false;
      if (q) {
        const haystack = `${r.num} ${r.title} ${r.cat} ${r.explain} ${r.trick || ''}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
    return result;
  });

  const totalPages = $derived(Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)));
  const currentPage = $derived(Math.min(page, totalPages));
  const pageItems = $derived(filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));

  function toggleExpand(num: number) {
    expandedRule = expandedRule === num ? null : num;
  }
  function handleQuery(v: string) { query = v; page = 1; expandedRule = null; }
</script>

<div class="space-y-4">
  <!-- Search & filter bar -->
  <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <input
          type="search"
          value={query}
          oninput={(e) => handleQuery((e.target as HTMLInputElement).value)}
          placeholder="Search rules..."
          class="w-full pl-9 pr-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
        />
      </div>
      <select
        bind:value={catFilter}
        onchange={() => { page = 1; expandedRule = null; }}
        class="h-9 px-3 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
      >
        {#each categories as c}
          <option value={c.key}>{c.label}</option>
        {/each}
      </select>
    </div>
    <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span>
        <span class="font-semibold text-zinc-900 dark:text-zinc-100">{filtered.length}</span> rules
        {#if query}matching "{query}"{/if}
      </span>
      {#if totalPages > 1}<span class="ml-auto">page {currentPage} / {totalPages}</span>{/if}
    </div>
  </div>

  <ProgressTracker client:idle pageType="manisha-bansal" total={120} />

  {#if loading}
    <div class="space-y-3">
      {#each Array(5) as _}<div class="h-24 rounded-xl bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}
    </div>
  {:else if pageItems.length === 0}
    <div class="text-center py-12 border-2 border-dashed rounded-lg">
      <p class="text-sm text-zinc-500">No rules match your search.</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each pageItems as r (r.num)}
        {@const expanded = expandedRule === r.num}
        <article class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <button
            onclick={() => toggleExpand(r.num)}
            class="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
          >
            <span class="text-xs font-mono text-zinc-500 tabular-nums shrink-0 w-10 pt-0.5">#{r.num}</span>
            <div class="flex-1 min-w-0">
              <h3 class="text-base font-semibold tracking-tight break-words leading-snug">{r.title}</h3>
              <span class="inline-block mt-1 text-[10px] font-medium border rounded px-1.5 py-0.5 capitalize {catColors[r.cat] || catColors.style}">{r.cat}</span>
            </div>
            <span class="shrink-0 text-zinc-400 pt-0.5">{expanded ? '▲' : '▼'}</span>
          </button>
          {#if expanded}
            <div class="px-4 pb-4 pt-1 space-y-4 border-t border-zinc-100 dark:border-zinc-800">
              <!-- Title shown clearly first -->
              <div class="flex items-start justify-between gap-3 flex-wrap">
                <div class="flex-1 min-w-0">
                  <h4 class="text-base font-bold tracking-tight break-words leading-snug">{r.title}</h4>
                  <span class="inline-block mt-1 text-[10px] font-medium border rounded px-1.5 py-0.5 capitalize {catColors[r.cat] || catColors.style}">{r.cat}</span>
                </div>
                <ProblematicButton itemType="manisha-rule" itemKey={String(r.num)} subType={r.cat} label="Mark rule" />
              </div>

              <!-- Explanation -->
              {#if r.explain}
                <div class="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">{@html r.explain}</div>
              {/if}

              <!-- Usage notes -->
              {#if r.usage && r.usage.length > 0}
                <div class="space-y-1.5">
                  <div class="text-[11px] uppercase font-semibold text-zinc-500 tracking-wide">Usage</div>
                  {#each r.usage as u}
                    <div class="text-xs bg-zinc-50 dark:bg-zinc-800/40 p-2 rounded-md border border-zinc-200 dark:border-zinc-700">
                      <span class="font-semibold text-orange-600 dark:text-orange-400">{u.term}:</span>
                      <span class="text-zinc-700 dark:text-zinc-300">{u.desc}</span>
                    </div>
                  {/each}
                </div>
              {/if}

              <!-- Examples -->
              {#if r.examples && r.examples.length > 0}
                <div class="space-y-1.5">
                  <div class="text-[11px] uppercase font-semibold text-zinc-500 tracking-wide">Examples</div>
                  {#each r.examples as ex}
                    <div class="text-xs font-mono bg-zinc-50 dark:bg-zinc-800/40 p-2 rounded-md border border-zinc-200 dark:border-zinc-700 {ex.startsWith('✓') ? 'text-emerald-700 dark:text-emerald-300' : ex.startsWith('✗') ? 'text-rose-700 dark:text-rose-300' : 'text-zinc-700 dark:text-zinc-300'}">
                      {ex}
                    </div>
                  {/each}
                </div>
              {/if}

              <!-- Trick -->
              {#if r.trick}
                <div class="bg-amber-50 dark:bg-amber-950/20 border-l-2 border-amber-300 dark:border-amber-700 p-2.5 rounded-r-md text-sm">
                  <span class="font-semibold text-amber-700 dark:text-amber-400">💡 Trick: </span>
                  <span class="text-zinc-700 dark:text-zinc-300">{@html r.trick}</span>
                </div>
              {/if}
            </div>
          {/if}
        </article>
      {/each}
    </div>
  {/if}

  {#if totalPages > 1}
    <div class="flex items-center justify-center gap-2 pt-2">
      <button disabled={currentPage === 1} onclick={() => { page = currentPage - 1; expandedRule = null; }} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 hover:bg-zinc-50 dark:hover:bg-zinc-800">Previous</button>
      <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
      <button disabled={currentPage === totalPages} onclick={() => { page = currentPage + 1; expandedRule = null; }} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 hover:bg-zinc-50 dark:hover:bg-zinc-800">Next</button>
    </div>
  {/if}
</div>
