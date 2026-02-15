<script setup lang="ts">
import type { DbStats } from '@/types'

defineProps<{
  stats: DbStats
}>()

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <p class="text-xs text-muted-foreground text-center">
    <span class="font-medium tabular-nums">{{ stats.total_stories.toLocaleString() }}</span> stories &middot;
    <span class="font-medium tabular-nums">{{ stats.total_chunks.toLocaleString() }}</span> chunks &middot;
    {{ formatDate(stats.oldest_story) }} — {{ formatDate(stats.newest_story) }} &middot;
    {{ stats.index_type.toUpperCase() }} index
  </p>
</template>
