<script lang="ts">
  // src/components/WordLinkButton.svelte
  // Small button that links to a word's detail page (/word/[word]).
  // Designed to be placed inline next to any word without conflicting with
  // surrounding click handlers (uses stopPropagation on the anchor).
  let {
    word,
    size = 'sm',
  }: {
    word: string;
    size?: 'xs' | 'sm' | 'md';
  } = $props();

  const sizeClasses = {
    xs: 'h-5 w-5',
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
  };
  const iconSizes = {
    xs: 10,
    sm: 11,
    md: 14,
  };

  // Build the href — encode the word for URL safety (handles spaces, apostrophes)
  const href = $derived(`/word/${encodeURIComponent(word.toLowerCase())}`);

  function handleClick(e: MouseEvent) {
    e.stopPropagation();
    // allow the navigation to proceed (don't preventDefault)
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.stopPropagation();
    }
  }
</script>

<a
  href={href}
  onclick={handleClick}
  onkeydown={handleKeydown}
  class="shrink-0 {sizeClasses[size]} rounded-full flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 hover:bg-sky-100 dark:hover:bg-sky-900 text-zinc-500 dark:text-zinc-400 hover:text-sky-700 dark:hover:text-sky-300 transition-colors align-middle"
  title="Open {word} detail page"
  aria-label="Open {word} detail page"
>
  <svg xmlns="http://www.w3.org/2000/svg" width={iconSizes[size]} height={iconSizes[size]} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
</a>
