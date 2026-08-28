<script lang="ts">
  // src/components/WordCard.svelte
  import FrequencyBadge from './FrequencyBadge.svelte';
  import type { WordEntry, QTypeExtended } from '../lib/vocab-data';

  let {
    word,
    rank,
    view,
    qtypeFilter = null,
    onSelect,
  }: {
    word: WordEntry;
    rank: number;
    view: 'stems' | 'options';
    qtypeFilter?: QTypeExtended | null;
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

  // Per-qtype counts (when qtypeFilter is set, we show qtype-specific badges)
  const countsInQtype = $derived(
    qtypeFilter
      ? {
          asStem: word.qtypesAsStem[qtypeFilter] ?? 0,
          asOption: word.qtypesAsOption[qtypeFilter] ?? 0,
        }
      : null
  );

  // For OWS/Idioms/Homonyms/Spelling: only the "as option" count is meaningful
  // (these question types don't have single-word stems). So we show one badge.
  const isPhraseQtype = $derived(
    qtypeFilter === 'one-word' || qtypeFilter === 'idiom' || qtypeFilter === 'homonym' || qtypeFilter === 'spelling'
  );
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
  {#if qtypeFilter && countsInQtype}
    {#if isPhraseQtype}
      <!-- For OWS/Idioms/Homonyms/Spelling: single badge showing how many times this word appeared -->
      <div class="mb-2">
        <FrequencyBadge label="Appeared" count={countsInQtype.asOption} variant="option" size="sm" />
      </div>
      <div class="text-[11px] text-zinc-500 leading-relaxed">
        <span class="font-semibold text-emerald-700 dark:text-emerald-400">
          {countsInQtype.asOption}× as option
        </span>
        in {qtypeFilter} questions
      </div>
    {:else}
      <!-- For syn/ant filtered: show stem and option counts for that qtype -->
      <div class="flex flex-wrap gap-1.5 mb-2">
        <FrequencyBadge label="Stem" count={countsInQtype.asStem} variant="stem" size="sm" />
        <FrequencyBadge label="Option" count={countsInQtype.asOption} variant="option" size="sm" />
      </div>
      <div class="text-[11px] text-zinc-500 leading-relaxed">
        <span class="font-semibold text-amber-700 dark:text-amber-400">{countsInQtype.asStem}× as stem</span>
        <span class="mx-1">•</span>
        <span class="font-semibold text-emerald-700 dark:text-emerald-400">{countsInQtype.asOption}× as option</span>
        in {qtypeFilter} questions
      </div>
    {/if}
  {:else}
    <!-- Default: overall counts -->
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
  {/if}
  {#if allExams.length > 0}
    <div class="text-[10px] text-zinc-500/80 truncate mt-1">
      in {allExams.slice(0, 3).join(', ')}{allExams.length > 3 ? ' +more' : ''}
    </div>
  {/if}
</div>
