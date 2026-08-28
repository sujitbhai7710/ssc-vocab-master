<script lang="ts">
  // src/components/WordCard.svelte
  import FrequencyBadge from './FrequencyBadge.svelte';
  import type { WordEntry } from '../lib/vocab-data';

  let {
    word,
    rank,
    view,
    onSelect,
  }: {
    word: WordEntry;
    rank: number;
    view: 'stems' | 'options';
    onSelect: (w: WordEntry) => void;
  } = $props();

  function handleClick() {
    onSelect(word);
  }
  function handleKey(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(word);
    }
  }

  const allExams = $derived(Array.from(new Set([...word.stemExams, ...word.optionExams])));
</script>

<div
  role="button"
  tabindex="0"
  on:click={handleClick}
  on:keydown={handleKey}
  class="cursor-pointer transition-all duration-200 hover:shadow-md hover:border-orange-400/40 focus:outline-none focus:ring-2 focus:ring-orange-400/40 group p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:-translate-y-0.5"
>
  <div class="flex items-baseline gap-2 min-w-0 mb-2">
    <span class="text-xs font-mono text-zinc-500 tabular-nums">#{rank}</span>
    <h3 class="text-base font-semibold tracking-tight truncate group-hover:text-orange-600 transition-colors">
      {word.word}
    </h3>
  </div>
  <div class="flex flex-wrap gap-1.5 mb-2">
    <FrequencyBadge label="Stem" count={word.asStem} variant="stem" size="sm" />
    <FrequencyBadge label="Option" count={word.asOption} variant="option" size="sm" />
  </div>
  <div class="text-[11px] text-zinc-500 leading-relaxed">
    {#if view === 'stems'}
      <span class="font-semibold text-amber-700 dark:text-amber-400">{word.asStem}× as question stem</span>
      <span class="mx-1">•</span>
      <span>{word.asOption}× as option</span>
    {:else}
      <span class="font-semibold text-emerald-700 dark:text-emerald-400">{word.asOption}× as option choice</span>
      <span class="mx-1">•</span>
      <span>{word.asStem}× as stem</span>
    {/if}
  </div>
  {#if allExams.length > 0}
    <div class="text-[10px] text-zinc-500/80 truncate mt-1">
      in {allExams.slice(0, 3).join(', ')}{allExams.length > 3 ? ' +more' : ''}
    </div>
  {/if}
</div>
