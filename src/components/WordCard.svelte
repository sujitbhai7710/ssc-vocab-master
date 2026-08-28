<script lang="ts">
  // src/components/WordCard.svelte
  import FrequencyBadge from './FrequencyBadge.svelte';
  import { pronounceWord, type WordEntry, type QType } from '../lib/vocab-data';

  let {
    word,
    rank,
    view,
    qtypeFilter = null,
    restrictToSynAnt = false,
    onSelect,
  }: {
    word: WordEntry;
    rank: number;
    view: 'stems' | 'options';
    qtypeFilter?: QType | null;
    restrictToSynAnt?: boolean;
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
  function pronounce(e: MouseEvent) {
    e.stopPropagation();
    pronounceWord(word.word);
  }

  const allExams = $derived(Array.from(new Set([...word.stemExams, ...word.optionExams])));

  // Counts based on the view/filter
  const counts = $derived.by(() => {
    if (restrictToSynAnt) {
      const opt = (word.qtypesAsOption['synonym'] ?? 0) + (word.qtypesAsOption['antonym'] ?? 0);
      return { asStem: word.asStem, asOption: opt };
    }
    if (qtypeFilter) {
      return {
        asStem: word.qtypesAsStem[qtypeFilter] ?? 0,
        asOption: word.qtypesAsOption[qtypeFilter] ?? 0,
      };
    }
    return { asStem: word.asStem, asOption: word.asOption };
  });

  // For OWS/Idioms/Homonyms/Spelling — single count badge ("as main question" = correct answer)
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
    <span class="text-xs font-mono text-zinc-500 tabular-nums shrink-0">#{rank}</span>
    <h3 class="text-base font-semibold tracking-tight truncate group-hover:text-orange-600 transition-colors flex-1 min-w-0">
      {word.word}
    </h3>
    <!-- Pronunciation button -->
    <button
      on:click={pronounce}
      on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); pronounceWord(word.word); } }}
      class="shrink-0 h-6 w-6 rounded-full flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 hover:bg-orange-100 dark:hover:bg-orange-900 text-zinc-600 dark:text-zinc-300 hover:text-orange-700 dark:hover:text-orange-300 transition-colors"
      title="Pronounce '{word.word}'"
      aria-label="Pronounce {word.word}"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.72a.99.99 0 0 1-.703.286H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.71a.99.99 0 0 1 .703.286l3.484 3.516A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M19.364 5.636a9 9 0 0 1 0 12.728"/></svg>
    </button>
  </div>
  {#if isPhraseQtype}
    <!-- For OWS/Idioms/Homonyms/Spelling: single badge showing how many times this word appeared as the answer -->
    <div class="mb-2">
      <FrequencyBadge label="As answer" count={counts.asStem} variant="stem" size="sm" />
    </div>
    <div class="text-[11px] text-zinc-500 leading-relaxed">
      <span class="font-semibold text-amber-700 dark:text-amber-400">
        {counts.asStem}× as the correct answer
      </span>
      in {qtypeFilter === 'one-word' ? 'OWS' : qtypeFilter === 'idiom' ? 'idiom' : qtypeFilter === 'homonym' ? 'homonym' : 'spelling'} questions
      {#if counts.asOption > 0}
        <span class="mx-1">•</span>
        {counts.asOption}× as a distractor
      {/if}
    </div>
  {:else if restrictToSynAnt}
    <!-- /options page: show stem and syn/ant option counts -->
    <div class="flex flex-wrap gap-1.5 mb-2">
      <FrequencyBadge label="Stem" count={word.asStem} variant="stem" size="sm" />
      <FrequencyBadge label="Syn/Ant Opt" count={counts.asOption} variant="option" size="sm" />
    </div>
    <div class="text-[11px] text-zinc-500 leading-relaxed">
      <span class="font-semibold text-emerald-700 dark:text-emerald-400">
        {counts.asOption}× as synonym/antonym option
      </span>
      <span class="mx-1">•</span>
      <span>{word.asStem}× as question stem</span>
    </div>
  {:else if qtypeFilter}
    <!-- For syn/ant filtered -->
    <div class="flex flex-wrap gap-1.5 mb-2">
      <FrequencyBadge label="Stem" count={counts.asStem} variant="stem" size="sm" />
      <FrequencyBadge label="Option" count={counts.asOption} variant="option" size="sm" />
    </div>
    <div class="text-[11px] text-zinc-500 leading-relaxed">
      <span class="font-semibold text-amber-700 dark:text-amber-400">{counts.asStem}× as {qtypeFilter} stem</span>
      <span class="mx-1">•</span>
      <span class="font-semibold text-emerald-700 dark:text-emerald-400">{counts.asOption}× as option</span>
    </div>
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
