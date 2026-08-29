<script lang="ts">
  // src/components/PronounceButton.svelte
  // Small, reusable pronunciation button. Click to hear the word spoken.
  // Uses dictionaryapi.dev (real human audio) with Web Speech API fallback.
  // Designed to be placed inline next to any word without conflicting with
  // surrounding click handlers (uses stopPropagation).
  import { pronounceWord } from '../lib/vocab-data';

  let {
    word,
    size = 'sm',
  }: {
    word: string;
    size?: 'xs' | 'sm' | 'md';
  } = $props();

  let loading = $state(false);

  const sizeClasses = {
    xs: 'h-5 w-5',
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
  };
  const iconSizes = {
    xs: 10,
    sm: 12,
    md: 16,
  };

  async function handleClick(e: MouseEvent) {
    e.stopPropagation();
    e.preventDefault();
    if (loading || !word) return;
    loading = true;
    try {
      await pronounceWord(word);
    } finally {
      // small delay to show feedback
      setTimeout(() => { loading = false; }, 300);
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      e.stopPropagation();
      handleClick(e as unknown as MouseEvent);
    }
  }
</script>

<button
  onclick={handleClick}
  onkeydown={handleKeydown}
  role="button"
  tabindex="0"
  class="shrink-0 {sizeClasses[size]} rounded-full flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 hover:bg-orange-100 dark:hover:bg-orange-900 text-zinc-500 dark:text-zinc-400 hover:text-orange-700 dark:hover:text-orange-300 transition-colors align-middle"
  title="Pronounce {word}"
  aria-label="Pronounce {word}"
>
  {#if loading}
    <svg class="animate-spin" xmlns="http://www.w3.org/2000/svg" width={iconSizes[size]} height={iconSizes[size]} fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
  {:else}
    <svg xmlns="http://www.w3.org/2000/svg" width={iconSizes[size]} height={iconSizes[size]} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.72a.99.99 0 0 1-.703.286H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.71a.99.99 0 0 1 .703.286l3.484 3.516A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M19.364 5.636a9 9 0 0 1 0 12.728"/></svg>
  {/if}
</button>
