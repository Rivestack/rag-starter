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
  <!-- Hero (before first search): a retro terminal window -->
  <div v-if="!hasSearched && !isSearching" class="w-full pt-8 pb-2">
    <div class="border-2 border-foreground bg-card shadow-[6px_6px_0_0_#214bff]">
      <!-- Titlebar: traffic-light dots + path -->
      <div class="flex items-center gap-2 border-b-2 border-foreground bg-muted px-3 py-2">
        <span class="h-3 w-3 rounded-full bg-[#ff5f57]" />
        <span class="h-3 w-3 rounded-full bg-[#febc2e]" />
        <span class="h-3 w-3 rounded-full bg-[#28c840]" />
        <span class="ml-2 text-xs text-muted-foreground">~/rivestack/ask-hn</span>
      </div>
      <!-- Body -->
      <div class="px-5 py-7 sm:px-7 sm:py-8">
        <p class="text-sm">
          <span class="text-primary">visitor@rivestack</span><span class="text-muted-foreground"> ~ $ </span><span class="text-foreground">semantic-search --over hacker-news</span>
        </p>
        <h2 class="mt-4 text-2xl font-bold tracking-tight sm:text-3xl">
          <span class="text-primary">#</span> Search Hacker News
        </h2>
        <p class="mt-2 max-w-xl text-sm text-muted-foreground">
          <span class="text-primary">//</span> semantic search over stories + comments, powered by Rivestack pgvector
        </p>
      </div>
    </div>
  </div>

  <SearchBox v-model="query" :is-searching="isSearching" @search="handleSearch" />
  <StatsBar v-if="stats" :stats="stats" />
  <PerformanceStats v-if="performance" :performance="performance" />
  <SearchResults :results="results" :is-searching="isSearching" :has-searched="hasSearched" />
</template>
