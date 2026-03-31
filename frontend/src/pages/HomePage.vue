<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SearchBox from '@/components/SearchBox.vue'
import SearchResults from '@/components/SearchResults.vue'
import PerformanceStats from '@/components/PerformanceStats.vue'
import StatsBar from '@/components/StatsBar.vue'
import { useSearch } from '@/composables/useSearch'
import { useStats } from '@/composables/useStats'

const route = useRoute()
const router = useRouter()
const { query, results, performance, isSearching, search } = useSearch()
const { stats, fetchStats } = useStats()

const hasSearched = computed(() => performance.value !== null)

function handleSearch() {
  const q = query.value.trim()
  if (!q) return
  // Update URL with ?q= param
  router.replace({ query: { q } })
  search()
}

// On mount, if ?q= is present, run the search
onMounted(() => {
  if (route.query.q && typeof route.query.q === 'string') {
    query.value = route.query.q
    search()
  }
})

fetchStats()
</script>

<template>
  <!-- Hero (before first search) -->
  <div v-if="!hasSearched && !isSearching" class="flex flex-col items-center gap-4 pt-16 pb-8">
    <div class="flex items-center justify-center h-16 w-16 rounded-2xl bg-primary/10">
      <img src="/vector-icon.png" alt="Vector" class="h-8 w-8" />
    </div>
    <div class="text-center">
      <h2 class="text-2xl font-bold tracking-tight">Search Hacker News</h2>
      <p class="text-sm text-muted-foreground mt-1 max-w-md">
        Semantic search over Hacker News stories and comments, powered by Rivestack pgvector
      </p>
    </div>
  </div>

  <SearchBox v-model="query" :is-searching="isSearching" @search="handleSearch" />
  <StatsBar v-if="stats" :stats="stats" />
  <PerformanceStats v-if="performance" :performance="performance" />
  <SearchResults :results="results" :is-searching="isSearching" :has-searched="hasSearched" />
</template>
