<script lang="ts">
  // src/components/FrequencyBadge.svelte
  let {
    label,
    count,
    variant = 'neutral',
    size = 'md',
  }: {
    label: string;
    count: number;
    variant?: 'stem' | 'option' | 'neutral';
    size?: 'sm' | 'md' | 'lg';
  } = $props();

  let cls = $derived(
    'frequency-badge' +
    (variant === 'stem' ? ' frequency-badge-stem'
      : variant === 'option' ? ' frequency-badge-option'
      : ' frequency-badge-neutral') +
    (size === 'sm' ? ' !text-[10px] !px-2 !py-0.5'
      : size === 'lg' ? ' !text-sm !px-3 !py-1.5'
      : '')
  );
</script>

<span class={cls}>
  <span class="opacity-80">{label}:</span>
  <span class="font-bold tabular-nums">{count}</span>
  <span class="opacity-70">{count === 1 ? 'time' : 'times'}</span>
</span>
