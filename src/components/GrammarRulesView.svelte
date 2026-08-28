<script lang="ts">
  // src/components/GrammarRulesView.svelte
  // Grammar Rules page: searchable, topic-filtered accordion of rules.
  // Each rule expands to show concept + examples + practice MCQs.
  import type { GrammarRule, GrammarQuestion } from '../lib/grammar-data';
  import { loadGrammarRules, loadQuestionsForRule } from '../lib/grammar-data';
  import GrammarMCQCard from './GrammarMCQCard.svelte';
  import ProblematicButton from './ProblematicButton.svelte';

  let rules = $state<GrammarRule[]>([]);
  let loading = $state(true);
  let query = $state('');
  let topicFilter = $state('all');
  let page = $state(1);
  let expandedRule = $state<string | null>(null);
  let ruleQs = $state<Record<string, GrammarQuestion[]>>({});
  let ruleLoading = $state<Record<string, boolean>>({});
  let ruleQIdx = $state<Record<string, number>>({});

  const PAGE_SIZE = 25;

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        rules = await loadGrammarRules();
      } catch (e) { console.error(e); }
      finally { loading = false; }
    })();
  }

  const topics = $derived(['all', ...Array.from(new Set(rules.map((r) => r.topic).filter(Boolean))).sort()]);
  const sourceBadge: Record<string, string> = {
    rani: 'Rani', error: 'Error PDF', aman: 'Aman', pyq: 'PYQ',
  };

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    let res = rules.filter((r) => {
      if (topicFilter !== 'all' && r.topic !== topicFilter) return false;
      if (q && !(`${r.no} ${r.title} ${r.topic} ${r.concept}`.toLowerCase().includes(q))) return false;
      return true;
    });
    return res;
  });

  const totalPages = $derived(Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)));
  const currentPage = $derived(Math.min(page, totalPages));
  const pageItems = $derived(filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));

  function toggleExpand(r: GrammarRule) {
    if (expandedRule === r.id) {
      expandedRule = null;
      return;
    }
    expandedRule = r.id;
    if (!ruleQs[r.id] && !ruleLoading[r.id]) {
      ruleLoading[r.id] = true;
      loadQuestionsForRule(r.id).then((qs) => {
        ruleQs[r.id] = qs;
        ruleLoading[r.id] = false;
      });
    }
  }
  function qsFor(r: GrammarRule): GrammarQuestion[] {
    return ruleQs[r.id] || [];
  }
  function visibleQs(r: GrammarRule): GrammarQuestion[] {
    const all = qsFor(r);
    return all;
  }
  function prevRuleQ(ruleId: string) {
    const i = ruleQIdx[ruleId] ?? 0;
    if (i > 0) ruleQIdx[ruleId] = i - 1;
  }
  function nextRuleQ(ruleId: string) {
    const i = ruleQIdx[ruleId] ?? 0;
    const total = (ruleQs[ruleId] || []).length;
    if (i < total - 1) ruleQIdx[ruleId] = i + 1;
  }
</script>

<div class="space-y-4">
  <div class="sticky top-1 z-20 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <input type="search" value={query} oninput={(e) => { query = (e.target as HTMLInputElement).value; page = 1; }} placeholder="Search rules (e.g. since, subject-verb, pronoun)..." class="w-full pl-9 pr-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40" />
      </div>
      <select bind:value={topicFilter} onchange={() => { page = 1; }} class="h-9 px-3 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40">
        {#each topics as t}<option value={t}>{t === 'all' ? 'All topics' : t}</option>{/each}
      </select>
    </div>
    <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span><span class="font-semibold text-zinc-900 dark:text-zinc-100">{filtered.length.toLocaleString()}</span> rules · click any card to expand</span>
      {#if totalPages > 1}<span class="ml-auto">page {currentPage} / {totalPages}</span>{/if}
    </div>
  </div>

  {#if loading}
    <div class="space-y-2">{#each Array(6) as _}<div class="h-16 rounded-lg bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}</div>
  {:else if pageItems.length === 0}
    <div class="text-center py-12 border-2 border-dashed rounded-lg"><p class="text-sm text-zinc-500">No rules match your search.</p></div>
  {:else}
    <div class="space-y-2">
      {#each pageItems as r, i (r.id)}
        {@const rank = (currentPage - 1) * PAGE_SIZE + i + 1}
        {@const expanded = expandedRule === r.id}
        {@const qcount = r.questionIds?.length ?? 0}
        <article class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <button onclick={() => toggleExpand(r)} class="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
            <span class="text-xs font-mono text-zinc-500 tabular-nums shrink-0 w-8">#{r.no}</span>
            <div class="flex-1 min-w-0">
              <h3 class="text-base font-semibold tracking-tight truncate">{r.title}</h3>
              {#if r.topic}<p class="text-[11px] text-zinc-500 truncate">{r.topic}</p>{/if}
            </div>
            <div class="flex items-center gap-1 shrink-0 flex-wrap justify-end">
              {#each r.sources.slice(0,4) as s}<span class="text-[9px] font-medium border rounded px-1.5 py-0.5 bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700">{sourceBadge[s] ?? s}</span>{/each}
            </div>
            <span class="shrink-0 text-[11px] text-zinc-500 tabular-nums">{qcount} Q</span>
            <span class="shrink-0 text-zinc-400">{expanded ? '▲' : '▼'}</span>
          </button>
          {#if expanded}
            <div class="px-4 pb-4 pt-1 space-y-4 border-t border-zinc-100 dark:border-zinc-800">
              <div class="flex items-start justify-between gap-3 flex-wrap">
                <div class="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300 flex-1 min-w-0">
                  <span class="font-semibold text-orange-600 dark:text-orange-400">Rule: </span>{r.concept}
                </div>
                <ProblematicButton itemType="grammar-rule" itemKey={r.id} subType={r.topic} label="Mark rule" />
              </div>
              {#if r.examples && r.examples.length}
                <div class="space-y-1.5">
                  <div class="text-[11px] uppercase font-semibold text-zinc-500 tracking-wide">Examples</div>
                  {#each r.examples.slice(0,4) as ex}
                    <div class="text-xs bg-rose-50 dark:bg-rose-950/20 border-l-2 border-rose-300 dark:border-rose-700 p-2 rounded-r-md">
                      {#if ex.incorrect}<span class="text-rose-700 dark:text-rose-300">✗ {ex.incorrect}</span><br/>{/if}
                      {#if ex.correct}<span class="text-emerald-700 dark:text-emerald-300">✓ {ex.correct}</span>{/if}
                      {#if ex.sentence && !ex.incorrect}<span>{ex.sentence}</span> <span class="text-emerald-700 dark:text-emerald-300">→ {ex.correction || ''}</span>{/if}
                    </div>
                  {/each}
                </div>
              {/if}
              {#if ruleLoading[r.id]}
                <div class="text-xs text-zinc-400 py-3 text-center">Loading questions…</div>
              {:else if qsFor(r).length}
                {@const qs = qsFor(r)}
                {@const idx = ruleQIdx[r.id] ?? 0}
                {@const cur = qs[idx]}
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <div class="text-[11px] uppercase font-semibold text-zinc-500 tracking-wide">Practice MCQs ({qs.length})</div>
                    <span class="text-[11px] text-zinc-500 tabular-nums">{idx + 1} / {qs.length}</span>
                  </div>
                  {#if cur}
                    <GrammarMCQCard question={cur} index={idx} />
                  {/if}
                  <div class="flex items-center justify-between pt-2 border-t border-zinc-100 dark:border-zinc-800">
                    <button onclick={() => prevRuleQ(r.id)} disabled={idx === 0} class="flex items-center gap-1.5 text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>Previous
                    </button>
                    <button onclick={() => nextRuleQ(r.id)} disabled={idx === qs.length - 1} class="flex items-center gap-1.5 text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed">
                      Next<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
                    </button>
                  </div>
                </div>
              {:else}
                <p class="text-xs text-zinc-400 italic">No practice MCQs mapped to this rule yet.</p>
              {/if}
            </div>
          {/if}
        </article>
      {/each}
    </div>
    {#if totalPages > 1}
      <div class="flex items-center justify-center gap-2 pt-2">
        <button disabled={currentPage === 1} onclick={() => { page = currentPage - 1; expandedRule = null; }} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 hover:bg-zinc-50 dark:hover:bg-zinc-800">Previous</button>
        <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
        <button disabled={currentPage === totalPages} onclick={() => { page = currentPage + 1; expandedRule = null; }} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 hover:bg-zinc-50 dark:hover:bg-zinc-800">Next</button>
      </div>
    {/if}
  {/if}
</div>
