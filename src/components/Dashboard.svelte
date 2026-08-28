<script lang="ts">
  // src/components/Dashboard.svelte
  import FrequencyBadge from './FrequencyBadge.svelte';
  import { loadSummary, loadWords, type WordEntry, type SummaryStats } from '../lib/vocab-data';

  let summary = $state<SummaryStats | null>(null);
  let words = $state<WordEntry[]>([]);
  let loading = $state(true);

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        summary = await loadSummary();
        words = await loadWords();
      } catch (err) {
        console.error('Failed to load summary/words:', err);
      } finally {
        loading = false;
      }
    })();
  }

  // Compute top words
  const topWords = $derived([...words].sort((a, b) => b.total - a.total).slice(0, 10));
  const topStems = $derived([...words].filter((w) => w.asStem > 0).sort((a, b) => b.asStem - a.asStem).slice(0, 10));
  // For Module 2 (Options): only syn/ant option words (per user request)
  const topOptions = $derived(
    [...words]
      .filter((w) => {
        const saOpt = (w.qtypesAsOption['synonym'] ?? 0) + (w.qtypesAsOption['antonym'] ?? 0);
        return saOpt > 0;
      })
      .sort((a, b) => {
        const aSA = (a.qtypesAsOption['synonym'] ?? 0) + (a.qtypesAsOption['antonym'] ?? 0);
        const bSA = (b.qtypesAsOption['synonym'] ?? 0) + (b.qtypesAsOption['antonym'] ?? 0);
        return bSA - aSA;
      })
      .slice(0, 10)
  );

  // Navigate to a section page
  function navigate(href: string) {
    if (typeof window !== 'undefined') window.location.href = href;
  }
  function selectWord(w: WordEntry) {
    if (typeof window !== 'undefined') window.location.href = `/word/${encodeURIComponent(w.wordLower)}`;
  }

  const modules = $derived([
    { href: '/stems', title: 'Module 1 — Main Question Stems', desc: 'Words that appeared as the main question word in synonym/antonym questions. Sorted most-repeated → least.', count: summary?.totalSynonymAntonym ?? 0, top: topStems[0]?.asStem ?? 0, accent: 'amber', icon: 'stems' },
    { href: '/options', title: 'Module 2 — Syn/Ant Option Choices', desc: 'Words that appeared as option choices in synonym/antonym questions only. Sorted most-repeated → least.', count: summary?.totalSynonymAntonym ?? 0, top: (topOptions[0]?.qtypesAsOption['synonym'] ?? 0) + (topOptions[0]?.qtypesAsOption['antonym'] ?? 0) ?? 0, accent: 'emerald', icon: 'options' },
    { href: '/ows', title: 'Module 3 — One-Word Substitution', desc: 'Words that appeared as the correct answer in one-word substitution questions. Sorted by frequency.', count: summary?.totalOneWord ?? 0, top: 0, accent: 'violet', icon: 'ows' },
    { href: '/idioms', title: 'Module 4 — Idioms & Phrases', desc: 'Idiom phrases that appeared as the question stem (e.g. "By and by", "tip of the iceberg"). Sorted by frequency.', count: summary?.totalIdioms ?? 0, top: 0, accent: 'orange', icon: 'idiom' },
    { href: '/homonyms', title: 'Module 5 — Homonyms & Homophones', desc: 'Correct homonym words from fill-in-the-blank questions (e.g. add, aid, aide).', count: summary?.totalHomonyms ?? 0, top: 0, accent: 'pink', icon: 'homonym' },
    { href: '/spelling', title: 'Module 6 — Spelling', desc: 'Correctly-spelt words from spelling questions. Sorted by frequency.', count: summary?.totalSpelling ?? 0, top: 0, accent: 'sky', icon: 'spelling' },
    { href: '/roots', title: 'Module 7 — Root Words', desc: 'All 1,603 Latin/Greek root families with their word lists, Bengali meanings, and tricks to remember.', count: summary?.totalRoots ?? 0, top: 0, accent: 'rose', icon: 'roots' },
  ] as const);

  const accentMap: Record<string, { bg: string; text: string; border: string }> = {
    amber: { bg: 'bg-amber-100 dark:bg-amber-950/40', text: 'text-amber-700 dark:text-amber-300', border: 'hover:border-amber-400/40' },
    emerald: { bg: 'bg-emerald-100 dark:bg-emerald-950/40', text: 'text-emerald-700 dark:text-emerald-300', border: 'hover:border-emerald-400/40' },
    violet: { bg: 'bg-violet-100 dark:bg-violet-950/40', text: 'text-violet-700 dark:text-violet-300', border: 'hover:border-violet-400/40' },
    orange: { bg: 'bg-orange-100 dark:bg-orange-950/40', text: 'text-orange-700 dark:text-orange-300', border: 'hover:border-orange-400/40' },
    pink: { bg: 'bg-pink-100 dark:bg-pink-950/40', text: 'text-pink-700 dark:text-pink-300', border: 'hover:border-pink-400/40' },
    sky: { bg: 'bg-sky-100 dark:bg-sky-950/40', text: 'text-sky-700 dark:text-sky-300', border: 'hover:border-sky-400/40' },
    rose: { bg: 'bg-rose-100 dark:bg-rose-950/40', text: 'text-rose-700 dark:text-rose-300', border: 'hover:border-rose-400/40' },
  };
</script>

<div class="space-y-6">
  {#if loading || !summary}
    <div class="space-y-4">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        {#each Array(4) as _}<div class="h-24 rounded-xl bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}
      </div>
    </div>
  {:else}
    <!-- Hero stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      {#each [{ icon: '📄', label: 'SSC Exam Papers', value: summary.totalFiles, sub: 'CGL/CHSL/CPO/MTS (2019-2026)' },
              { icon: '❓', label: 'Total Questions', value: summary.totalQuestions, sub: `across 6 question types` },
              { icon: '📚', label: 'Unique Vocabulary', value: summary.totalUniqueWords, sub: 'words, idiom phrases, roots' },
              { icon: '🌱', label: 'Root Word Families', value: summary.totalRoots, sub: 'Latin/Greek roots with families' }] as stat}
        <div class="border border-orange-200 dark:border-orange-800 rounded-xl bg-white dark:bg-zinc-900 p-4 space-y-1.5">
          <div class="flex items-center gap-1.5 text-xs font-medium text-zinc-500">
            <span class="text-base">{stat.icon}</span>
            {stat.label}
          </div>
          <div class="text-2xl font-bold tabular-nums tracking-tight">{stat.value.toLocaleString()}</div>
          <div class="text-[10px] text-zinc-500 leading-snug">{stat.sub}</div>
        </div>
      {/each}
    </div>

    <!-- Question-type breakdown -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4">
      <h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-500"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        Question Type Breakdown
      </h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
        {#each Object.entries(summary.byType).sort((a, b) => b[1] - a[1]) as [qtype, count]}
          <button
            on:click={() => {
              const hrefMap: Record<string, string> = {
                synonym: '/stems',
                antonym: '/stems',
                'one-word': '/ows',
                idiom: '/idioms',
                homonym: '/homonyms',
                spelling: '/spelling',
              };
              navigate(hrefMap[qtype] || '/');
            }}
            class="text-left border border-zinc-200 dark:border-zinc-700 rounded-md p-2 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
          >
            <div class="text-[10px] uppercase font-semibold text-zinc-500 tracking-wide capitalize">{qtype}</div>
            <div class="text-xl font-bold tabular-nums">{count.toLocaleString()}</div>
            <div class="text-[10px] text-zinc-500 mt-0.5">questions</div>
          </button>
        {/each}
      </div>
    </div>

    <!-- Module navigation -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each modules as mod}
        <button
          on:click={() => navigate(mod.href)}
          class="text-left cursor-pointer transition-all duration-200 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-orange-400/40 overflow-hidden group bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4 {accentMap[mod.accent].border}"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="h-11 w-11 rounded-lg flex items-center justify-center shrink-0 {accentMap[mod.accent].bg} {accentMap[mod.accent].text}">
              {#if mod.icon === 'stems'}
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 7h6v6"/><path d="m22 7-8.5 8.5-5-5L2 17"/></svg>
              {:else if mod.icon === 'options'}
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/></svg>
              {:else if mod.icon === 'ows'}
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3"/><path d="M9 22h6"/><path d="M12 18v4"/><path d="M4 7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2"/></svg>
              {:else if mod.icon === 'idiom'}
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
              {:else if mod.icon === 'homonym'}
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V12"/><path d="M2 12h20"/><circle cx="12" cy="6" r="4"/></svg>
              {:else if mod.icon === 'spelling'}
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="m9 11 2 2 4-4"/></svg>
              {:else if mod.icon === 'roots'}
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/><circle cx="12" cy="12" r="9"/></svg>
              {/if}
            </div>
            <div class="text-right">
              <div class="text-2xl font-bold tabular-nums {accentMap[mod.accent].text}">{mod.count.toLocaleString()}</div>
              <div class="text-[10px] text-zinc-500">{mod.href === '/roots' ? 'families' : mod.href === '/stems' || mod.href === '/options' ? 'questions' : 'questions'}</div>
            </div>
          </div>
          <h3 class="text-base font-semibold mt-2">{mod.title}</h3>
          <p class="text-xs text-zinc-500 leading-relaxed mt-1">{mod.desc}</p>
        </button>
      {/each}
    </div>

    <!-- Top words preview -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
        <div class="px-4 pt-3 pb-2 flex items-center justify-between">
          <span class="text-sm font-semibold flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-600"><path d="M16 7h6v6"/><path d="m22 7-8.5 8.5-5-5L2 17"/></svg>
            Top 10 Most Frequent Question Stems
          </span>
          <a href="/stems" class="text-xs h-7 px-2 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-md flex items-center gap-1">
            View all
            <svg class="h-3 w-3" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </a>
        </div>
        <div class="pt-1 px-2 pb-3">
          <ol class="space-y-1">
            {#each topStems as w, i}
              <li
                role="button"
                tabindex="0"
                on:click={() => selectWord(w)}
                on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectWord(w); } }}
                class="flex items-center justify-between gap-2 px-2 py-1.5 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer transition-colors text-sm"
              >
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-[10px] font-mono text-zinc-500 tabular-nums w-5 shrink-0">#{i + 1}</span>
                  <span class="font-medium truncate">{w.word}</span>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <FrequencyBadge label="Stem" count={w.asStem} variant="stem" size="sm" />
                  <FrequencyBadge label="Opt" count={w.asOption} variant="option" size="sm" />
                </div>
              </li>
            {/each}
          </ol>
        </div>
      </div>
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
        <div class="px-4 pt-3 pb-2 flex items-center justify-between">
          <span class="text-sm font-semibold flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-emerald-600"><path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/></svg>
            Top 10 Syn/Ant Option Words
          </span>
          <a href="/options" class="text-xs h-7 px-2 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-md flex items-center gap-1">
            View all
            <svg class="h-3 w-3" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </a>
        </div>
        <div class="pt-1 px-2 pb-3">
          <ol class="space-y-1">
            {#each topOptions as w, i}
              <li
                role="button"
                tabindex="0"
                on:click={() => selectWord(w)}
                on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectWord(w); } }}
                class="flex items-center justify-between gap-2 px-2 py-1.5 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer transition-colors text-sm"
              >
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-[10px] font-mono text-zinc-500 tabular-nums w-5 shrink-0">#{i + 1}</span>
                  <span class="font-medium truncate">{w.word}</span>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <FrequencyBadge label="Stem" count={w.asStem} variant="stem" size="sm" />
                  <FrequencyBadge label="Opt" count={(w.qtypesAsOption['synonym'] ?? 0) + (w.qtypesAsOption['antonym'] ?? 0)} variant="option" size="sm" />
                </div>
              </li>
            {/each}
          </ol>
        </div>
      </div>
    </div>
  {/if}
</div>
