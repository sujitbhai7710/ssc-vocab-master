<script lang="ts">
  // src/components/Nav.svelte
  // Site navigation with mobile hamburger menu.
  // - Desktop (sm+): horizontal nav bar with all items
  // - Mobile (<sm): hamburger button reveals a full dropdown with all items
  import { onMount, onDestroy } from 'svelte';

  let { activeNav = 'home' }: { activeNav?: string } = $props();

  let mobileOpen = $state(false);
  let outsideClickUnsub: (() => void) | null = null;

  const navItems = [
    { key: 'home', href: '/', label: 'Home', icon: 'home' },
    { key: 'stems', href: '/stems', label: 'Stems', icon: 'stems' },
    { key: 'options', href: '/options', label: 'Options', icon: 'options' },
    { key: 'ows', href: '/ows', label: 'OWS', icon: 'ows' },
    { key: 'idioms', href: '/idioms', label: 'Idioms', icon: 'idiom' },
    { key: 'homonyms', href: '/homonyms', label: 'Homonyms', icon: 'homonym' },
    { key: 'spelling', href: '/spelling', label: 'Spelling', icon: 'spelling' },
    { key: 'roots', href: '/roots', label: 'Roots', icon: 'roots' },
    { key: 'grammar-rules', href: '/grammar-rules', label: 'Grammar Rules', icon: 'grammar' },
    { key: 'manisha-bansal', href: '/manisha-bansal', label: 'Manisha 120', icon: 'manisha' },
    { key: 'manisha-mcq', href: '/manisha-mcq', label: 'Manisha MCQ', icon: 'manisha' },
    { key: 'narration', href: '/narration', label: 'Narration', icon: 'narration' },
    { key: 'voice', href: '/voice', label: 'Voice', icon: 'voice' },
    { key: 'problems', href: '/problems', label: 'Problems', icon: 'problems' },
    { key: 'tests', href: '/tests', label: 'Tests', icon: 'tests' },
  ] as const;

  function toggleMobile() {
    mobileOpen = !mobileOpen;
  }
  function closeMobile() {
    mobileOpen = false;
  }

  function handleOutsideClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (target && !target.closest('#nav-container')) {
      closeMobile();
    }
  }
  function handleEscape(e: KeyboardEvent) {
    if (e.key === 'Escape') closeMobile();
  }

  onMount(() => {
    document.addEventListener('click', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);
    outsideClickUnsub = () => {
      document.removeEventListener('click', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
  });
  onDestroy(() => { outsideClickUnsub?.(); });

  // Icon SVG paths (reusable)
  const icons: Record<string, string> = {
    home: '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    stems: '<path d="M16 7h6v6"/><path d="m22 7-8.5 8.5-5-5L2 17"/>',
    options: '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    ows: '<path d="M4 7V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3"/><path d="M9 22h6"/><path d="M12 18v4"/><path d="M4 7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2"/>',
    idiom: '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
    homonym: '<path d="M12 22V12"/><path d="M2 12h20"/><circle cx="12" cy="6" r="4"/>',
    spelling: '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="m9 11 2 2 4-4"/>',
    roots: '<path d="M12 5v14"/><path d="M5 12h14"/><circle cx="12" cy="12" r="9"/>',
    grammar: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/><path d="M8 11h8"/><path d="M8 7h6"/>',
    manisha: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    narration: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    voice: '<path d="M3 12h4l3-9 4 18 3-9h4"/>',
    problems: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    tests: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
  };
</script>

<div id="nav-container" class="relative">
  <!-- Desktop nav (sm and up) -->
  <nav class="hidden sm:flex items-center gap-0.5 text-sm overflow-x-auto max-w-full">
    {#each navItems as item}
      <a href={item.href} class={`flex items-center gap-1.5 h-8 px-2.5 rounded-md whitespace-nowrap text-xs sm:text-sm ${activeNav === item.key ? 'bg-zinc-100 dark:bg-zinc-800 font-medium' : 'hover:bg-zinc-50 dark:hover:bg-zinc-800'}`}>
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html icons[item.icon]}</svg>
        <span>{item.label}</span>
      </a>
    {/each}
  </nav>

  <!-- Mobile hamburger button (< sm) -->
  <button
    onclick={toggleMobile}
    class="sm:hidden flex items-center gap-1.5 h-9 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-sm font-medium"
    aria-label="Toggle menu"
    aria-expanded={mobileOpen}
  >
    {#if mobileOpen}
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
    {:else}
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
    {/if}
    <span>Menu</span>
  </button>

  <!-- Mobile dropdown — z-50 to stay above all page content -->
  {#if mobileOpen}
    <div class="sm:hidden absolute top-full right-0 mt-1 w-64 max-w-[calc(100vw-2rem)] bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-xl z-50 py-1 max-h-[80vh] overflow-y-auto">
      {#each navItems as item}
        <a
          href={item.href}
          onclick={closeMobile}
          class={`flex items-center gap-2.5 px-3 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 ${activeNav === item.key ? 'bg-zinc-100 dark:bg-zinc-800 font-medium' : ''}`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-zinc-500 shrink-0">{@html icons[item.icon]}</svg>
          <span>{item.label}</span>
        </a>
      {/each}
    </div>
  {/if}
</div>
