<script setup lang="ts">
import { computed } from 'vue'
import SearchBox from '@/components/SearchBox.vue'
import SearchResults from '@/components/SearchResults.vue'
import PerformanceStats from '@/components/PerformanceStats.vue'
import StatsBar from '@/components/StatsBar.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useSearch } from '@/composables/useSearch'
import { useStats } from '@/composables/useStats'

const { query, results, performance, isSearching, search } = useSearch()
const { stats, fetchStats } = useStats()

const hasSearched = computed(() => performance.value !== null)

fetchStats()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Header -->
    <header class="flex items-center justify-between px-6 py-4">
      <div class="flex items-center gap-3">
        <div class="flex items-center justify-center h-9 w-9 rounded-lg bg-primary/10">
          <img src="/logo.svg" alt="Rivestack" class="h-5 w-5" />
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight leading-none">Ask HN</h1>
          <p class="text-[11px] text-muted-foreground font-medium">Semantic Search</p>
        </div>
      </div>
      <ThemeToggle />
    </header>

    <!-- Main -->
    <main class="flex-1 flex flex-col items-center px-4 pt-6 pb-16 gap-5 max-w-3xl mx-auto w-full">
      <!-- Hero (before first search) -->
      <div v-if="!hasSearched && !isSearching" class="flex flex-col items-center gap-4 pt-16 pb-8">
        <div class="flex items-center justify-center h-16 w-16 rounded-2xl bg-primary/10">
          <img src="/vector-icon.png" alt="Vector" class="h-8 w-8" />
        </div>
        <div class="text-center">
          <h2 class="text-2xl font-bold tracking-tight">Search Hacker News</h2>
          <p class="text-sm text-muted-foreground mt-1 max-w-md">
            Semantic search over 30 days of HN stories and comments, powered by Rivestack pgvector
          </p>
        </div>
      </div>

      <SearchBox v-model="query" :is-searching="isSearching" @search="search" />
      <StatsBar v-if="stats" :stats="stats" />
      <PerformanceStats v-if="performance" :performance="performance" />
      <SearchResults :results="results" :is-searching="isSearching" :has-searched="hasSearched" />
    </main>

    <AppFooter />
  </div>
</template>
