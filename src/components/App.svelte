<script lang="ts">
  // src/components/App.svelte — root stateful component
  import Dashboard from './Dashboard.svelte';
  import WordListView from './WordListView.svelte';
  import WordDetail from './WordDetail.svelte';
  import {
    loadSummary,
    loadWords,
    type WordEntry,
    type SummaryStats,
  } from '../lib/vocab-data';

  type View = 'home' | 'stems' | 'options' | 'ows' | 'idioms' | 'homonyms' | 'spelling' | 'word';

  let view: View = $state('home');
  let selectedWord: WordEntry | null = $state(null);
  let summary: SummaryStats | null = $state(null);
  let words: WordEntry[] = $state([]);
  let loadingWords = $state(true);

  // Load summary + words on mount (browser only)
  if (typeof window !== 'undefined') {
    (async () => {
      try {
        summary = await loadSummary();
        words = await loadWords();
      } catch (err) {
        console.error('Failed to load summary/words:', err);
      } finally {
        loadingWords = false;
      }
    })();
  }

  function selectWord(w: WordEntry) {
    selectedWord = w;
    view = 'word';
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function navigate(v: 'stems' | 'options' | 'ows' | 'idioms' | 'homonyms' | 'spelling') {
    view = v;
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function backToList() {
    view = selectedWord ? (selectedWord.asStem > 0 ? 'stems' : 'options') : 'home';
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Compute top words
  const topWords = $derived([...words].sort((a, b) => b.total - a.total).slice(0, 10));
  const topStems = $derived([...words].filter((w) => w.asStem > 0).sort((a, b) => b.asStem - a.asStem).slice(0, 10));
  const topOptions = $derived([...words].filter((w) => w.asOption > 0).sort((a, b) => b.asOption - a.asOption).slice(0, 10));

  const navItems = [
    { id: 'home', label: 'Home', icon: 'home' },
    { id: 'stems', label: 'Stems', icon: 'stems' },
    { id: 'options', label: 'Options', icon: 'options' },
    { id: 'ows', label: 'OWS', icon: 'ows' },
    { id: 'idioms', label: 'Idioms', icon: 'idiom' },
    { id: 'homonyms', label: 'Homonyms', icon: 'homonym' },
    { id: 'spelling', label: 'Spelling', icon: 'spelling' },
  ] as const;
</script>

<div class="min-h-screen flex flex-col">
  <!-- Header -->
  <header class="sticky top-0 z-30 bg-white/85 dark:bg-zinc-900/85 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-700">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-3 flex-wrap">
      <button on:click={() => (view = 'home')} class="flex items-center gap-2.5 group min-w-0">
        <div class="h-9 w-9 rounded-lg bg-gradient-to-br from-amber-500 via-orange-500 to-rose-500 flex items-center justify-center text-white shrink-0 shadow-sm group-hover:shadow-md transition-shadow">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/><path d="M8 11h8"/><path d="M8 7h6"/></svg>
        </div>
        <div class="min-w-0 text-left">
          <h1 class="text-base font-bold tracking-tight leading-tight truncate">SSC Vocab Master</h1>
          <p class="text-[10px] text-zinc-500 leading-none truncate">
            {summary ? `${summary.totalQuestions.toLocaleString()} questions · ${summary.totalFiles} papers · ${summary.totalUniqueWords.toLocaleString()} words` : '5 years of synonyms & antonyms · 23 papers'}
          </p>
        </div>
      </button>

      <nav class="flex items-center gap-0.5 text-sm overflow-x-auto max-w-full">
        {#each navItems as item}
          <button
            on:click={() => (item.id === 'home' ? (view = 'home') : navigate(item.id as any))}
            class="flex items-center gap-1.5 h-8 px-2.5 rounded-md whitespace-nowrap text-xs sm:text-sm {view === item.id ? 'bg-zinc-100 dark:bg-zinc-800 font-medium' : 'hover:bg-zinc-50 dark:hover:bg-zinc-800'}"
            title={item.label}
          >
            {#if item.icon === 'home'}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
            {:else if item.icon === 'stems'}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 7h6v6"/><path d="m22 7-8.5 8.5-5-5L2 17"/></svg>
            {:else if item.icon === 'options'}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/></svg>
            {:else if item.icon === 'ows'}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3"/><path d="M9 22h6"/><path d="M12 18v4"/><path d="M4 7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2"/></svg>
            {:else if item.icon === 'idiom'}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            {:else if item.icon === 'homonym'}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V12"/><path d="M2 12h20"/><circle cx="12" cy="6" r="4"/></svg>
            {:else if item.icon === 'spelling'}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="m9 11 2 2 4-4"/></svg>
            {/if}
            <span class="hidden md:inline">{item.label}</span>
          </button>
        {/each}
      </nav>
    </div>
  </header>

  <!-- Main content -->
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
    {#if view === 'home'}
      {#if summary}
        <Dashboard
          {summary}
          {topWords}
          {topStems}
          {topOptions}
          onNavigate={(v) => navigate(v as any)}
          onSelectWord={selectWord}
        />
      {:else}
        <div class="space-y-4">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            {#each Array(4) as _}<div class="h-24 rounded-xl bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}
          </div>
        </div>
      {/if}
    {:else if view === 'stems'}
      <section class="space-y-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-600"><path d="M16 7h6v6"/><path d="m22 7-8.5 8.5-5-5L2 17"/></svg>
            Module 1 — Main Question Stems
          </h2>
          <p class="text-sm text-zinc-500 mt-1 leading-relaxed">
            Words that appeared as the main question word in synonym/antonym questions across SSC exams. Sorted from most repeated to least repeated.
          </p>
        </div>
        <WordListView {words} view="stems" loading={loadingWords} onSelectWord={selectWord} />
      </section>
    {:else if view === 'options'}
      <section class="space-y-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-emerald-600"><path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/></svg>
            Module 2 — Option Choices
          </h2>
          <p class="text-sm text-zinc-500 mt-1 leading-relaxed">
            Words that appeared as one of the four option choices (distractors or correct answers). Sorted from most repeated to least repeated.
          </p>
        </div>
        <WordListView {words} view="options" loading={loadingWords} onSelectWord={selectWord} />
      </section>
    {:else if view === 'ows'}
      <section class="space-y-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-violet-600"><path d="M4 7V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3"/><path d="M9 22h6"/><path d="M12 18v4"/><path d="M4 7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2"/></svg>
            Module 3 — One-Word Substitution (Vocabulary)
          </h2>
          <p class="text-sm text-zinc-500 mt-1 leading-relaxed">
            Words that appeared as options in {summary?.totalOneWord ?? 755} one-word substitution questions across SSC exams. Sorted from most repeated to least repeated.
          </p>
        </div>
        <WordListView {words} view="options" qtypeFilter="one-word" loading={loadingWords} onSelectWord={selectWord} />
      </section>
    {:else if view === 'idioms'}
      <section class="space-y-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-600"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            Module 4 — Idioms & Phrases (Vocabulary)
          </h2>
          <p class="text-sm text-zinc-500 mt-1 leading-relaxed">
            Vocabulary words that appeared as options in {summary?.totalIdioms ?? 887} idiom and phrase questions across SSC exams. Sorted from most repeated to least repeated.
          </p>
        </div>
        <WordListView {words} view="options" qtypeFilter="idiom" loading={loadingWords} onSelectWord={selectWord} />
      </section>
    {:else if view === 'homonyms'}
      <section class="space-y-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-pink-600"><path d="M12 22V12"/><path d="M2 12h20"/><circle cx="12" cy="6" r="4"/></svg>
            Module 5 — Homonyms & Homophones (Vocabulary)
          </h2>
          <p class="text-sm text-zinc-500 mt-1 leading-relaxed">
            Words that appeared as options in {summary?.totalHomonyms ?? 34} homonym/homophone fill-in-the-blank questions. Sorted from most repeated to least repeated.
          </p>
        </div>
        <WordListView {words} view="options" qtypeFilter="homonym" loading={loadingWords} onSelectWord={selectWord} />
      </section>
    {:else if view === 'spelling'}
      <section class="space-y-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-sky-600"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="m9 11 2 2 4-4"/></svg>
            Module 6 — Spelling (Vocabulary)
          </h2>
          <p class="text-sm text-zinc-500 mt-1 leading-relaxed">
            Words that appeared as options in {summary?.totalSpelling ?? 866} spelling questions (correctly spelt / misspelt / spelling error). Sorted from most repeated to least repeated.
          </p>
        </div>
        <WordListView {words} view="options" qtypeFilter="spelling" loading={loadingWords} onSelectWord={selectWord} />
      </section>
    {:else if view === 'word' && selectedWord}
      <WordDetail word={selectedWord} onBack={backToList} />
    {/if}
  </main>

  <!-- Footer -->
  <footer class="mt-auto border-t border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900/30">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-zinc-500 text-center">
      <p>
        SSC Vocab Master · {summary?.totalQuestions.toLocaleString() ?? '4,475'} vocabulary questions parsed from {summary?.totalFiles ?? 23} SSC exam papers (2019–2026) · Built for aspirants preparing for CGL, CHSL, CPO, MTS, Selection Posts.
      </p>
      <p class="mt-1 text-[10px]">
        Word definitions sourced from WordNet · SSC synonym/antonym relationships extracted from past papers · Best-guess answers computed via WordNet similarity (SSC does not publish official answer keys).
      </p>
    </div>
  </footer>
</div>
