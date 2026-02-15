<script setup lang="ts">
import { Zap, Clock, Layers, Search } from 'lucide-vue-next'
import type { PerformanceStats } from '@/types'

defineProps<{
  performance: PerformanceStats
}>()
</script>

<template>
  <div class="w-full rounded-lg border bg-muted/30 px-4 py-2.5 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs text-muted-foreground">
    <span class="flex items-center gap-1.5">
      <Zap class="h-3 w-3 text-primary" />
      <span class="font-medium text-foreground">{{ performance.total_time_ms.toFixed(0) }}ms</span>
      total
    </span>
    <span class="flex items-center gap-1.5">
      <Clock class="h-3 w-3" />
      {{ performance.query_time_ms.toFixed(0) }}ms query
    </span>
    <span class="flex items-center gap-1.5">
      <Clock class="h-3 w-3" />
      {{ performance.embedding_time_ms.toFixed(0) }}ms embedding
    </span>
    <span class="flex items-center gap-1.5">
      <img src="/vector-icon.png" alt="Vector" class="h-3 w-3" />
      {{ performance.chunks_searched.toLocaleString() }} chunks searched
    </span>
    <span class="flex items-center gap-1.5">
      <Search class="h-3 w-3" />
      {{ performance.results_found }} results
    </span>
    <span class="flex items-center gap-1.5">
      <Layers class="h-3 w-3" />
      {{ performance.index_type.toUpperCase() }} / {{ performance.similarity_metric }}
    </span>
  </div>
</template>
