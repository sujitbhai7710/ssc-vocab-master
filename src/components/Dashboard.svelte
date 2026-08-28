<script lang="ts">
  // src/components/Dashboard.svelte
  import FrequencyBadge from './FrequencyBadge.svelte';
  import type { SummaryStats, WordEntry } from '../lib/vocab-data';

  let {
    summary,
    topWords = [],
    topStems = [],
    topOptions = [],
    onNavigate = () => {},
    onSelectWord = () => {},
  }: {
    summary: SummaryStats;
    topWords?: WordEntry[];
    topStems?: WordEntry[];
    topOptions?: WordEntry[];
    onNavigate?: (view: 'stems' | 'options' | 'ows' | 'idioms' | 'homonyms' | 'spelling') => void;
    onSelectWord?: (w: WordEntry) => void;
  } = $props();

  // Module cards config
  const modules = [
    { id: 'stems', title: 'Module 1 — Main Question Stems', desc: 'Words that appeared as the main question word in synonym/antonym questions. Sorted most-repeated → least.', count: summary.totalUniqueWords, top: topStems[0]?.asStem ?? 0, accent: 'amber', icon: 'stems' },
    { id: 'options', title: 'Module 2 — Option Choices', desc: 'Words that appeared strictly as one of the four option choices. Sorted most-repeated → least.', count: summary.totalUniqueWords, top: topOptions[0]?.asOption ?? 0, accent: 'emerald', icon: 'options' },
    { id: 'ows', title: 'Module 3 — One-Word Substitution', desc: 'Words that appeared as options in one-word substitution questions. Sorted by frequency in OWS questions.', count: summary.totalOneWord, top: 0, accent: 'violet', icon: 'ows' },
    { id: 'idioms', title: 'Module 4 — Idioms & Phrases', desc: 'Vocabulary words that appeared as options in idiom and phrase questions. Sorted by frequency.', count: summary.totalIdioms, top: 0, accent: 'orange', icon: 'idiom' },
    { id: 'homonyms', title: 'Module 5 — Homonyms & Homophones', desc: 'Words that appeared as options in homonym/homophone fill-in-the-blank questions.', count: summary.totalHomonyms, top: 0, accent: 'pink', icon: 'homonym' },
    { id: 'spelling', title: 'Module 6 — Spelling', desc: 'Words that appeared as options in correctly/incorrectly spelt questions. Sorted by frequency.', count: summary.totalSpelling, top: 0, accent: 'sky', icon: 'spelling' },
  ] as const;

  const accentMap: Record<string, { bg: string; text: string; border: string }> = {
    amber: { bg: 'bg-amber-100 dark:bg-amber-950/40', text: 'text-amber-700 dark:text-amber-300', border: 'hover:border-amber-400/40' },
    emerald: { bg: 'bg-emerald-100 dark:bg-emerald-950/40', text: 'text-emerald-700 dark:text-emerald-300', border: 'hover:border-emerald-400/40' },
    violet: { bg: 'bg-violet-100 dark:bg-violet-950/40', text: 'text-violet-700 dark:text-violet-300', border: 'hover:border-violet-400/40' },
    orange: { bg: 'bg-orange-100 dark:bg-orange-950/40', text: 'text-orange-700 dark:text-orange-300', border: 'hover:border-orange-400/40' },
    pink: { bg: 'bg-pink-100 dark:bg-pink-950/40', text: 'text-pink-700 dark:text-pink-300', border: 'hover:border-pink-400/40' },
    sky: { bg: 'bg-sky-100 dark:bg-sky-950/40', text: 'text-sky-700 dark:text-sky-300', border: 'hover:border-sky-400/40' },
  };
</script>

<div class="space-y-6">
  <!-- Hero stats -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
    {#each [{ icon: '📄', label: 'SSC Exam Papers', value: summary.totalFiles, sub: 'across 4 exams (2019-2026)' },
            { icon: '❓', label: 'Total Questions', value: summary.totalQuestions, sub: `across 6 question types` },
            { icon: '📚', label: 'Unique Vocabulary', value: summary.totalUniqueWords, sub: 'synonym/antonym/OWS options' },
            { icon: '⭐', label: 'Syn+Ant Qs', value: summary.totalSynonymAntonym, sub: 'the core vocab questions' }] as stat}
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
            if (qtype === 'synonym' || qtype === 'antonym') onNavigate('stems');
            else if (qtype === 'one-word') onNavigate('ows');
            else if (qtype === 'idiom') onNavigate('idioms');
            else if (qtype === 'homonym') onNavigate('homonyms');
            else if (qtype === 'spelling') onNavigate('spelling');
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
        on:click={() => onNavigate(mod.id as any)}
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
            {/if}
          </div>
          <div class="text-right">
            <div class="text-2xl font-bold tabular-nums {accentMap[mod.accent].text}">{mod.count.toLocaleString()}</div>
            <div class="text-[10px] text-zinc-500">{mod.id === 'stems' || mod.id === 'options' ? 'words' : 'questions'}</div>
          </div>
        </div>
        <h3 class="text-base font-semibold mt-2">{mod.title}</h3>
        <p class="text-xs text-zinc-500 leading-relaxed mt-1">{mod.desc}</p>
        {#if mod.id === 'stems' || mod.id === 'options'}
          <div class="pt-1">
            <span class="text-[10px] font-medium border border-zinc-200 dark:border-zinc-700 px-2 py-0.5 rounded-md">Top word: {mod.top} times</span>
          </div>
        {/if}
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
        <button on:click={() => onNavigate('stems')} class="text-xs h-7 px-2 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-md flex items-center gap-1">
          View all
          <svg class="h-3 w-3" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </button>
      </div>
      <div class="pt-1 px-2 pb-3">
        {#if topStems.length === 0}
          <p class="text-xs text-zinc-500 italic px-2">No stem words found.</p>
        {:else}
          <ol class="space-y-1">
            {#each topStems as w, i}
              <li
                role="button"
                tabindex="0"
                on:click={() => onSelectWord(w)}
                on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelectWord(w); } }}
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
        {/if}
      </div>
    </div>
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
      <div class="px-4 pt-3 pb-2 flex items-center justify-between">
        <span class="text-sm font-semibold flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-emerald-600"><path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/></svg>
          Top 10 Most Frequent Option Choices
        </span>
        <button on:click={() => onNavigate('options')} class="text-xs h-7 px-2 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-md flex items-center gap-1">
          View all
          <svg class="h-3 w-3" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </button>
      </div>
      <div class="pt-1 px-2 pb-3">
        {#if topOptions.length === 0}
          <p class="text-xs text-zinc-500 italic px-2">No option words found.</p>
        {:else}
          <ol class="space-y-1">
            {#each topOptions as w, i}
              <li
                role="button"
                tabindex="0"
                on:click={() => onSelectWord(w)}
                on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelectWord(w); } }}
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
        {/if}
      </div>
    </div>
  </div>

  <!-- Exam coverage -->
  <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
    <div class="px-4 pt-3 pb-2 text-sm font-semibold flex items-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-sky-600"><path d="M21 15V6"/><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M12 12H3"/><path d="M16 6H3"/><path d="M12 18H3"/></svg>
      Exam Coverage — {summary.totalFiles} SSC Papers (2019–2026)
    </div>
    <div class="px-4 pb-4 pt-1">
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
        {#each summary.questionsPerFile as f}
          <div class="border border-zinc-200 dark:border-zinc-700 rounded-md p-2 bg-zinc-50 dark:bg-zinc-800/30 hover:bg-zinc-100 dark:hover:bg-zinc-800/60 transition-colors">
            <div class="text-xs font-medium truncate" title={f.exam}>{f.exam.replace('SSC ', '')}</div>
            <div class="text-[10px] text-zinc-500 mt-0.5">{f.questions} vocab Qs</div>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>
