<script lang="ts">
  // src/components/TopicRulesView.svelte
  // Renders ONE narration/voice section: concept, detailed rules, examples,
  // and all PYQ MCQs mapped to this section.
  import type { TopicRule, GrammarQuestion } from '../lib/grammar-data';
  import GrammarMCQCard from './GrammarMCQCard.svelte';
  import ProblematicButton from './ProblematicButton.svelte';

  let {
    section,
    kind,
    allSections,
    questions,
  }: {
    section: TopicRule;
    kind: 'narration' | 'voice';
    allSections: TopicRule[];
    questions: Record<string, GrammarQuestion>;
  } = $props();

  const qs = $derived((section.questionIds || []).map((id) => questions[id]).filter(Boolean));
  const showAll = $state(false);
  const visibleQs = $derived(qs);

  // prev/next nav
  const idx = $derived(allSections.findIndex((s) => s.id === section.id));
  const prev = $derived(idx > 0 ? allSections[idx - 1] : null);
  const next = $derived(idx >= 0 && idx < allSections.length - 1 ? allSections[idx + 1] : null);
  const base = $derived(kind === 'narration' ? '/narration' : '/voice');

  function slug(s: TopicRule) {
    return `${s.no}-${s.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;
  }
</script>

<div class="space-y-5">
  <!-- breadcrumb -->
  <div class="text-xs text-zinc-500 flex items-center gap-1.5 flex-wrap">
    <a href="/" class="hover:text-orange-600">Home</a><span>/</span>
    <a href={base} class="hover:text-orange-600 capitalize">{kind}</a><span>/</span>
    <span class="text-zinc-700 dark:text-zinc-300">Section {section.no}</span>
  </div>

  <div>
    <div class="text-[11px] uppercase font-semibold tracking-wide text-orange-600 dark:text-orange-400">{kind === 'narration' ? 'Direct–Indirect Speech' : 'Active–Passive Voice'} · Section {section.no} of {allSections.length}</div>
    <div class="flex items-start justify-between gap-3 flex-wrap mt-1">
      <h2 class="text-2xl font-bold tracking-tight">{section.title}</h2>
      <ProblematicButton itemType={kind} itemKey={section.id} subType={section.title} label="Mark section" />
    </div>
    <p class="text-sm text-zinc-600 dark:text-zinc-400 mt-2 leading-relaxed">{section.concept}</p>
  </div>

  {#if section.rules && section.rules.length}
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4 space-y-2.5">
      <h3 class="text-sm font-semibold flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-orange-500"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
        Key Rules
      </h3>
      <ul class="space-y-2">
        {#each section.rules as rule}
          <li class="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300 flex gap-2">
            <span class="text-orange-500 mt-0.5 shrink-0">▸</span>
            <span>{rule}</span>
          </li>
        {/each}
      </ul>
    </div>
  {/if}

  {#if section.examples && section.examples.length}
    <div class="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 space-y-2">
      <h3 class="text-sm font-semibold text-amber-800 dark:text-amber-300">Worked Examples</h3>
      {#each section.examples as ex}
        <div class="text-sm leading-relaxed">
          {#if ex.direct || ex.active}
            <div class="text-zinc-700 dark:text-zinc-300"><span class="font-semibold text-rose-600 dark:text-rose-400">Direct/Active:</span> {ex.direct || ex.active}</div>
          {/if}
          {#if ex.indirect || ex.passive}
            <div class="text-zinc-700 dark:text-zinc-300"><span class="font-semibold text-emerald-600 dark:text-emerald-400">Indirect/Passive:</span> {ex.indirect || ex.passive}</div>
          {/if}
          {#if ex.note}<div class="text-xs text-zinc-500 mt-0.5">{ex.note}</div>{/if}
        </div>
      {/each}
    </div>
  {/if}

  {#if qs.length}
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-sky-500"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>
          PYQ Practice ({qs.length})
        </h3>
        <span class="text-[11px] text-zinc-500">click an option to reveal the answer</span>
      </div>
      {#each visibleQs as q, qi (q.id)}
        <GrammarMCQCard question={q} index={qi} />
      {/each}
    </div>
  {:else}
    <p class="text-xs text-zinc-400 italic">No PYQs mapped to this section.</p>
  {/if}

  <!-- prev/next -->
  <div class="flex items-center justify-between gap-2 pt-3 border-t border-zinc-200 dark:border-zinc-700">
    {#if prev}
      <a href={`${base}/${slug(prev)}`} class="text-sm h-9 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-1.5">← {prev.no}. {prev.title}</a>
    {:else}<span></span>{/if}
    <a href={base} class="text-sm h-9 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800">All sections</a>
    {#if next}
      <a href={`${base}/${slug(next)}`} class="text-sm h-9 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-1.5">{next.no}. {next.title} →</a>
    {:else}<span></span>{/if}
  </div>
</div>
