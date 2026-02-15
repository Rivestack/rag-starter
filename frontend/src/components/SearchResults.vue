<script setup lang="ts">
import { SearchX } from 'lucide-vue-next'
import { Skeleton } from '@/components/ui/skeleton'
import ResultCard from '@/components/ResultCard.vue'
import type { SearchResultItem } from '@/types'

defineProps<{
  results: SearchResultItem[]
  isSearching: boolean
  hasSearched: boolean
}>()
</script>

<template>
  <!-- Loading skeletons -->
  <div v-if="isSearching" class="w-full flex flex-col gap-3">
    <div v-for="i in 5" :key="i" class="rounded-xl border bg-card p-5">
      <Skeleton class="h-4 w-3/4 mb-3" />
      <Skeleton class="h-3 w-1/2 mb-4" />
      <Skeleton class="h-3 w-full" />
      <Skeleton class="h-3 w-5/6 mt-1.5" />
    </div>
  </div>

  <!-- Results -->
  <div v-else-if="results.length > 0" class="w-full flex flex-col gap-3">
    <ResultCard v-for="(result, i) in results" :key="i" :result="result" />
  </div>

  <!-- No results -->
  <div v-else-if="hasSearched" class="flex flex-col items-center py-12 text-center">
    <SearchX class="h-10 w-10 text-muted-foreground/40 mb-3" />
    <p class="text-sm font-medium text-muted-foreground">No results found</p>
    <p class="text-xs text-muted-foreground/70 mt-1">Try a different query or broader terms</p>
  </div>
</template>
