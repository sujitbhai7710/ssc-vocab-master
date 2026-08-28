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
    onNavigate?: (view: 'stems' | 'options') => void;
    onSelectWord?: (w: WordEntry) => void;
  } = $props();
</script>

<div class="space-y-6">
  <!-- Hero stats -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
    {#each [{ icon: '📄', label: 'SSC Exam Papers', value: summary.totalFiles, sub: 'across 4 exams (2019-2026)' },
            { icon: '✓', label: 'Synonym / Antonym Qs', value: summary.totalSynonymAntonym, sub: 'parsed from past papers' },
            { icon: '⊞', label: 'One-word Substitution Qs', value: summary.totalOneWord, sub: 'group-of-words → single word' },
            { icon: '📚', label: 'Unique Vocabulary Words', value: summary.totalUniqueWords, sub: 'appeared as stem or option' }] as stat}
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

  <!-- Module navigation -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <button
      on:click={() => onNavigate('stems')}
      class="text-left cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-orange-400/40 focus:outline-none focus:ring-2 focus:ring-orange-400/40 overflow-hidden group bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="h-11 w-11 rounded-lg flex items-center justify-center shrink-0 bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 7h6v6"/><path d="m22 7-8.5 8.5-5-5L2 17"/></svg>
        </div>
        <svg class="h-4 w-4 text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-white transition-colors" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      </div>
      <h3 class="text-base font-semibold mt-2">Module 1 — Main Question Stems</h3>
      <p class="text-xs text-zinc-500 leading-relaxed mt-1">Words that appeared as the main question word in synonym/antonym questions. Sorted from most repeated to least repeated.</p>
      <div class="pt-1">
        <span class="text-[10px] font-medium border border-zinc-200 dark:border-zinc-700 px-2 py-0.5 rounded-md">Top word: {topStems[0]?.asStem ?? 0} times</span>
      </div>
    </button>
    <button
      on:click={() => onNavigate('options')}
      class="text-left cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-orange-400/40 focus:outline-none focus:ring-2 focus:ring-orange-400/40 overflow-hidden group bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="h-11 w-11 rounded-lg flex items-center justify-center shrink-0 bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/></svg>
        </div>
        <svg class="h-4 w-4 text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-white transition-colors" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      </div>
      <h3 class="text-base font-semibold mt-2">Module 2 — Option Choices</h3>
      <p class="text-xs text-zinc-500 leading-relaxed mt-1">Words that appeared strictly as one of the four option choices. Sorted from most repeated to least repeated.</p>
      <div class="pt-1">
        <span class="text-[10px] font-medium border border-zinc-200 dark:border-zinc-700 px-2 py-0.5 rounded-md">Top word: {topOptions[0]?.asOption ?? 0} times</span>
      </div>
    </button>
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
            <div class="text-[10px] text-zinc-500 mt-0.5">{f.questions} synonym/antonym Qs</div>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>
